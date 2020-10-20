import logging
import uuid

from dateutil import parser
from decimal import Decimal
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import make_aware
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from urllib.parse import urlparse

User = get_user_model()

logger = logging.getLogger('formsaurus')


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    @property
    def short_id(self):
        return str(self.id)[:8]

    class Meta:
        abstract = True


MAX_DIGITS = 12
PRECISION = 3

#
# SURVEY
#

class QuestionType:
    def __init__(self, question_type, name, disabled=False):
        self.type = question_type
        self.name = name
        self.disabled = disabled

    def __str__(self):
        return f'{self.type} {self.name} {self.disabled}'

class Shape:
    def __init__(self, shape_type, name, disabled=False):
        self.shape = shape_type
        self.name = name
        self.disabled = disabled

class AbstractSurvey(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=None, null=True, blank=True)
    first_question = models.ForeignKey(
        'Question', on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='first_question')
    last_question = models.ForeignKey('Question', on_delete=models.SET_NULL,
                                      blank=True, null=True, default=None, related_name='last_question')

    class Meta:
        abstract = True

    def publish(self):
        Submission.objects.filter(survey=self, is_preview=True).delete()
        self.published = True
        self.published_at = timezone.now()
        self.save()

    @property
    def question_types(self):
        """
        Return the list of supported Question Types.
        This can be easily overwritten to tailor which types
        are allowed to be added.
        """
        types = {}
        for key, value in Question.TYPES:
            # Skip PAYMENT for now
            if key == Question.PAYMENT:
                continue
            types[key] = QuestionType(
                key,
                value,
                disabled=False,
            )
        return types

    @property
    def answerable(self):
        """
        This can be overwitten to limit when a survey can be
        answered (maybe based no number of answers)
        """
        return True

    @property
    def rating_shapes(self):
        """
        Return the list of supported rating shapes.
        """
        shapes = {}
        for key, value in RatingParameters.SHAPES:
            shapes[key] = Shape(
                key,
                value,
                disabled=False,
            )
        return shapes

    @property
    def logic_enabled(self):
        """
        Returns whether logic jumps are enabled.
        """
        return True

    @property
    def wizard_actions_template_name(self):
        return None

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'published': self.published,
            'logic_enabled': self.logic_enabled,
            'has_unsplash': hasattr(settings, 'UNSPLASH_ACCESS_KEY'),
            'has_pexels': hasattr(settings, 'PEXELS_API_KEY'),
            'has_tenor': hasattr(settings, 'TENOR_API_KEY'),
            'wizard_actions_template_name': self.wizard_actions_template_name,
        }

    @property
    def submissions(self):
        return self.submission_set.filter(is_preview=False).all()

    @property
    def questions(self):
        questions = self.question_set.all()
        # Need to order based on next_question
        cache = {}
        for question in questions:
            cache[question.id] = question
        results = []
        current = cache[self.first_question_id] if self.first_question_id is not None else None
        while current is not None:
            results.append(current)
            current = cache[current.next_question_id] if current.next_question_id is not None else None
        return results

    def add_hidden_field(self, name):
        field, _ = HiddenField.objects.get_or_create(survey=self, name=name)
        return field

    def append_question(self, question):
        if self.first_question is None:
            self.first_question = question
            self.last_question = question
            self.save()
        else:
            # (TODO) 'Thank you screen' should be at the end
            # 1) When adding a TS make it last_question
            # 2) When adding other, make sure to put it before TS
            self.last_question.next_question = question
            self.last_question.save()

            self.last_question = question
            self.save()

    def delete_question(self, question):
        qs = Question.objects.filter(
            survey=self, next_question=question)
        previous_question = None
        if len(qs) > 0:
            previous_question = qs[0]

        if self.first_question == question:
            self.first_question = question.next_question
        else:
            previous_question.next_question = question.next_question

        if self.last_question == question:
            self.last_question = previous_question
        question.delete()

    def add_welcome_screen(self, question, description=None, button_label='Start', image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        # Check whether we already have a welcome screen
        qs = self.question_set.filter(question_type='WS')
        if qs.count() == 1:
            # Technically return an error or throw an exception
            return qs.first()
        else:
            question = Question.objects.create(
                survey=self,
                question=question,
                description=description,
                question_type=Question.WELCOME_SCREEN,
                required=False,
            )
            _ = WelcomeParameters.objects.create(
                question=question,
                button_label=button_label,
                image_url=image_url,
                video_url=video_url,
                orientation=orientation,
                position_x=position_x,
                position_y=position_y,
                opacity=opacity,
            )
            self.append_question(question)
            return question

    def add_thank_you_screen(self, question, description=None, show_button=True, button_label='Done', button_link=None, show_social_media=True, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.THANK_YOU_SCREEN,
            required=False,
        )
        _ = ThankYouParameters.objects.create(
            question=question,
            show_button=show_button,
            button_label=button_label,
            button_link=button_link,
            show_social_media=show_social_media,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_multiple_choice(self,
                            question,
                            required=True,
                            description=None,
                            multiple_selection=False,
                            randomize=False,
                            other_option=False,
                            choices=[],
                            vertical_alignment=False,
                            image_url=None,
                            video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.MULTIPLE_CHOICE,
            required=required,
        )
        _ = MultipleChoiceParameters.objects.create(
            question=question,
            multiple_selection=multiple_selection,
            randomize=randomize,
            other_option=other_option,
            vertical_alignment=vertical_alignment,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        position = 0
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice,
                position=position,
            )
            position = position + 1
        self.append_question(question)
        return question

    def add_phone_number(self, question, required=True, description=None, default_country_code=1, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PHONE_NUMBER,
            required=required,
        )
        _ = PhoneNumberParameters.objects.create(
            question=question,
            default_country_code=default_country_code,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_short_text(self, question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.SHORT_TEXT,
            required=required,
        )
        _ = ShortTextParameters.objects.create(
            question=question,
            limit_character=limit_character,
            limit=limit,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_long_text(self, question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.LONG_TEXT,
            required=required,
        )
        _ = LongTextParameters.objects.create(
            question=question,
            limit_character=limit_character,
            limit=limit,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_statement(self, question, description=None, button_label='Next', show_quotation_mark=True, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.STATEMENT,
            required=False,
        )
        _ = StatementParameters.objects.create(
            question=question,
            button_label=button_label,
            show_quotation_mark=show_quotation_mark,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_picture_choice(self, question, required=False, description=None, multiple_selection=False, randomize=False, other_option=False, choices=[], show_labels=False, supersize=False, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PICTURE_CHOICE,
            required=required,
        )
        _ = PictureChoiceParameters.objects.create(
            question=question,
            multiple_selection=multiple_selection,
            randomize=randomize,
            other_option=other_option,
            show_labels=show_labels,
            supersize=supersize,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )

        position = 0
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice['label'],
                image_url=choice['image_url'],
                position=position,
            )
            position=position+1
        self.append_question(question)
        return question

    def add_yes_no(self, question, required=False, description=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.YES_NO,
            required=required,
        )
        _ = YesNoParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_email(self, question, required=False, description=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.EMAIL,
            required=required,
        )
        _ = EmailParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )

        self.append_question(question)
        return question

    def add_opinion_scale(self, question, required=False, description=None, start_at_one=True, number_of_steps=11, show_labels=False, left_label=None, center_label=None, right_label=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.OPINION_SCALE,
            required=required,
        )
        _ = OpinionScaleParameters.objects.create(
            question=question,
            start_at_one=start_at_one,
            number_of_steps=number_of_steps,
            show_labels=show_labels,
            left_label=left_label,
            center_label=center_label,
            right_label=right_label,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_rating(self, question, required=False, description=None, number_of_steps=5, shape='ST', image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.RATING,
            required=required,
        )
        _ = RatingParameters.objects.create(
            question=question,
            number_of_steps=number_of_steps,
            shape=shape,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_date(self, question, required=False, description=None, date_format='A', date_separator='/', image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.DATE,
            required=required,
        )
        _ = DateParameters.objects.create(
            question=question,
            date_format=date_format,
            date_separator=date_separator,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_number(self, question, required=False, description=None, enable_min=False, min_value=None, enable_max=False, max_value=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.NUMBER,
            required=required,
        )
        _ = NumberParameters.objects.create(
            question=question,
            enable_min=enable_min,
            min_value=min_value,
            enable_max=enable_max,
            max_value=max_value,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_dropdown(self, question, required=False, description=None, randomize=False, alphabetical=False, choices=[], image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.DROPDOWN,
            required=required,
        )
        _ = DropdownParameters.objects.create(
            question=question,
            randomize=randomize,
            alphabetical=alphabetical,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        position = 0
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice,
                position=position,
            )
            position = position + 1
        self.append_question(question)
        return question

    def add_legal(self, question, required=False, description=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.LEGAL,
            required=required,
        )
        _ = LegalParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_file_upload(self, question, required=False, description=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.FILE_UPLOAD,
            required=required,
        )
        _ = FileUploadParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_payment(self, question, required=False, description=None, currency='USD', price=0.0, stripe_token=None, button_label='Pay', image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PAYMENT,
            required=required,
        )
        _ = PaymentParameters.objects.create(
            question=question,
            currency=currency,
            price=price,
            stripe_token=stripe_token,
            button_label=button_label,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def add_website(self, question, description=None, required=False, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.WEBSITE,
            required=required,
        )
        _ = WebsiteParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
            orientation=orientation,
            position_x=position_x,
            position_y=position_y,
            opacity=opacity,
        )
        self.append_question(question)
        return question

    def move_question_up(self, question):
        if self.first_question == question:
            logger.debug('Not moving first question up')
            return
        # We're assured there is a previous question based on the previous if statement
        previous_question = Question.objects.filter(
            survey=self, next_question=question)[0]
        qs = Question.objects.filter(
            survey=self, next_question=previous_question)
        previous_previous_question = qs[0] if len(qs) > 0 else None
        next_question = question.next_question

        logger.debug('Trying to move %s up:', question)
        logger.debug('%s ==> %s -> %s -> %s -> %s ==> %s',
                     self.first_question,
                     previous_previous_question,
                     previous_question,
                     question,
                     next_question,
                     self.last_question)

        if previous_previous_question is not None:
            previous_previous_question.next_question = question
            previous_previous_question.save()
        previous_question.next_question = next_question
        question.next_question = previous_question
        if self.first_question == previous_question:
            self.first_question = question
        previous_question.save()
        if next_question is not None:
            next_question.save()
        question.save()
        self.save()

    def move_question_down(self, question):
        if question.next_question is None:
            logger.debug('Not moving question down, there is no next question')
            return
        qs = Question.objects.filter(survey=self, next_question=question)
        previous_question = qs[0] if len(qs) > 0 else None
        next_question = question.next_question
        logger.debug('Trying to move %s down:', question)
        logger.debug('%s ==> %s -> %s -> %s ==> %s',
                     self.first_question,
                     previous_question,
                     question,
                     next_question,
                     self.last_question)

        previous_question.next_question = next_question
        question.next_question = next_question.next_question
        next_question.next_question = question
        if self.last_question == next_question:
            self.last_question = question
        previous_question.save()
        next_question.save()
        question.save()
        self.save()

class Survey(AbstractSurvey):
    pass

class HiddenField(BaseModel):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)

#
# QUESTION
#


class Question(BaseModel):
    WELCOME_SCREEN = 'WS'
    THANK_YOU_SCREEN = 'TS'
    MULTIPLE_CHOICE = 'MC'
    PHONE_NUMBER = 'PN'
    SHORT_TEXT = 'ST'
    LONG_TEXT = 'LT'
    STATEMENT = 'S_'
    PICTURE_CHOICE = 'PC'
    YES_NO = 'YN'
    EMAIL = 'E_'
    OPINION_SCALE = 'OS'
    RATING = 'R_'
    DATE = 'D_'
    NUMBER = 'N_'
    DROPDOWN = 'DD'
    LEGAL = 'L_'
    FILE_UPLOAD = 'FU'
    PAYMENT = 'P_'
    WEBSITE = 'W_'

    TYPES = [
        (WELCOME_SCREEN, 'Welcome Screen'),
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (PHONE_NUMBER, 'Phone Number'),
        (SHORT_TEXT, 'Short Text'),
        (LONG_TEXT, 'Long Text'),
        (STATEMENT, 'Statement'),
        (PICTURE_CHOICE, 'Picture Choice'),
        (YES_NO, 'Yes/No'),
        (EMAIL, 'Email'),
        (OPINION_SCALE, 'Opinion Scale'),
        (RATING, 'Rating'),
        (DATE, 'Date'),
        (NUMBER, 'Number'),
        (DROPDOWN, 'Dropdown'),
        (LEGAL, 'Legal'),
        (FILE_UPLOAD, 'File Upload'),
        (PAYMENT, 'Payment'),
        (WEBSITE, 'Website'),
        (THANK_YOU_SCREEN, 'Thank You Screen'),
    ]
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.TextField()
    description = models.TextField(blank=True, null=True, default=None)
    question_type = models.CharField(max_length=2, choices=TYPES)
    required = models.BooleanField()
    next_question = models.ForeignKey('Question', on_delete=models.SET_NULL,
                                      related_name='previous_question', blank=True, null=True, default=None)

    @classmethod
    def type_name(cls, question_type):
        for value in Question.TYPES:
            if value[0] == question_type:
                return value[1]
        return "Unknown"

    @property
    def condition_type(self):
        if self.question_type in [Question.YES_NO, Question.LEGAL, Question.FILE_UPLOAD]:
            return Condition.BOOLEAN
        elif self.question_type in [Question.MULTIPLE_CHOICE, Question.PICTURE_CHOICE]:
            return Condition.CHOICE
        elif self.question_type in [Question.OPINION_SCALE, Question.RATING, Question.NUMBER]:
            return Condition.NUMBER
        elif self.question_type in [Question.PHONE_NUMBER, Question.SHORT_TEXT, Question.LONG_TEXT, Question.EMAIL, Question.WEBSITE, Question.DROPDOWN]:
            return Condition.TEXT
        elif self.question_type in [Question.DATE]:
            return Condition.DATE
        else:
            return None

    def next(self, submission):
        # Any rules associated to this question
        qs = self.ruleset_set.all()
        if qs.count() == 0:
            logger.debug(
                f"{self.short_id} has no ruleset, returning default {self.next_question}")
            return self.next_question
        logger.debug(f"{self.short_id} has {qs.count()} ruleset(s)")
        for ruleset in qs:
            logger.debug(
                f"{self.short_id} evaluating ruleset {ruleset.short_id}")
            q = ruleset.evaluate(submission)
            logger.debug(
                f"{self.short_id} evaluation of {ruleset.id} returned {q}")
            if q is not None:
                return q
        # If none of the ruleset evaluated successfully, fallback to next_question
        logger.debug(
            f"{self.short_id} no ruleset matched, returning default {self.next_question}")
        return self.next_question

    def __str__(self):
        return f"{self.short_id} {self.question_type} {self.question}"

    @property
    def parameters(self):
        if self.question_type == Question.WELCOME_SCREEN:
            return self.welcomeparameters_set.first()
        elif self.question_type == Question.THANK_YOU_SCREEN:
            return self.thankyouparameters_set.first()
        elif self.question_type == Question.MULTIPLE_CHOICE:
            return self.multiplechoiceparameters_set.first()
        elif self.question_type == Question.PHONE_NUMBER:
            return self.phonenumberparameters_set.first()
        elif self.question_type == Question.SHORT_TEXT:
            return self.shorttextparameters_set.first()
        elif self.question_type == Question.LONG_TEXT:
            return self.longtextparameters_set.first()
        elif self.question_type == Question.STATEMENT:
            return self.statementparameters_set.first()
        elif self.question_type == Question.PICTURE_CHOICE:
            return self.picturechoiceparameters_set.first()
        elif self.question_type == Question.YES_NO:
            return self.yesnoparameters_set.first()
        elif self.question_type == Question.EMAIL:
            return self.emailparameters_set.first()
        elif self.question_type == Question.OPINION_SCALE:
            return self.opinionscaleparameters_set.first()
        elif self.question_type == Question.RATING:
            return self.ratingparameters_set.first()
        elif self.question_type == Question.DATE:
            return self.dateparameters_set.first()
        elif self.question_type == Question.NUMBER:
            return self.numberparameters_set.first()
        elif self.question_type == Question.DROPDOWN:
            return self.dropdownparameters_set.first()
        elif self.question_type == Question.LEGAL:
            return self.legalparameters_set.first()
        elif self.question_type == Question.FILE_UPLOAD:
            return self.fileuploadparameters_set.first()
        elif self.question_type == Question.PAYMENT:
            return self.paymentparameters_set.first()
        elif self.question_type == Question.WEBSITE:
            return self.websiteparameters_set.first()

        return None

# PARAMETERS FOR THE DIFFERENT QUESTION TYPES


class QuestionParameter(BaseModel):
    STACK = 'S'
    FLOAT = 'F'
    SPLIT = '2'
    BACKGROUND = 'B'

    ORIENTATIONS = [
        (STACK, 'Stack'),
        (FLOAT, 'Float'),
        (SPLIT, 'Split'),
        (BACKGROUND, 'Background'),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True, default=None)
    video_url = models.URLField(blank=True, null=True, default=None)
    orientation = models.CharField(
        max_length=1, choices=ORIENTATIONS, blank=True, null=True, default=None)
    position_x = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    position_y = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    opacity = models.PositiveIntegerField(blank=True, null=True, default=None)

    class Meta:
        abstract = True


class WelcomeParameters(QuestionParameter):
    button_label = models.CharField(max_length=128)


class ThankYouParameters(QuestionParameter):
    show_button = models.BooleanField()
    button_label = models.CharField(max_length=128)
    button_link = models.URLField(blank=True, null=True, default=None)
    show_social_media = models.BooleanField()


class MultipleAnswer(QuestionParameter):
    multiple_selection = models.BooleanField()
    randomize = models.BooleanField()
    other_option = models.BooleanField()

    class Meta:
        abstract = True


class MultipleChoiceParameters(MultipleAnswer):
    vertical_alignment = models.BooleanField()


class PhoneNumberParameters(QuestionParameter):
    default_country_code = models.CharField(max_length=2)


class ShortTextParameters(QuestionParameter):
    limit_character = models.BooleanField()
    limit = models.PositiveIntegerField(blank=True, null=True, default=None)


class LongTextParameters(QuestionParameter):
    limit_character = models.BooleanField()
    limit = models.PositiveIntegerField(blank=True, null=True, default=None)


class StatementParameters(QuestionParameter):
    button_label = models.CharField(max_length=128)
    show_quotation_mark = models.BooleanField()


class PictureChoiceParameters(MultipleAnswer):
    show_labels = models.BooleanField()
    supersize = models.BooleanField()


class YesNoParameters(QuestionParameter):
    pass


class EmailParameters(QuestionParameter):
    pass


class OpinionScaleParameters(QuestionParameter):
    start_at_one = models.BooleanField()
    number_of_steps = models.PositiveSmallIntegerField()
    show_labels = models.BooleanField()
    left_label = models.CharField(
        max_length=128, blank=True, null=True, default=None)
    center_label = models.CharField(
        max_length=128, blank=True, null=True, default=None)
    right_label = models.CharField(
        max_length=128, blank=True, null=True, default=None)


class RatingParameters(QuestionParameter):
    STARS = 'ST'
    HEARTS = 'HE'
    USERS = 'US'
    THUMBS = 'TU'
    CROWNS = 'CR'
    CATS = 'CA'
    DOGS = 'DO'
    CIRCLES = 'CI'
    FLAGS = 'FL'
    DROPLETS = 'DR'
    TICKS = 'TI'
    LIGHTBULBS = 'LI'
    TROPHIES = 'TR'
    CLOUDS = 'CL'
    THUNDERBOLTS = 'TH'
    PENCILS = 'PE'
    SKULLS = 'SK'

    SHAPES = [
        (STARS, 'Stars'),
        (HEARTS, 'Hearts'),
        (USERS, 'Users'),
        (THUMBS, 'Thumbs'),
        (CROWNS, 'Crowns'),
        (CATS, 'Cats'),
        (DOGS, 'Dogs'),
        (CIRCLES, 'Circles'),
        (FLAGS, 'Flags'),
        (DROPLETS, 'Droplets'),
        (TICKS, 'Ticks'),
        (LIGHTBULBS, 'Lightbulbs'),
        (TROPHIES, 'Trophies'),
        (CLOUDS, 'Clouds'),
        (THUNDERBOLTS, 'Thunderbolts'),
        (PENCILS, 'Pencils'),
        (SKULLS, 'Skulls'),
    ]
    number_of_steps = models.PositiveSmallIntegerField()
    shape = models.CharField(max_length=2, choices=SHAPES)


class DateParameters(QuestionParameter):
    YYYYMMDD = 'A'
    DDMMYYYY = 'B'
    MMDDYYYY = 'C'

    FORMATS = [
        (YYYYMMDD, 'YYYYMMDD'),
        (DDMMYYYY, 'DDMMYYYY'),
        (MMDDYYYY, 'MMDDYYYY'),
    ]
    DASH = '-'
    DOT = '.'
    SLASH = '/'
    SEPARATORS = [
        (DASH, '-'),
        (DOT, '.'),
        (SLASH, '/'),
    ]
    date_format = models.CharField(max_length=1, choices=FORMATS)
    date_separator = models.CharField(max_length=1, choices=SEPARATORS)

    @property
    def format(self):
        s = self.date_separator
        if self.date_format == 'A':
            return f"YYYY{s}MM{s}DD"
        elif self.date_format == 'B':
            return f"DD{s}MM{s}YYYY"
        elif self.date_format == 'C':
            return f"MM{s}DD{s}YYYY"
        return f"YYYY{s}MM{s}DD"


class NumberParameters(QuestionParameter):
    enable_min = models.BooleanField()
    min_value = models.DecimalField(
        decimal_places=PRECISION, max_digits=MAX_DIGITS, blank=True, null=True, default=None)
    enable_max = models.BooleanField()
    max_value = models.DecimalField(
        decimal_places=PRECISION, max_digits=MAX_DIGITS, blank=True, null=True, default=None)


class DropdownParameters(QuestionParameter):
    randomize = models.BooleanField()
    alphabetical = models.BooleanField()


class LegalParameters(QuestionParameter):
    pass


class FileUploadParameters(QuestionParameter):
    pass


class PaymentParameters(QuestionParameter):
    currency = models.CharField(max_length=10)
    price = models.DecimalField(
        decimal_places=PRECISION, max_digits=MAX_DIGITS)
    stripe_token = models.CharField(max_length=256)
    button_label = models.CharField(max_length=128)


class WebsiteParameters(QuestionParameter):
    pass

# Other optional information about a question


def item_directory_path(instance, filename):
    return f'surveys/{instance.question.survey.short_id}/media/{instance.question.short_id}/{filename}'


class Choice(BaseModel):
    choice = models.CharField(max_length=1024)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True, default=None)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.short_id}: "{self.choice}"'


#
# SUBMISSIONS & ANSWERS
#

class MissingRequiredAnswer:
    pass


class OutOfRangeAnswer:
    pass


def is_empty(text):
    return text is None or text.strip() == ""


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


class Submission(BaseModel):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    is_preview = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True, default=None)

    def complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()

    def answers(self):
        answers = []
        for answer in self.multiplechoiceanswer_set.all():
            answers.append(answer)
        for answer in self.phonenumberanswer_set.all():
            answers.append(answer)
        for answer in self.shorttextanswer_set.all():
            answers.append(answer)
        for answer in self.longtextanswer_set.all():
            answers.append(answer)
        for answer in self.picturechoiceanswer_set.all():
            answers.append(answer)
        for answer in self.yesnoanswer_set.all():
            answers.append(answer)
        for answer in self.emailanswer_set.all():
            answers.append(answer)
        for answer in self.opinionscaleanswer_set.all():
            answers.append(answer)
        for answer in self.ratinganswer_set.all():
            answers.append(answer)
        for answer in self.dateanswer_set.all():
            answers.append(answer)
        for answer in self.numberanswer_set.all():
            answers.append(answer)
        for answer in self.dropdownanswer_set.all():
            answers.append(answer)
        for answer in self.legalanswer_set.all():
            answers.append(answer)
        for answer in self.fileuploadanswer_set.all():
            answers.append(answer)
        for answer in self.paymentanswer_set.all():
            answers.append(answer)
        for answer in self.websiteanswer_set.all():
            answers.append(answer)
        return answers

    def previous_answer(self, question):
        if question.question_type == Question.WELCOME_SCREEN:
            return None
        elif question.question_type == Question.THANK_YOU_SCREEN:
            return None
        elif question.question_type == Question.MULTIPLE_CHOICE:
            try:
                return MultipleChoiceAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.PHONE_NUMBER:
            try:
                return PhoneNumberAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.SHORT_TEXT:
            try:
                return ShortTextAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.LONG_TEXT:
            try:
                return LongTextAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.STATEMENT:
            return None
        elif question.question_type == Question.PICTURE_CHOICE:
            try:
                return PictureChoiceAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.YES_NO:
            try:
                return YesNoAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.EMAIL:
            try:
                return EmailAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.OPINION_SCALE:
            try:
                return OpinionScaleAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.RATING:
            try:
                return RatingAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.DATE:
            try:
                return DateAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.NUMBER:
            try:
                return NumberAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.DROPDOWN:
            try:
                return DropdownAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.LEGAL:
            try:
                return LegalAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.FILE_UPLOAD:
            try:
                return FileUploadAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        elif question.question_type == Question.PAYMENT:
            return None
        elif question.question_type == Question.WEBSITE:
            try:
                return WebsiteAnswer.objects.get(
                    question=question,
                    submission=self,
                )
            except:
                return None
        return None

    def record_answer(self, question, post_data, files_data):
        answer = self.previous_answer(question)
        if question.question_type == Question.WELCOME_SCREEN:
            return None, None
        elif question.question_type == Question.THANK_YOU_SCREEN:
            return None, None
        elif question.question_type == Question.MULTIPLE_CHOICE:
            choices = []
            for choice_id in post_data.getlist('answer'):
                if not is_empty(choice_id):
                    choices.append(choice_id)
            logger.debug(f'<Question:{question}> {choices}')

            if question.required and len(choices) == 0:
                logger.info(f'<Question:{question}> MissingRequiredAnswer()')
                return None, MissingRequiredAnswer()

            parameters = question.parameters
            if choices is not None and not parameters.multiple_selection and len(choices) > 1:
                logger.info(f'<Question:{question}> OutOfRangeAnswer()')
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = MultipleChoiceAnswer(
                    question=question,
                    submission=self,
                )
                answer.save()

            # Clear choices first
            answer.choices.clear()
            # Add each choice
            for choice_id in choices:
                logger.debug(f"<Question:{question}> Recording Choice '{choice_id}'")
                if choice_id is not None:
                    try:
                        choice = Choice.objects.get(pk=choice_id)
                        logger.debug(f"<Question:{question}> Matched Choice <Choice:{choice}>")
                        answer.choices.add(choice)
                    except:
                        if not parameters.other_option:
                            logger.info(f'<Question:{question}> OutOfRangeAnswer() Other detected when not allowed')
                            return OutOfRangeAnswer()
                        logger.debug(f"<Question:{question}> Other '{choice_id}'")
                        answer.other = choice_id
                        answer.save()

            return answer, None
        elif question.question_type == Question.PHONE_NUMBER:
            phone_number = post_data.get('answer', None)
            logger.debug(f'<Question:{question}> {phone_number}')
            if question.required and is_empty(phone_number):
                logger.info(f'<Question:{question}> MissingRequiredAnswer()')
                return None, MissingRequiredAnswer()

            if answer is None:
                answer = PhoneNumberAnswer(
                    question=question,
                    submission=self,
                )
            answer.phone_number = phone_number
            answer.save()
            return answer, None
        elif question.question_type == Question.SHORT_TEXT:
            short_text = post_data.get('answer', None)
            if question.required and is_empty(short_text):
                logger.info(f'<Question:{question}> MissingRequiredAnswer()')
                return None, MissingRequiredAnswer()

            # Is it within parameters
            parameters = question.parameters
            if parameters.limit_character and len(short_text) > parameters.limit:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = ShortTextAnswer(
                    question=question,
                    submission=self,
                )
            answer.short_text = short_text
            answer.save()
            return answer, None
        elif question.question_type == Question.LONG_TEXT:
            long_text = post_data.get('answer', None)
            if question.required and is_empty(long_text):
                return None, MissingRequiredAnswer()

            # Is it within parameters
            parameters = question.parameters
            if parameters.limit_character and len(long_text) > parameters.limit:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = LongTextAnswer(
                    question=question,
                    submission=self,
                )
            answer.long_text = long_text
            answer.save()
            return answer, None
        elif question.question_type == Question.STATEMENT:
            return None, None
        elif question.question_type == Question.PICTURE_CHOICE:
            choices = []
            for choice_id in post_data.getlist('answer'):
                if not is_empty(choice_id):
                    choices.append(choice_id)
            logger.debug(f'<Question:{question}> {choices}')
            if question.required and len(choices) == 0:
                logger.info(f'<Question:{question}> MissingRequiredAnswer()')
                return None, MissingRequiredAnswer()

            parameters = question.parameters
            if choices is not None and not parameters.multiple_selection and len(choices) > 1:
                logger.info(f'<Question:{question}> OutOfRangeAnswer()')
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = PictureChoiceAnswer(
                    question=question,
                    submission=self
                )
                answer.save()

            answer.choices.clear()
            for choice_id in choices:
                logger.debug(f"<Question:{question}> Recording Choice '{choice_id}'")
                if choice_id is not None:
                    try:
                        choice = Choice.objects.get(pk=choice_id)
                        logger.debug(f"<Question:{question}> Matched Choice <Choice:{choice}>")
                        answer.choices.add(choice)
                    except:
                        if not parameters.other_option:
                            logger.info(f'<Question:{question}> OutOfRangeAnswer() Other detected when not allowed')
                            return OutOfRangeAnswer()
                        logger.debug(f"<Question:{question}> Other '{choice_id}'")
                        answer.other = choice_id
                        answer.save()

            return answer, None
        elif question.question_type == Question.YES_NO:
            y = post_data.get('answer', None)
            if y not in ['Yes', 'No', None]:
                return None, OutOfRangeAnswer()

            if y is None and question.required:
                return None, MissingRequiredAnswer()

            if y == 'Yes':
                y = True
            elif y == 'No':
                y = False

            if answer is None:
                answer = YesNoAnswer(
                    question=question,
                    submission=self,
                )
            answer.yes = y
            answer.save()
            return answer, None
        elif question.question_type == Question.EMAIL:
            email = post_data.get('answer', None)
            if question.required and is_empty(email):
                return None, MissingRequiredAnswer()

            if answer is None:
                answer = EmailAnswer(
                    question=question,
                    submission=self,
                )
            answer.email = email
            answer.save()
            return answer, None
        elif question.question_type == Question.OPINION_SCALE:
            level = post_data.get('answer', None)
            if level is not None:
                level = Decimal(level)
            if question.required and level is None:
                return None, MissingRequiredAnswer()

            parameters = question.parameters
            if parameters.start_at_one and level < 1:
                return None, OutOfRangeAnswer()
            elif not parameters.start_at_one and level < 0:
                return None, OutOfRangeAnswer()
            max_value = parameters.number_of_steps
            if parameters.start_at_one:
                max_value = max_value + 1
            if level >= max_value:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = OpinionScaleAnswer(
                    question=question,
                    submission=self,
                )
            answer.opinion = level
            answer.save()
            return answer, None
        elif question.question_type == Question.RATING:
            level = post_data.get('answer', None)
            if level is not None:
                level = Decimal(level)
            if question.required and level is None:
                return None, MissingRequiredAnswer()

            parameters = question.parameters
            if level > parameters.number_of_steps:
                return None, OutOfRangeAnswer()
            elif level < 0:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = RatingAnswer(
                    question=question,
                    submission=self,
                )
            answer.rating = level
            answer.save()
            return answer, None
        elif question.question_type == Question.DATE:
            raw = post_data.get('answer', None)
            if question.required and raw is None:
                return None, MissingRequiredAnswer()

            date = None
            if raw is not None:
                try:
                    date = make_aware(parser.parse(raw))
                except:
                    return None, OutOfRangeAnswer()

            if answer is None:
                answer = DateAnswer(
                    question=question,
                    submission=self,
                )
            answer.date = date
            answer.save()
            return answer, None
        elif question.question_type == Question.NUMBER:
            number = post_data.get('answer', None)
            if question.required and number is None:
                return None, MissingRequiredAnswer()

            if number is not None and not is_number(number):
                return None, OutOfRangeAnswer()
            if number is not None:
                try:
                    number = Decimal(number)
                except:
                    try:
                        import unicodedata
                        number = unicodedata.numeric(number)
                    except (TypeError, ValueError):
                        return None, OutOfRangeAnswer()

            parameters = question.parameters
            if number is not None and parameters.enable_min and number < parameters.min_value:
                return None, OutOfRangeAnswer()
            if number is not None and parameters.enable_max and number > parameters.max_value:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = NumberAnswer(
                    question=question,
                    submission=self,
                )
            answer.number = number
            answer.save()
            return answer, None
        elif question.question_type == Question.DROPDOWN:
            choices = post_data.getlist('answer')
            if question.required and len(choices) == 0:
                return None, MissingRequiredAnswer()
            if len(choices) > 1:
                return None, OutOfRangeAnswer()

            if answer is None:
                answer = DropdownAnswer(
                    question=question,
                    submission=self
                )
                answer.save()
            answer.choices.clear()
            for choice_id in choices:
                if choice_id is not None:
                    try:
                        choice = Choice.objects.get(pk=choice_id)
                        answer.choices.add(choice)
                    except:
                        return None, OutOfRangeAnswer()

            return answer, None
        elif question.question_type == Question.LEGAL:
            y = post_data.get('answer', None)
            if y not in ['accept', 'no_accept', None]:
                return None, OutOfRangeAnswer()

            if y == 'accept':
                y = True
            elif y == 'no_accept':
                y = False
            if y is None and question.required:
                return None, MissingRequiredAnswer()

            if answer is None:
                answer = LegalAnswer(
                    question=question,
                    submission=self,
                )
            answer.accept = y
            answer.save()
            return answer, None
        elif question.question_type == Question.FILE_UPLOAD:
            logger.debug(f'File Upload {post_data} {files_data}')
            if question.required and len(files_data) == 0:
                return None, MissingRequiredAnswer()
            form = FileUploadAnswerForm(post_data, files_data)
            if form.is_valid():
                answer = form.save(commit=False)
                answer.question = question
                answer.submission = self
                answer.save()
                logger.debug(f'<FileUploadAnswer:{answer}>')
                return answer, None
            else:
                logger.warn(f'Failed to validate form {form.errors}')
                return None, OutOfRangeAnswer()
        elif question.question_type == Question.PAYMENT:
            return None, None
        elif question.question_type == Question.WEBSITE:
            url = post_data.get('answer', None)
            if question.required and is_empty(url):
                return None, MissingRequiredAnswer()

            if url is not None:
                parsed = urlparse(url)
                if is_empty(parsed.netloc):
                    return None, OutOfRangeAnswer()

            if answer is None:
                answer = WebsiteAnswer(
                    question=question,
                    submission=self,
                )
            answer.url = url
            answer.save()
            return answer, None
        return None, None


class FilledField(BaseModel):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    field = models.ForeignKey(HiddenField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)


class Answer(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class MultipleChoiceAnswer(Answer):
    choices = models.ManyToManyField(Choice)
    other = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    @property
    def answer(self):
        answers = []
        for choice in self.choices.all():
            answers.append(choice.choice)
        if self.other is not None and self.other != "":
            answers.append(self.other)
        return answers

    def __str__(self):
        return f'{self.short_id} {self.choices.all()} {self.other}'


class PhoneNumberAnswer(Answer):
    phone_number = PhoneNumberField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(self.phone_number)

    @property
    def answer(self):
        return self.phone_number

    def __str__(self):
        return f'{self.short_id} {self.phone_number}'


class ShortTextAnswer(Answer):
    short_text = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    @property
    def text(self):
        return self.short_text

    @property
    def answer(self):
        return self.short_text

    def __str__(self):
        return f'{self.short_id} {self.short_text}'


class LongTextAnswer(Answer):
    long_text = models.TextField(blank=True, null=True, default=None)

    @property
    def text(self):
        return self.long_text

    @property
    def answer(self):
        return self.long_text

    def __str__(self):
        return f'{self.short_id} {self.long_text}'


class PictureChoiceAnswer(Answer):
    choices = models.ManyToManyField(Choice)
    other = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    @property
    def answer(self):
        return self.choices.all()

    def __str__(self):
        return f'{self.short_id} {self.choices.all()}'


class YesNoAnswer(Answer):
    yes = models.BooleanField(blank=True, null=True, default=None)

    @property
    def boolean(self):
        return self.yes

    @property
    def answer(self):
        return self.yes

    def __str__(self):
        return f'{self.short_id} {"Yes" if self.yes else "No"}'


class EmailAnswer(Answer):
    email = models.EmailField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(self.email)

    @property
    def answer(self):
        return self.email

    def __str__(self):
        return f'{self.short_id} {self.email}'


class OpinionScaleAnswer(Answer):
    opinion = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None)

    @property
    def number(self):
        return self.opinion

    @property
    def answer(self):
        return self.opinion

    def __str__(self):
        return f'{self.short_id} {self.opinion}'


class RatingAnswer(Answer):
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None)

    @property
    def number(self):
        return self.rating

    @property
    def answer(self):
        return self.rating

    def __str__(self):
        return f'{self.short_id} {self.rating}'


class DateAnswer(Answer):
    date = models.DateField(blank=True, null=True, default=None)

    @property
    def answer(self):
        return self.date

    def __str__(self):
        return f'{self.short_id} {self.date}'


class NumberAnswer(Answer):
    number = models.DecimalField(
        decimal_places=PRECISION, max_digits=MAX_DIGITS, blank=True, null=True, default=None)

    @property
    def answer(self):
        return self.number

    def __str__(self):
        return f'{self.short_id} {self.number}'


class DropdownAnswer(Answer):
    choices = models.ManyToManyField(Choice)
    other = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    @property
    def answer(self):
        return self.choices.all()

    def __str__(self):
        return f'{self.short_id} {self.choices.all()} {self.other}'


class LegalAnswer(Answer):
    accept = models.BooleanField(blank=True, null=True, default=None)

    @property
    def boolean(self):
        return self.accept

    @property
    def answer(self):
        return self.accept

    def __str__(self):
        return f'{self.short_id} {self.accept}'


def survey_directory(instance, filename):
    return 'files/survey/{}/{}/{}'.format(instance.submission.survey.id, instance.submission.id, filename)


class FileUploadAnswer(Answer):
    file = models.FileField(blank=True,
                            null=True, default=None, upload_to=survey_directory)

    @property
    def answer(self):
        return self.file

    def __str__(self):
        return f'{self.short_id} {self.file}'


class PaymentAnswer(Answer):
    token = models.CharField(
        max_length=1024, blank=True, null=True, default=None)


class WebsiteAnswer(Answer):
    url = models.URLField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(url)

    @property
    def answer(self):
        return self.url

    def __str__(self):
        return f'{self.short_id} {self.url}'


#
# LOGIC JUMPS
#

class RuleSet(BaseModel):
    # The question this belongs to
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # where to jump when conditions are met
    jump_to = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='jump_to')
    # To order rulesets when a question has more than one
    index = models.PositiveIntegerField()

    @property
    def conditions(self):
        conditions = []
        for condition in self.textcondition_set.all():
            conditions.append(condition)
        for condition in self.numbercondition_set.all():
            conditions.append(condition)
        for condition in self.choicecondition_set.all():
            conditions.append(condition)
        for condition in self.booleancondition_set.all():
            conditions.append(condition)
        for condition in self.datecondition_set.all():
            conditions.append(condition)
        return sorted(conditions, key=lambda condition: condition.index)

    def evaluate(self, submission):
        logger.debug(
            f"{self.short_id} evaluating for submission {submission.short_id}")
        value = None
        answers = submission.answers()
        logger.debug(
            f"{self.short_id} submission {submission.short_id} has {len(answers)} answer(s)")
        logger.debug(
            f"{self.short_id} has {len(self.conditions)} condition(s)")
        for condition in self.conditions:
            logger.debug(f"{self.short_id} checking condition {condition}")
            for answer in answers:
                if answer.question.id == condition.tested.id:
                    logger.debug(
                        f"Condition {condition.short_id} testing against {condition.tested.short_id} which we have answer {answer.short_id}")
                    current = condition.evaluate(answer)
                    logger.debug(
                        f"condition {condition.short_id} evaluated to {current}")
                    if value is None:
                        value = current
                    else:
                        logger.debug(f"Chaining using {condition.operand}")
                        if condition.operand == Condition.OR:
                            value = value or current
                        else:
                            value = value and current
        return self.jump_to if value else None

    def __str__(self):
        return f'{self.short_id} #{self.index} <Question:{self.question}> => <Question:{self.jump_to}>'


class Condition(BaseModel):
    TEXT = 'T'
    NUMBER = 'N'
    CHOICE = 'C'
    BOOLEAN = 'B'
    DATE = 'D'

    OR = 'OR'
    AND = 'AND'
    OPERAND = [
        (OR, 'Or'),
        (AND, 'And'),
    ]
    # which ruleset this belongs to
    ruleset = models.ForeignKey(RuleSet, on_delete=models.CASCADE)
    index = models.PositiveIntegerField()  # order in the chain
    # the question tested by this condition
    tested = models.ForeignKey(Question, on_delete=models.CASCADE)
    # when index > 0, the operand to use
    operand = models.CharField(
        max_length=3, choices=OPERAND, blank=True, null=True, default=None)

    class Meta:
        abstract = True


class TextCondition(Condition):
    EQUAL = 'EQ'
    NOT_EQUAL = 'NEQ'
    STARTS_WITH = 'SW'
    ENDS_WITH = 'EW'
    CONTAINS = 'C'
    DOES_NOT_CONTAINS = 'DNC'
    MATCHES = [
        (EQUAL, 'Equal'),
        (NOT_EQUAL, 'Not Equal'),
        (STARTS_WITH, 'Starts With'),
        (ENDS_WITH, 'Ends With'),
        (CONTAINS, 'Contains'),
        (DOES_NOT_CONTAINS, 'Does Not Contain'),
    ]
    match = models.CharField(max_length=3, choices=MATCHES)
    pattern = models.TextField()

    def evaluate(self, answer):
        if self.match == TextCondition.EQUAL:
            return answer.text == self.pattern
        elif self.match == TextCondition.NOT_EQUAL:
            return answer.text != self.pattern
        elif self.match == TextCondition.STARTS_WITH:
            return answer.text.startswith(self.pattern)
        elif self.match == TextCondition.ENDS_WITH:
            return answer.text.endswith(self.pattern)
        elif self.match == TextCondition.CONTAINS:
            return self.pattern in answer.text
        elif self.match == TextCondition.DOES_NOT_CONTAINS:
            return self.pattern not in answer.text
        return False

    def __str__(self):
        return f'{self.short_id} {self.match} {self.pattern} {self.operand}'


class NumberCondition(Condition):
    EQUAL = 'EQ'
    NOT_EQUAL = 'NEQ'
    LOWER_THAN = 'LT'
    LOWER_THAN_OR_EQUAL = 'LTOEQ'
    GREATER_THAN = 'GT'
    GREATER_THAN_OR_EQUAL = 'GTOEQ'
    MATCHES = [
        (EQUAL, 'Equal'),
        (NOT_EQUAL, 'Not Equal'),
        (LOWER_THAN, 'Lower Than'),
        (LOWER_THAN_OR_EQUAL, 'Lower Than Or Equal'),
        (GREATER_THAN, 'Greater Than'),
        (GREATER_THAN_OR_EQUAL, 'Greater Than Or Equal'),
    ]
    match = models.CharField(max_length=5, choices=MATCHES)
    pattern = models.DecimalField(
        max_digits=MAX_DIGITS, decimal_places=PRECISION)

    def evaluate(self, answer):
        if self.match == NumberCondition.EQUAL:
            return self.pattern == answer.number
        elif self.match == NumberCondition.NOT_EQUAL:
            return self.pattern != answer.number
        elif self.match == NumberCondition.LOWER_THAN:
            return self.number < self.pattern
        elif self.match == NumberCondition.LOWER_THAN_OR_EQUAL:
            return self.number <= self.pattern
        elif self.match == NumberCondition.GREATER_THAN:
            return self.number > self.pattern
        elif self.match == NumberCondition.GREATER_THAN_OR_EQUAL:
            return self.number >= self.pattern
        return False

    def __str__(self):
        return f'{self.short_id} {self.match} {self.pattern} {self.operand}'


class ChoiceCondition(Condition):
    IS = 'IS'
    IS_NOT = 'ISN'
    MATCHES = [
        (IS, 'Is'),
        (IS_NOT, 'Is Not'),
    ]
    match = models.CharField(max_length=3, choices=MATCHES)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    def evaluate(self, answer):
        if self.match == ChoiceCondition.IS:
            return self.choice in answer.choices.all()
        elif self.match == ChoiceCondition.IS_NOT:
            return self.choice not in answer.choices.all()
        return False

    def __str__(self):
        return f'{self.short_id} {self.match} <Choice:{self.choice}> {self.operand}'


class BooleanCondition(Condition):
    IS = 'IS'
    IS_NOT = 'ISN'
    MATCHES = [
        (IS, 'Is'),
        (IS_NOT, 'Is Not'),
    ]
    match = models.CharField(max_length=3, choices=MATCHES)
    boolean = models.BooleanField()

    def evaluate(self, answer):
        if self.match == BooleanCondition.IS:
            return answer.boolean == self.boolean
        elif self.match == BooleanCondition.IS_NOT:
            return answer.boolean != self.boolean

    def __str__(self):
        return f'{self.short_id} {self.match} {self.boolean} {self.operand}'


class DateCondition(Condition):
    IS_ON = 'IS'
    IS_NOT_ON = 'ISN'
    IS_BEFORE = 'ISB'
    IS_BEFORE_OR_ON = 'ISBOO'
    IS_AFTER = 'ISA'
    IS_AFTER_OR_ON = 'ISAOO'
    MATCHES = [
        (IS_ON, 'Is on'),
        (IS_NOT_ON, 'Is not on'),
        (IS_BEFORE, 'Is before'),
        (IS_BEFORE_OR_ON, 'Is before or on'),
        (IS_AFTER, 'Is after'),
        (IS_AFTER_OR_ON, 'Is after or on'),
    ]
    match = models.CharField(max_length=5, choices=MATCHES)
    date = models.DateField()

    def evaluate(self, answer):
        if self.match == DateCondition.IS_ON:
            return answer.date == self.date
        elif self.match == DateCondition.IS_NOT_ON:
            return answer.date != self.date
        elif self.match == DateCondition.IS_BEFORE:
            return answer.date < self.date
        elif self.match == DateCondition.IS_BEFORE_OR_ON:
            return answer.date <= self.date
        elif self.match == DateCondition.IS_AFTER:
            return answer.date > self.date
        elif self.match == DateCondition.IS_AFTER_OR_ON:
            return answer.date >= self.date

    def __str__(self):
        return f'{self.short_id} {self.match} {self.date} {self.operand}'


class FileUploadAnswerForm(forms.ModelForm):
    class Meta:
        model = FileUploadAnswer
        fields = ['file']
