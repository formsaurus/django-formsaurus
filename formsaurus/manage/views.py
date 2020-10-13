import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum, Case, When, Value, IntegerField
from django.conf import settings

from formsaurus.models import (Question, Submission, Choice, RuleSet, Condition,
                               TextCondition, BooleanCondition, ChoiceCondition, BooleanCondition, DateCondition, NumberCondition)
from formsaurus.serializer import Serializer
from formsaurus.utils import get_survey_model
from formsaurus.manage.forms import (SurveyForm, HiddenFieldForm, AddQuestionForm, WelcomeParametersForm, ThankYouParametersForm, MultipleChoiceParametersForm, PhoneNumberParametersForm, ShortTextParametersForm, LongTextParametersForm, StatementParametersForm, PictureChoiceParametersForm,
                              YesNoParametersForm, EmailParametersForm, OpinionScaleParametersForm, RatingParametersForm, DateParameters, NumberParametersForm, DropdownParametersForm, LegalParametersForm, FileUploadParametersForm, PaymentParametersForm, WebsiteParametersForm)
from formsaurus.manage.unsplash import Unsplash
from formsaurus.manage.pexels import Pexels
from formsaurus.manage.tenor import Tenor

logger = logging.getLogger('formsaurus')

Survey = get_survey_model()

class ManageView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:surveys'

    def get(self, request):
        return redirect(self.success_url)


class SurveysView(LoginRequiredMixin, View):
    """List all forms own by authorized user."""
    template_name = 'formsaurus/manage/surveys.html'

    def get(self, request):
        context = {}
        context['surveys'] = []
        for survey in Survey.objects.filter(user=request.user).order_by('-created_at'):
            context['surveys'].append(Serializer.survey(survey))
        return render(request, self.template_name, context)


