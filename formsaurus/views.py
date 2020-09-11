import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum

from formsaurus.models import Survey, Question, Submission
from formsaurus.serializer import Serializer
from formsaurus.forms import *

logger = logging.getLogger('formsaurus')


class SurveyView(View):
    """This is the entry to a survey."""
    question_url = 'formsaurus:question'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if not survey.published:
            raise Http404

        question = survey.first_question
        submission = Submission.objects.create(
            survey=survey,
        )
        return redirect(self.question_url, survey.id, question.id, submission.id)


class QuestionView(View):
    """This is used to handle a particular question."""
    question_url = 'formsaurus:question'
    completed_url = 'formsaurus:completed'
    template_name = 'formsaurus/question.html'

    def get(self, request, survey_id, question_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404
        submission = get_object_or_404(Submission, pk=submission_id)
        if submission.survey != survey:
            raise Http404
        context = {}
        context['survey'] = Serializer.survey(survey)
        context['question'] = Serializer.question(question)
        context['submission'] = Serializer.submission(
            submission) if submission is not None else None
        return render(request, self.template_name, context=context)

    def post(self, request, survey_id, question_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)

        question = get_object_or_404(Question, pk=question_id)
        if question.survey != survey:
            raise Http404

        submission = get_object_or_404(Submission, pk=submission_id)
        if submission.survey != survey:
            raise Http404

        answer = submission.record_answer(
            question, request.POST, request.FILES)
        if answer is None:
            logger.debug("No answer recorded")
        else:
            logger.debug(f"Recorded answer {answer.id}")

        next_question = question.next(submission)
        logger.debug(f"Evaluated next to be {next_question}")

        # Find Next Question
        if next_question is None:
            submission.complete()
            request.session['submission'] = None
            return redirect(self.completed_url, survey.id, submission.id)
        else:
            if next_question.question_type == Question.THANK_YOU_SCREEN:
                submission.complete()
                request.session['submission'] = None

            print(f"{question.id} -> {next_question.id}")
            return redirect(self.question_url, survey.id, next_question.id, submission.id)


class CompletedView(View):
    """Shown when a survey has been completed."""
    template_name = 'formsaurus/completed.html'
    site_url = None
    register_url = None

    def get(self, request, survey_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        submission = get_object_or_404(Submission, pk=submission_id)
        context = {}
        context['survey'] = Serializer.survey(survey)
        context['submission'] = Serializer.submission(submission)
        context['site_url'] = reverse(self.site_url) if self.site_url is not None else None
        context['register_url'] = reverse(self.register_url) if self.register_url is not None else None
        return render(request, self.template_name, context=context)


class ManageView(LoginRequiredMixin, View):
    success_url = 'formsaurus:surveys'

    def get(self, request):
        return redirect(self.success_url)


class SurveysView(LoginRequiredMixin, View):
    """List all forms own by authorized user."""
    template_name = 'formsaurus/manage/surveys.html'

    def get(self, request):
        context = {}
        context['surveys'] = Survey.objects.filter(user=request.user)
        return render(request, self.template_name, context)


class SurveyWizardView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_wizard.html'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        context = {}
        context['survey'] = survey
        if survey.published:
            # Stats about submissions
            context['submissions'] = {}
            row = Submission.objects.filter(survey=survey).aggregate(
                count=Count('id'), sum=Sum('completed'))
            completed = 1 if row['sum'] is True else 0 if row['sum'] is None else row['sum']
            context['submissions']['count'] = row['count']
            context['submissions']['completed'] = completed
            context['submissions']['ratio'] = completed / row['count'] * 100 if row['count'] > 0 else 0

            pass
        return render(request, self.template_name, context)


class AddQuestionView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add_question.html'
    add_question_url = 'formsaurus:survey_add_question'

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
        context['survey'] = survey
        context['types'] = {}
        for key, value in Question.TYPES:
            if key == Question.PAYMENT or key == Question.FILE_UPLOAD:
                continue
            if has_ws and key == Question.WELCOME_SCREEN:
                continue
            context['types'][key] = value
            if key == question_type:
                context['type_name'] = value
        context['type'] = question_type

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
                    )
                    logger.info('Created Statement %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate statement parameters %s', parameters_form.errors)
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
                        other_option=parameters_form.cleaned_data['other_option'],
                        show_labels=parameters_form.cleaned_data['show_labels'],
                        supersize=parameters_form.cleaned_data['supersize'],
                        choices=choices,
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
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
                        left_label=parameters_form.cleaned_data['left_label'],
                        center_label=parameters_form.cleaned_data['center_label'],
                        right_label=parameters_form.cleaned_data['right_label'],
                        image_url=parameters_form.cleaned_data['image_url'],
                        video_url=parameters_form.cleaned_data['video_url'],
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
                    )
                    logger.info('Created Email %s', question.id)
                    return redirect(self.add_question_url, survey.id)
                else:
                    logger.warning(
                        'Failed to validate email parameters %s', parameters_form.errors)
            elif question_type == Question.FILE_UPLOAD:
                raise Http404
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


class SurveyAddView(LoginRequiredMixin, FormView):
    template_name = 'formsaurus/manage/survey_add.html'
    success_url = 'formsaurus:survey_wizard'

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


class PublishSurveyView(LoginRequiredMixin, View):
    success_url = 'formsaurus:survey_wizard'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        survey.published = True
        survey.published_at = timezone.now()
        survey.save()
        return redirect(self.success_url, survey.id)


class DeleteSurveyView(LoginRequiredMixin, View):
    success_url = 'formsaurus:surveys'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if survey.user != request.user:
            raise Http404
        if not survey.published:
            survey.delete()
        return redirect(self.success_url)


class HiddenFieldView(LoginRequiredMixin, View):
    template_name = 'formsaurus/manage/survey_add_hidden_field.html'
    success_url = 'formsaurus:survey_wizard'

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
