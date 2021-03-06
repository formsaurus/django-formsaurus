import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum

from formsaurus.models import (Question, Submission, FilledField, QuestionParameter)
from formsaurus.serializer import Serializer
from formsaurus.utils import get_survey_model

logger = logging.getLogger('formsaurus')

Survey = get_survey_model()

class SurveyView(View):
    """This is the entry to a survey."""
    question_url = 'formsaurus:question'
    completed_url = 'formsaurus:completed'
    closed_url = 'formsaurus:closed'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if not survey.can_view(request.user):
            raise Http404
        if not survey.answerable:
            return redirect(self.closed_url, survey.id)

        question = survey.first_question
        submission = Submission.objects.create(
            survey=survey,
            is_preview=not survey.published,
        )
        # Store fields
        for field in survey.hiddenfield_set.all():
            value = request.GET.get(field.name)
            FilledField.objects.create(
                submission=submission,
                field=field,
                value=value,
            )
        if question is None:
            return redirect(self.completed_url, survey.id, submission.id)
        return redirect(self.question_url, survey.id, question.id, submission.id)


class QuestionView(View):
    """This is used to handle a particular question."""
    question_url = 'formsaurus:question'
    completed_url = 'formsaurus:completed'
    template_name = 'formsaurus/question.html'

    def context(self, question, survey, submission):
        context = {}
        if question.parameters.orientation is None or question.parameters.orientation == QuestionParameter.STACK:
            context['question_base'] = 'formsaurus/templates/base_stack.html'
        elif question.parameters.orientation == QuestionParameter.FLOAT:
            context['question_base'] = 'formsaurus/templates/base_float.html'
        elif question.parameters.orientation == QuestionParameter.SPLIT:
            context['question_base'] = 'formsaurus/templates/base_split.html'
        elif question.parameters.orientation == QuestionParameter.BACKGROUND:
            context['question_base'] = 'formsaurus/templates/base_background.html'
        context['survey'] = Serializer.survey(survey)
        context['question'] = Serializer.question(question)
        context['submission'] = Serializer.submission(
            submission) if submission is not None else None
        if question.question_type == Question.RATING and question.parameters.shape is not None:
            context['question_shape'] = survey.rating_shapes[question.parameters.shape]

        return context

    def get(self, request, survey_id, question_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if not survey.can_view(request.user):
            raise Http404
        if not survey.answerable:
            return redirect(self.closed_url, survey.id)

        question = get_object_or_404(Question, pk=question_id)
        if question.survey_id != survey_id:
            raise Http404
        submission = get_object_or_404(Submission, pk=submission_id)
        if submission.survey_id != survey_id:
            raise Http404
        context = self.context(question, survey, submission)
        return render(request, self.template_name, context=context)

    def post(self, request, survey_id, question_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)

        question = get_object_or_404(Question, pk=question_id)
        if question.survey_id != survey_id:
            raise Http404

        submission = get_object_or_404(Submission, pk=submission_id)
        if submission.survey_id != survey_id:
            raise Http404

        answer, error = submission.record_answer(
            question, request.POST, request.FILES)
        if answer is None:
            logger.debug("No answer recorded")
            if error is not None:
                context = self.context(question, survey, submission)
                context['error'] = True
                return render(request, self.template_name, context=context)
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
        context['site_url'] = reverse(
            self.site_url) if self.site_url is not None else None
        context['register_url'] = reverse(
            self.register_url) if self.register_url is not None else None
        return render(request, self.template_name, context=context)


class ClosedView(View):
    template_name = 'formsaurus/closed.html'
    site_url = None
    register_url = None

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        context = {}
        context['survey'] = Serializer.survey(survey)
        context['site_url'] = reverse(
            self.site_url) if self.site_url is not None else None
        context['register_url'] = reverse(
            self.register_url) if self.register_url is not None else None
        return render(request, self.template_name, context=context)
