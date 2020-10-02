import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Choice, Survey, Submission, DropdownAnswer)

User = get_user_model()


class DropdownTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()

    def test_required_dropdown(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_dropdown(
            "What's your favorite flavor?",
            required=True,
            choices=['Vanilla', 'Chocolate', 'Strawberry'],
        )
        # Prepare for submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        # Send empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))
        choices = Choice.objects.filter(
            question=question,
        )
        self.assertEqual(3, len(choices))
        # Send one choice to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': choices[0].id})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, DropdownAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[0].id)
        # Changing choice
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': choices[2].id})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, DropdownAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[2].id)
        # Cannot submit multiple choices
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': [choices[2].id, choices[1].id]})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[2].id)


