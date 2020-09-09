from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from formsaurus.models import Survey, Question, Submission
from formsaurus.serializer import Serializer


def index(request):
    return render(request, 'index.html')


def survey(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    question = survey.first_question
    context = {}
    context['survey'] = Serializer.survey(survey)
    context['question'] = Serializer.question(question)
    return render(request, 'survey.html', context=context)

def question(request, survey_id, question_id, submission_id=None):
    survey = get_object_or_404(Survey, pk=survey_id)
    question = get_object_or_404(Question, pk=question_id)
    if question.survey != survey:
        raise Http404
    

    submission = None
    if submission_id is not None or submission_id == '':
        submission = get_object_or_404(Submission, pk=submission_id)

    if request.method == 'POST':     
        if submission is None:
            submission = Submission.objects.create(
                survey=survey,
            )
            print(f"Created new submission {submission.id}")
        
        answer = submission.record_answer(question, request.POST, request.FILES)
        if answer is None:
            print("No answer recorded")
        else:
            print(f"Recorded answer {answer.id}")

        next_question = question.next(submission)
        print(f"Evaluated next to be {next_question}")

        # Find Next Question
        if next_question is None:
            submission.complete()
            request.session['submission'] = None
            return redirect('formsaurus:completed', survey.id, submission.id)
        else:
            if next_question.question_type == Question.THANK_YOU_SCREEN:
                submission.complete()
                request.session['submission'] = None

            print(f"{question.id} -> {next_question.id}")            
            return redirect('formsaurus:question', survey.id, next_question.id, submission.id)

    context = {}
    context['survey'] = Serializer.survey(survey)
    context['question'] = Serializer.question(question)
    context['submission'] = Serializer.submission(submission) if submission is not None else None
    return render(request, 'survey.html', context=context)

def completed(request, survey_id, submission_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    context = {}
    context['survey'] = Serializer.survey(survey)
    context['submission'] = Serializer.submission(submission)
    return render(request, 'completed.html', context=context)