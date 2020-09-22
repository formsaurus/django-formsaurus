import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum

from formsaurus.models import Survey, Question, Submission, FilledField
from formsaurus.serializer import Serializer

logger = logging.getLogger('formsaurus')


class SurveyView(View):
    """This is the entry to a survey."""
    question_url = 'formsaurus:question'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if not survey.published:
            if not request.user.is_authenticated or survey.user != request.user:
                raise Http404

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
        return redirect(self.question_url, survey.id, question.id, submission.id)


class QuestionView(View):
    """This is used to handle a particular question."""
    question_url = 'formsaurus:question'
    completed_url = 'formsaurus:completed'
    template_name = 'formsaurus/question.html'

    def get(self, request, survey_id, question_id, submission_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        if not survey.published:
            if not request.user.is_authenticated or survey.user != request.user:
                raise Http404

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
        context['site_url'] = reverse(
            self.site_url) if self.site_url is not None else None
        context['register_url'] = reverse(
            self.register_url) if self.register_url is not None else None
        return render(request, self.template_name, context=context)
