import uuid

from dateutil import parser
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


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


class Survey(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)
    published = models.BooleanField(default=False)
    first_question = models.ForeignKey(
        'Question', on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='first_question')
    last_question = models.ForeignKey('Question', on_delete=models.CASCADE,
                                      blank=True, null=True, default=None, related_name='last_question')

    def add_hidden_field(self, name):
        # Do we already have it?
        qs = HiddenField.objects.filter(survey=self, name=name)
        if qs.count() == 0:
            return HiddenField.objects.create(
                survey=self,
                name=name,
            )
        else:
            return qs.first()

    def append_question(self, question):
        if self.first_question is None:
            self.first_question = question
            self.last_question = question
            self.save()
        else:
            self.last_question.next_question = question
            self.last_question.save()

            self.last_question = question
            self.save()

    def add_welcome_screen(self, question, description=None, button_label='Start', image_url=None, video_url=None):
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
            parameters = WelcomeParameters.objects.create(
                question=question,
                button_label=button_label,
                image_url=image_url,
                video_url=video_url,
            )
            self.append_question(question)
            return question

    def add_thank_you_screen(self, question, description=None, show_button=True, button_label='Done', button_link=None, show_social_media=True, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.THANK_YOU_SCREEN,
            required=False,
        )
        parameters = ThankYouParameters.objects.create(
            question=question,
            show_button=show_button,
            button_label=button_label,
            button_link=button_link,
            show_social_media=show_social_media,
            image_url=image_url,
            video_url=video_url,
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
                            video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.MULTIPLE_CHOICE,
            required=required,
        )
        parameters = MultipleChoiceParameters.objects.create(
            question=question,
            multiple_selection=multiple_selection,
            randomize=randomize,
            other_option=other_option,
            vertical_alignment=vertical_alignment,
            image_url=image_url,
            video_url=video_url,
        )
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice,
            )
        self.append_question(question)
        return question

    def add_phone_number(self, question, required=True, description=None, default_country_code=1, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PHONE_NUMBER,
            required=required,
        )
        parameters = PhoneNumberParameters.objects.create(
            question=question,
            default_country_code=default_country_code,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_short_text(self, question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.SHORT_TEXT,
            required=required,
        )
        parameters = ShortTextParameters.objects.create(
            question=question,
            limit_character=limit_character,
            limit=limit,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_long_text(self, question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.LONG_TEXT,
            required=required,
        )
        parameters = LongTextParameters.objects.create(
            question=question,
            limit_character=limit_character,
            limit=limit,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_statement(self, question, description=None, button_label='Next', show_quotation_mark=True, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.STATEMENT,
            required=False,
        )
        parameters = StatementParameters.objects.create(
            question=question,
            button_label=button_label,
            show_quotation_mark=show_quotation_mark,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_picture_choice(self, question, required=False, description=None, multiple_selection=False, randomize=False, other_option=False, choices=[], show_labels=False, supersize=False, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PICTURE_CHOICE,
            required=required,
        )
        parameters = PictureChoiceParameters.objects.create(
            question=question,
            multiple_selection=multiple_selection,
            randomize=randomize,
            other_option=other_option,
            show_labels=show_labels,
            supersize=supersize,
            image_url=image_url,
            video_url=video_url,
        )

        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice['label'],
                image_url=choice['image_url'],
            )
        self.append_question(question)
        return question

    def add_yes_no(self, question, required=False, description=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.YES_NO,
            required=required,
        )
        parameters = YesNoParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_email(self, question, required=False, description=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.EMAIL,
            required=required,
        )
        parameters = EmailParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
        )

        self.append_question(question)
        return question

    def add_opinion_scale(self, question, required=False, description=None, start_at_one=True, number_of_steps=11, show_labels=False, left_label=None, center_label=None, right_label=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.OPINION_SCALE,
            required=required,
        )
        parameters = OpinionScaleParameters.objects.create(
            question=question,
            start_at_one=start_at_one,
            number_of_steps=number_of_steps,
            show_labels=show_labels,
            left_label=left_label,
            center_label=center_label,
            right_label=right_label,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_rating(self, question, required=False, description=None, number_of_steps=5, shape='S', image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.RATING,
            required=required,
        )
        parameters = RatingParameters.objects.create(
            question=question,
            number_of_steps=number_of_steps,
            shape=shape,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_date(self, question, required=False, description=None, date_format='A', date_separator='/', image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.DATE,
            required=required,
        )
        parameters = DateParameters.objects.create(
            question=question,
            date_format=date_format,
            date_separator=date_separator,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_number(self, question, required=False, description=None, enable_min=False, min_value=None, enable_max=False, max_value=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.NUMBER,
            required=required,
        )
        parameters = NumberParameters.objects.create(
            question=question,
            enable_min=enable_min,
            min_value=min_value,
            enable_max=enable_max,
            max_value=max_value,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_dropdown(self, question, required=False, description=None, randomize=False, alphabetical=False, choices=[], image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.DROPDOWN,
            required=required,
        )
        parameters = DropdownParameters.objects.create(
            question=question,
            randomize=randomize,
            alphabetical=alphabetical,
            image_url=image_url,
            video_url=video_url,
        )
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice=choice,
            )
        self.append_question(question)
        return question

    def add_legal(self, question, required=False, description=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.LEGAL,
            required=required,
        )
        parameters = LegalParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_file_upload(self, question, required=False, description=None, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.FILE_UPLOAD,
            required=required,
        )
        parameters = FileUploadParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_payment(self, question, required=False, description=None, currency='USD', price=0.0, stripe_token=None, button_label='Pay', image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.PAYMENT,
            required=required,
        )
        parameters = PaymentParameters.objects.create(
            question=question,
            currency=currency,
            price=price,
            stripe_token=stripe_token,
            button_label=button_label,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question

    def add_website(self, question, description=None, required=False, image_url=None, video_url=None):
        question = Question.objects.create(
            survey=self,
            question=question,
            description=description,
            question_type=Question.WEBSITE,
            required=required,
        )
        parameters = WebsiteParameters.objects.create(
            question=question,
            image_url=image_url,
            video_url=video_url,
        )
        self.append_question(question)
        return question


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
        (THANK_YOU_SCREEN, 'Thank You Screen'),
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
    ]
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.TextField()
    description = models.TextField(blank=True, null=True, default=None)
    question_type = models.CharField(max_length=2, choices=TYPES)
    required = models.BooleanField()
    next_question = models.ForeignKey('Question', on_delete=models.CASCADE,
                                      related_name='previous_question', blank=True, null=True, default=None)

    def next(self, submission):
        # Any rules
        qs = self.ruleset_set.all()
        if qs.count() == 0:
            print(
                f"{self.short_id} has no ruleset, returning default {self.next_question}")
            return self.next_question
        print(f"{self.short_id} has {qs.count()} ruleset(s)")
        for ruleset in qs:
            print(f"{self.short_id} evaluating ruleset {ruleset.short_id}")
            q = ruleset.evaluate(submission)
            print(f"{self.short_id} evaluation of {ruleset.id} returned {q}")
            if q is not None:
                return q
        # If none of the ruleset evaluated successfully, fallback to next_question
        print(
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
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True, default=None)
    video_url = models.URLField(blank=True, null=True, default=None)

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
    default_country_code = models.PositiveIntegerField()


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
    SHAPES = [
        ('S_', 'Stars'),
        ('T_', 'Thumbs'),
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
    SEPARATORS = [
        ('-', '-'),
        ('.', '.'),
        ('/', '/'),
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

    def __str__(self):
        return f'{self.short_id} {self.choice}'


#
# SUBMISSIONS & ANSWERS
#

class Submission(BaseModel):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
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

    def record_answer(self, question, post_data, files_data):
        if question.question_type == Question.WELCOME_SCREEN:
            return None
        elif question.question_type == Question.THANK_YOU_SCREEN:
            return None
        elif question.question_type == Question.MULTIPLE_CHOICE:
            print("Recording a multiple choice answer")
            answer = MultipleChoiceAnswer(
                question=question,
                submission=self,
            )
            answer.save()
            choice_id = post_data.get('answer', None)
            print(f"Raw response {choice_id}")
            if choice_id is not None:
                choice = Choice.objects.get(pk=choice_id)
                print(f"Picked up choice {choice}")
                answer.choices.add(choice)

            return answer
        elif question.question_type == Question.PHONE_NUMBER:
            answer = PhoneNumberAnswer(
                question=question,
                submission=self,
            )
            answer.phone_number = post_data.get('answer', None)
            answer.save()
            return answer
        elif question.question_type == Question.SHORT_TEXT:
            answer = ShortTextAnswer(
                question=question,
                submission=self,
            )
            answer.short_text = post_data.get('answer', None)
            answer.save()
            return answer
        elif question.question_type == Question.LONG_TEXT:
            answer = LongTextAnswer(
                question=question,
                submission=self,
            )
            answer.long_text = post_data.get('answer', None)
            answer.save()
            return answer
        elif question.question_type == Question.STATEMENT:
            return None
        elif question.question_type == Question.PICTURE_CHOICE:
            answer = PictureChoiceAnswer(
                question=question,
                submission=self
            )
            answer.save()
            choice_id = post_data.get('answer', None)
            if choice_id is not None:
                choice = Choice.objects.get(pk=choice_id)
                answer.choices.add(choice)
            return answer
        elif question.question_type == Question.YES_NO:
            y = post_data.get('answer', None)
            if y == 'Yes':
                y = True
            elif y == 'No':
                y = False
            answer = YesNoAnswer(
                question=question,
                submission=self,
                yes=y,
            )
            answer.save()
            return answer
        elif question.question_type == Question.EMAIL:
            answer = EmailAnswer(
                question=question,
                submission=self,
            )
            answer.email = post_data.get('answer', None)
            answer.save()
            return answer
        elif question.question_type == Question.OPINION_SCALE:
            level = post_data.get('answer', None)
            if level is not None:
                level = Decimal(level)
            answer = OpinionScaleAnswer(
                question=question,
                submission=self,
                opinion=level,
            )
            answer.save()
            return answer
        elif question.question_type == Question.RATING:
            answer = RatingAnswer(
                question=question,
                submission=self,
            )
            level = post_data.get('answer', None)
            if level is not None:
                level = Decimal(level)
            answer.rating = level
            answer.save()
            return answer
        elif question.question_type == Question.DATE:
            answer = DateAnswer(
                question=question,
                submission=self,
            )
            raw = post_data.get('answer', None)
            if raw is not None:
                answer.date = make_aware(parser.parse(raw))
            answer.save()
            return answer
        elif question.question_type == Question.NUMBER:
            answer = NumberAnswer(
                question=question,
                submission=self,
            )
            answer.number = post_data.get('answer', None)
            answer.save()
            return answer
        elif question.question_type == Question.DROPDOWN:
            answer = DropdownAnswer(
                question=question,
                submission=self
            )
            answer.save()
            choice_id = post_data.get('answer', None)
            if choice_id is not None:
                choice = Choice.objects.get(pk=choice_id)
                answer.choices.add(choice)

            return answer
        elif question.question_type == Question.LEGAL:
            y = post_data.get('answer', None)
            if y == 'accept':
                y = True
            elif y == 'no_accept':
                y = False
            answer = LegalAnswer(
                question=question,
                submission=self,
                accept=y,
            )
            answer.save()
            return answer
        elif question.question_type == Question.FILE_UPLOAD:
            return None
        elif question.question_type == Question.PAYMENT:
            return None
        elif question.question_type == Question.WEBSITE:
            answer = WebsiteAnswer(
                question=question,
                submission=self,
            )
            answer.url = post_data.get('answer', None)
            answer.save()
            return answer
        return None


class Answer(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class MultipleChoiceAnswer(Answer):
    choices = models.ManyToManyField(Choice)
    other = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.short_id} {self.choices.all()} {self.other}'


class PhoneNumberAnswer(Answer):
    phone_number = PhoneNumberField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(self.phone_number)

    def __str__(self):
        return f'{self.short_id} {self.phone_number}'


class ShortTextAnswer(Answer):
    short_text = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    @property
    def text(self):
        return self.short_text

    def __str__(self):
        return f'{self.short_id} {self.short_text}'


class LongTextAnswer(Answer):
    long_text = models.TextField(blank=True, null=True, default=None)

    @property
    def text(self):
        return self.long_text

    def __str__(self):
        return f'{self.short_id} {self.long_text}'


class PictureChoiceAnswer(Answer):
    choices = models.ManyToManyField(Choice)

    def __str__(self):
        return f'{self.short_id} {self.choices.all()}'


class YesNoAnswer(Answer):
    yes = models.BooleanField(blank=True, null=True, default=None)

    @property
    def boolean(self):
        return self.yes

    def __str__(self):
        return f'{self.short_id} {"Yes" if self.yes else "No"}'


class EmailAnswer(Answer):
    email = models.EmailField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(self.email)

    def __str__(self):
        return f'{self.short_id} {self.email}'


class OpinionScaleAnswer(Answer):
    opinion = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None)

    @property
    def number(self):
        return self.opinion

    def __str__(self):
        return f'{self.short_id} {self.opinion}'


class RatingAnswer(Answer):
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None)

    @property
    def number(self):
        return self.rating

    def __str__(self):
        return f'{self.short_id} {self.rating}'


class DateAnswer(Answer):
    date = models.DateField(blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.short_id} {self.date}'


class NumberAnswer(Answer):
    number = models.DecimalField(
        decimal_places=PRECISION, max_digits=MAX_DIGITS, blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.short_id} {self.number}'


class DropdownAnswer(Answer):
    choices = models.ManyToManyField(Choice)
    other = models.CharField(
        max_length=1024, blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.short_id} {self.choices.all()} {self.other}'


class LegalAnswer(Answer):
    accept = models.BooleanField(blank=True, null=True, default=None)

    @property
    def boolean(self):
        return self.accept

    def __str__(self):
        return f'{self.short_id} {self.accept}'


class FileUploadAnswer(Answer):
    file = models.FileField(blank=True, null=True, default=None)


class PaymentAnswer(Answer):
    token = models.CharField(
        max_length=1024, blank=True, null=True, default=None)


class WebsiteAnswer(Answer):
    url = models.URLField(blank=True, null=True, default=None)

    @property
    def text(self):
        return str(url)

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
        return sorted(conditions, key=lambda condition: condition.index)

    def evaluate(self, submission):
        print(f"{self.short_id} evaluating for submission {submission.short_id}")
        value = None
        answers = submission.answers()
        print(
            f"{self.short_id} submission {submission.short_id} has {len(answers)} answer(s)")
        print(f"{self.short_id} has {len(self.conditions)} condition(s)")
        for condition in self.conditions:
            print(f"{self.short_id} checking condition {condition}")
            for answer in answers:
                if answer.question.id == condition.tested.id:
                    print(
                        f"Condition {condition.short_id} testing against {condition.tested.short_id} which we have answer {answer.short_id}")
                    current = condition.evaluate(answer)
                    print(
                        f"condition {condition.short_id} evaluated to {current}")
                    if value is None:
                        value = current
                    else:
                        print(f"Chaining using {condition.operand}")
                        if condition.operand == Condition.OR:
                            value = value or current
                        else:
                            value = value and current
        return self.jump_to if value else None


class Condition(BaseModel):
    OR = 'OS'
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
    MATCHES = [
        (EQUAL, 'Equal'),
        (NOT_EQUAL, 'Not Equal'),
        (STARTS_WITH, 'Starts With'),
        (ENDS_WITH, 'Ends With'),
        (CONTAINS, 'Contains'),
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
        return False


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
            print(
                f"[=] self.boolean = {self.boolean} answer.boolean = {answer.boolean}")
            return answer.boolean == self.boolean
        elif self.match == BooleanCondition.IS_NOT:
            print(
                f"[!] self.boolean = {self.boolean} answer.boolean = {answer.boolean}")
            return answer.boolean != self.boolean

    def __str__(self):
        return f'{self.short_id} {self.match} {self.boolean}'


class Builder:
    links = []

    def add_text_condition(self, question, pattern, match=TextCondition.EQUAL, operand=Condition.AND):
        links.push({
            'type': 'text',
            'question': question,
            'pattern': pattern,
            'match': match,
            'operand': operand,
        })
        return self

    def add_number_condition(self, question, pattern, match=NumberCondition.EQUAL, operand=Condition.AND):
        links.push({
            'type': 'number',
            'question': question,
            'pattern': pattern,
            'match': match,
            'operand': operand,
        })
        return self

    def add_choice_condition(self, question, choice, match=ChoiceCondition.IS, operand=Condition.AND):
        links.push({
            'type': 'choice',
            'question': question,
            'choice': choice,
            'match': match,
            'operand': operand,
        })
        return self

    def add_boolean_condition(self, question, boolean, match=BooleanCondition.IS, operand=Condition.AND):
        links.push({
            'type': 'boolean',
            'question': question,
            'boolean': boolean,
            'match': match,
            'operand': operand,
        })
        return self

    def build(self, jump_to):
        pass