class SurveyWizardView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_wizard.html'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        context = {}
        # context['survey'] = Serializer.survey(survey)
        context['survey'] = survey
        if survey.published:
            # Stats about submissions
            context['submissions'] = {}
            row = Submission.objects.filter(survey=survey, is_preview=False).aggregate(
                count=Count('id'),
                sum=Sum(Case(
                    When(completed=True, then=1),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            )
            completed = 1 if row['sum'] is True else 0 if row['sum'] is None or row['sum'] is False else row['sum']
            context['submissions']['count'] = row['count']
            context['submissions']['completed'] = completed
            context['submissions']['ratio'] = completed / \
                row['count'] * 100 if row['count'] > 0 else 0

            pass
        return render(request, self.template_name, context)


class AddQuestionView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add_question.html'
    add_question_url = 'formsaurus_manage:survey_add_question'

    def get(self, request, survey_id, question_type=None):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404

        # Do we already have a welcome screen?
        has_ws = survey.question_set.filter(
            question_type=Question.WELCOME_SCREEN).count() > 0
        default_type = Question.WELCOME_SCREEN if not has_ws else Question.YES_NO
        question_type = question_type if question_type is not None else default_type
        context = {}
        context['has_unsplash'] = hasattr(settings, 'UNSPLASH_ACCESS_KEY')
        context['has_pexels'] = hasattr(settings, 'PEXELS_API_KEY')
        context['has_tenor'] = hasattr(settings, 'TENOR_API_KEY')
        context['survey'] = Serializer.survey(survey)
        # Allowed question types
        question_types = survey.question_types
        if has_ws:
            question_types.pop(Question.WELCOME_SCREEN)
        context['type'] = question_type
        context['type_name'] = question_types[question_type].name
        context['types'] = question_types

        context['shapes'] = survey.rating_shapes

        return render(request, self.template_name, context)

    def post(self, request, survey_id, question_type):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404

        question_form = AddQuestionForm(request.POST)
        parameters_form = None

        logger.info('Question Type %s', question_type)
        if question_form.is_valid():
            logger.debug('Valid question form')
            if question_type == Question.WELCOME_SCREEN:
                parameters_form = WelcomeParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_welcome_screen(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        button_label=parameters_form.cleaned_data['button_label'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Welcome Screen %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate welcome_screen parameters %s', parameters_form.errors)
            elif question_type == Question.THANK_YOU_SCREEN:
                parameters_form = ThankYouParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_thank_you_screen(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        show_button=parameters_form.cleaned_data['show_button'],
                        button_label=parameters_form.cleaned_data['button_label'],
                        button_link=parameters_form.cleaned_data['button_link'],
                        show_social_media=parameters_form.cleaned_data['show_social_media'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Thank You Screen %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate thank_you_screen parameters %s', parameters_form.errors)
            elif question_type == Question.MULTIPLE_CHOICE:
                parameters_form = MultipleChoiceParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_multiple_choice(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        multiple_selection=parameters_form.cleaned_data['multiple_selection'],
                        randomize=parameters_form.cleaned_data['randomize'],
                        other_option=parameters_form.cleaned_data['other_option'],
                        choices=request.POST.getlist('choice'),
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Multiple Choice %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate multiple_choice parameters %s', parameters_form.errors)
            elif question_type == Question.PHONE_NUMBER:
                parameters_form = PhoneNumberParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_phone_number(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        default_country_code=parameters_form.cleaned_data['default_country_code'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Phone Number %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate phone_number parameters %s', parameters_form.errors)
            elif question_type == Question.SHORT_TEXT:
                parameters_form = ShortTextParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_short_text(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        limit_character=parameters_form.cleaned_data['limit_character'],
                        limit=parameters_form.cleaned_data['limit'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Short Text %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate short_text parameters %s', parameters_form.errors)
            elif question_type == Question.LONG_TEXT:
                parameters_form = LongTextParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_long_text(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        limit_character=parameters_form.cleaned_data['limit_character'],
                        limit=parameters_form.cleaned_data['limit'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Long Text %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate long_text parameters %s', parameters_form.errors)

            elif question_type == Question.STATEMENT:
                parameters_form = StatementParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_statement(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        button_label=parameters_form.cleaned_data['button_label'],
                        show_quotation_mark=parameters_form.cleaned_data['show_quotation_mark'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Statement %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate statement parameters %s', parameters_form.errors)
            elif question_type == Question.PICTURE_CHOICE:
                parameters_form = PictureChoiceParametersForm(request.POST)
                if parameters_form.is_valid():
                    images = request.POST.getlist('choice')
                    labels = request.POST.getlist('label')
                    choices = []
                    for index in range(len(images)):
                        choices.append({
                            'label': labels[index],
                            'image_url': images[index],
                        })

                    question = survey.add_picture_choice(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        multiple_selection=parameters_form.cleaned_data['multiple_selection'],
                        randomize=parameters_form.cleaned_data['randomize'],
                        other_option=parameters_form.cleaned_data['other_option'],
                        show_labels=parameters_form.cleaned_data['show_labels'],
                        supersize=parameters_form.cleaned_data['supersize'],
                        choices=choices,
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Picture Choice %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate picture_choice parameters %s', parameters_form.errors)

            elif question_type == Question.YES_NO:
                parameters_form = YesNoParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_yes_no(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Yes/No %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate yes_no parameters %s', parameters_form.errors)
            elif question_type == Question.EMAIL:
                parameters_form = EmailParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_email(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Email %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate email parameters %s', parameters_form.errors)
            elif question_type == Question.OPINION_SCALE:
                parameters_form = OpinionScaleParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_opinion_scale(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        start_at_one=parameters_form.cleaned_data['start_at_one'],
                        number_of_steps=parameters_form.cleaned_data['number_of_steps'],
                        show_labels=parameters_form.cleaned_data['show_labels'],
                        left_label=parameters_form.cleaned_data['left_label'],
                        center_label=parameters_form.cleaned_data['center_label'],
                        right_label=parameters_form.cleaned_data['right_label'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Opinion Scale %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate opinion_scale parameters %s', parameters_form.errors)
            elif question_type == Question.RATING:
                parameters_form = RatingParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_rating(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        number_of_steps=parameters_form.cleaned_data['number_of_steps'],
                        shape=parameters_form.cleaned_data['shape'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Rating %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate rating parameters %s', parameters_form.errors)
            elif question_type == Question.DATE:
                parameters_form = DateParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_date(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        date_format=parameters_form.cleaned_data['date_format'],
                        date_separator=parameters_form.cleaned_data['date_separator'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Date %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate date parameters %s', parameters_form.errors)
            elif question_type == Question.NUMBER:
                parameters_form = NumberParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_number(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        enable_min=parameters_form.cleaned_data['enable_min'],
                        min_value=parameters_form.cleaned_data['min_value'],
                        enable_max=parameters_form.cleaned_data['enable_max'],
                        max_value=parameters_form.cleaned_data['max_value'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Number %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate number parameters %s', parameters_form.errors)
            elif question_type == Question.DROPDOWN:
                parameters_form = DropdownParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_dropdown(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        alphabetical=parameters_form.cleaned_data['alphabetical'],
                        randomize=parameters_form.cleaned_data['randomize'],
                        choices=request.POST.getlist('choice'),
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Dropdown %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate dropdown parameters %s', parameters_form.errors)
            elif question_type == Question.LEGAL:
                parameters_form = LegalParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_legal(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Email %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate email parameters %s', parameters_form.errors)
            elif question_type == Question.FILE_UPLOAD:
                parameters_form = FileUploadParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_file_upload(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created File Upload %s', question.id)
                    return redirect(self.add_question_url, survey.id)
            elif question_type == Question.PAYMENT:
                raise Http404
            elif question_type == Question.WEBSITE:
                parameters_form = WebsiteParametersForm(request.POST)
                if parameters_form.is_valid():
                    question = survey.add_website(
                        question_form.cleaned_data['question'],
                        description=question_form.cleaned_data['description'],
                        required=question_form.cleaned_data['required'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
                        orientation=parameters_form.cleaned_data['orientation'],
                        position_x=parameters_form.cleaned_data['position_x'],
                        position_y=parameters_form.cleaned_data['position_y'],
                        opacity=parameters_form.cleaned_data['opacity'],
                    )
                    logger.info('Created Email %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate email parameters %s', parameters_form.errors)

            else:
                logger.warning('Unsupported type %s', question_type)

        else:
            logger.warning('Failed to create question %s',
                           question_form.errors)
        # TODO need to handle any potential issues while adding a question to a form.
        context = {}
        context['form'] = question_form
        context['parameters'] = parameters_form
        raise Http404
        # return render(request, self.template_name, context)


class EditQuestionView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add_question.html'
    edit_question_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        if survey.published:
            raise Http404

        # Do we already have a welcome screen?
        has_ws = survey.question_set.filter(
            question_type=Question.WELCOME_SCREEN).count() > 0
        question_type = question.question_type
        context = {}

        context['has_unsplash'] = hasattr(settings, 'UNSPLASH_ACCESS_KEY')
        context['has_pexels'] = hasattr(settings, 'PEXELS_API_KEY')
        context['has_tenor'] = hasattr(settings, 'TENOR_API_KEY')
        context['survey'] = Serializer.survey(survey)
        # Allowed question types
        question_types = survey.question_types
        if has_ws:
            question_types.pop(Question.WELCOME_SCREEN)
        context['type'] = question_type
        context['type_name'] = question_types[question_type].name
        context['types'] = question_types
        context['shapes'] = survey.rating_shapes
        context['question'] = Serializer.question(question)
        if question.question_type == Question.RATING and question.parameters.shape is not None:
            context['question_shape'] = survey.rating_shapes[question.parameters.shape]

        return render(request, self.template_name, context)

    def post(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        if survey.published:
            raise Http404

        question_form = AddQuestionForm(request.POST, instance=question)
        parameters_form = None
        question_type = question.question_type

        if question_form.is_valid():
            # Update the question
            question = question_form.save()
            # Update parameters
            if question_type == Question.WELCOME_SCREEN:
                parameters_form = WelcomeParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate welcome_screen parameters %s', parameters_form.errors)
            elif question_type == Question.THANK_YOU_SCREEN:
                parameters_form = ThankYouParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate thank_you_screen parameters %s', parameters_form.errors)
            elif question_type == Question.MULTIPLE_CHOICE:
                parameters_form = MultipleChoiceParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    question.choice_set.all().delete()
                    position = 0
                    for choice in request.POST.getlist('choice'):
                        Choice.objects.create(
                            question=question,
                            choice=choice,
                            position=position,
                        )
                        position = position+1

                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate multiple_choice parameters %s', parameters_form.errors)
            elif question_type == Question.PHONE_NUMBER:
                parameters_form = PhoneNumberParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate phone_number parameters %s', parameters_form.errors)
            elif question_type == Question.SHORT_TEXT:
                parameters_form = ShortTextParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate short_text parameters %s', parameters_form.errors)
            elif question_type == Question.LONG_TEXT:
                parameters_form = LongTextParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate long_text parameters %s', parameters_form.errors)
            elif question_type == Question.STATEMENT:
                parameters_form = StatementParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate statement parameters %s', parameters_form.errors)
            elif question_type == Question.PICTURE_CHOICE:
                parameters_form = PictureChoiceParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    question.choice_set.all().delete()
                    images = request.POST.getlist('choice')
                    labels = request.POST.getlist('label')
                    position = 0
                    for index in range(len(images)):
                        Choice.objects.create(
                            question=question,
                            image_url=images[index],
                            choice=labels[index],
                            position=position,
                        )
                        position = position + 1

                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate picture_choice parameters %s', parameters_form.errors)

            elif question_type == Question.YES_NO:
                parameters_form = YesNoParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate yes_no parameters %s', parameters_form.errors)
            elif question_type == Question.EMAIL:
                parameters_form = EmailParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate email parameters %s', parameters_form.errors)
            elif question_type == Question.OPINION_SCALE:
                parameters_form = OpinionScaleParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate opinion_scale parameters %s', parameters_form.errors)
            elif question_type == Question.RATING:
                parameters_form = RatingParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate rating parameters %s', parameters_form.errors)
            elif question_type == Question.DATE:
                parameters_form = DateParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate date parameters %s', parameters_form.errors)
            elif question_type == Question.NUMBER:
                parameters_form = NumberParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate number parameters %s', parameters_form.errors)
            elif question_type == Question.DROPDOWN:
                parameters_form = DropdownParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    question.choice_set.all().delete()
                    position = 0
                    for choice in request.POST.getlist('choice'):
                        if choice != "":
                            Choice.objects.create(
                                question=question,
                                choice=choice,
                                position=position
                            )
                            position = position + 1
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate dropdown parameters %s', parameters_form.errors)
            elif question_type == Question.LEGAL:
                parameters_form = LegalParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate legal parameters %s', parameters_form.errors)
            elif question_type == Question.FILE_UPLOAD:
                parameters_form = FileUploadParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate file_upload parameters %s', parameters_form.errors)
            elif question_type == Question.PAYMENT:
                raise Http404
            elif question_type == Question.WEBSITE:
                parameters_form = WebsiteParametersForm(
                    request.POST, instance=question.parameters)
                if parameters_form.is_valid():
                    parameters_form.save()
                    return redirect(self.edit_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate website parameters %s', parameters_form.errors)

            else:
                logger.warning('Unsupported type %s', question_type)

        else:
            logger.warning('Failed to create question %s',
                           question_form.errors)


class DeleteQuestionView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        if survey.published:
            raise Http404
        survey.delete_question(question)
        return redirect(self.success_url, survey.id)


class QuestionUpView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        if survey.published:
            raise Http404
        survey.move_question_up(question)
        return redirect(self.success_url, survey.id)


class QuestionDownView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        if survey.published:
            raise Http404
        survey.move_question_down(question)
        return redirect(self.success_url, survey.id)


class SurveyAddView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add.html'
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request):
        context = {}
        context['form'] = SurveyForm()
        return render(request, self.template_name, context)

    def post(self, request):
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.save()
            return redirect(self.success_url, survey.id)
        else:
            context = {}
            context['form'] = form
            return render(request, self.template_name, context)

class SurveyEditView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add.html'
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404

        context = {}
        context['form'] = SurveyForm(instance=survey)
        context['survey'] = Serializer.survey(survey)
        return render(request, self.template_name, context)

    def post(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404

        form = SurveyForm(request.POST, instance=survey)
        if form.is_valid():
            survey = form.save()
            return redirect(self.success_url, survey.id)
        else:
            context = {}
            context['survey'] = Serializer.survey(survey)
            context['form'] = form
            return render(request, self.template_name, context)


class PublishSurveyView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        survey.publish()
        return redirect(self.success_url, survey.id)


class DeleteSurveyView(LoginRequiredMixin, View):
    success_url = 'formsaurus_manage:surveys'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        if not survey.published:
            survey.delete()
        return redirect(self.success_url)


class HiddenFieldView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add_hidden_field.html'
    success_url = 'formsaurus_manage:survey_wizard'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        context = {}
        context['survey'] = survey
        context['form'] = HiddenFieldForm()
        return render(request, self.template_name, context)

    def post(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        form = HiddenFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.survey = survey
            field.save()
            return redirect(self.success_url, survey.id)
        context = {}
        context['survey'] = survey
        context['form'] = form
        return render(request, self.template_name, context)


class SubmissionsView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/submissions.html'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        context = {}
        context['survey'] = survey
        return render(request, self.template_name, context)


class SubmissionView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/submission.html'

    def get(self, request, survey_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        submission = get_object_or_404(Submission, pk=submission_id)
        if submission.survey != survey:
            raise Http404

        context = {}
        context['survey'] = survey
        context['submission'] = submission
        return render(request, self.template_name, context)


class LogicView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/logic_add.html'

    def get(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        if survey.published:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404

        questions = []
        previous_questions = []
        found = False

        for q in survey.questions:
            questions.append(Serializer.question(q))
            if not found:
                if q != question:
                    previous_questions.append(Serializer.question(q))
                else:
                    previous_questions.append(Serializer.question(q))
                    found = True

        context = {}
        context['survey'] = Serializer.survey(survey)
        context['question'] = Serializer.question(question)
        context['question']['rules'] = []
        for ruleset in question.ruleset_set.all():
            rule = Serializer.ruleset(ruleset)
            rule['conditions'] = []
            for condition in ruleset.conditions:
                rule['conditions'].append(Serializer.condition(condition))
            context['question']['rules'].append(rule)

        context['questions'] = questions
        context['previous_questions'] = previous_questions
        return render(request, self.template_name, context)

    def post(self, request, survey_id, question_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        if survey.published:
            raise Http404
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404

        if question.question_type in [Question.WELCOME_SCREEN, Question.THANK_YOU_SCREEN, Question.STATEMENT]:
            return JsonResponse({'status': 'failed', 'error': 'Non answerable question'})

        logic = json.loads(request.body)
        default_to = get_object_or_404(Question, pk=logic['default_to'])

        # Delete any existing ruleset first.
        question.ruleset_set.all().delete()

        group_index = 0
        for group in logic['groups']:
            logger.debug(f'{group_index}) Creating new RuleSet')
            jump_to = get_object_or_404(Question, pk=group['jump_to'])
            logger.debug(f'     Jump to <Question:{jump_to}>')
            # Create a ruleset for this group
            rs = RuleSet.objects.create(
                question=question,
                jump_to=jump_to,
                index=group_index
            )
            logger.debug(f'     <RuleSet:{rs}>')
            group_index = group_index + 1
            block_index = 0
            for block in group['blocks']:
                logger.debug(
                    f'     {block_index}) Creating new condition for <RuleSet:{rs}>')

                # Create the proper condition
                tested = get_object_or_404(Question, pk=block['question'])
                operand = block['operand'] if 'operand' in block else None
                logger.debug(
                    f'         Tested <Question:{tested}> operand = {operand}')
                if tested.condition_type == Condition.BOOLEAN:
                    boolean = True if block['pattern'] == 'True' else False
                    condition = BooleanCondition.objects.create(
                        ruleset=rs,
                        index=block_index,
                        tested=tested,
                        match=block['match'],
                        boolean=boolean,
                        operand=operand,
                    )
                    logger.debug(f'         <BooleanCondition:{condition}>')
                elif tested.condition_type == Condition.CHOICE:
                    choice = get_object_or_404(Choice, pk=block['pattern'])
                    condition = ChoiceCondition.objects.create(
                        ruleset=rs,
                        index=block_index,
                        tested=tested,
                        match=block['match'],
                        choice=choice,
                        operand=operand,
                    )
                    logger.debug(f'         <ChoiceCondition:{condition}>')
                elif tested.condition_type == Condition.NUMBER:
                    condition = NumberCondition.objects.create(
                        ruleset=rs,
                        index=block_index,
                        tested=tested,
                        match=block['match'],
                        pattern=block['pattern'],
                        operand=operand
                    )
                    logger.debug(f'         <NumberCondition:{condition}>')
                elif tested.condition_type == Condition.TEXT:
                    condition = TextCondition.objects.create(
                        ruleset=rs,
                        index=block_index,
                        tested=tested,
                        match=block['match'],
                        pattern=block['pattern'],
                        operand=operand,
                    )
                    logger.debug(f'         <TextCondition:{condition}>')
                elif tested.condition_type == Condition.DATE:
                    condition = DateCondition.objects.create(
                        ruleset=rs,
                        index=block_index,
                        tested=tested,
                        match=block['match'],
                        date=block['pattern'],
                        operand=operand,
                    )
                    logger.debug(f'         <DateCondition:{condition}>')
                block_index = block_index + 1

        question.next_question = default_to
        question.save()

        return JsonResponse({'status': 'ok'})


class UnsplashSearchView(LoginRequiredMixin, View):
    def get(self, request):
        term = request.GET.get('q')
        per_page = int(request.GET.get('per_page', 9))
        page = request.GET.get('page', None)
        client = Unsplash(settings.UNSPLASH_ACCESS_KEY)
        result = client.search(term, per_page=per_page, page=page)
        return JsonResponse(result)


class PexelsSearchView(LoginRequiredMixin, View):
    def get(self, request):
        term = request.GET.get('q')
        per_page = int(request.GET.get('per_page', 9))
        page = request.GET.get('page', None)
        client = Pexels(settings.PEXELS_API_KEY)
        result = client.search_videos(term, per_page=per_page, page=page)
        return JsonResponse(result)


class TenorSearchView(LoginRequiredMixin, View):
    def get(self, request):
        term = request.GET.get('q')
        per_page = int(request.GET.get('per_page', 9))
        client = Tenor(settings.TENOR_API_KEY)
        result = client.search(term, per_page=per_page)
        return JsonResponse(result)
