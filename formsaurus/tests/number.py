import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Survey, Submission, NumberAnswer)

User = get_user_model()


class NumberTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()

    def test_required_number(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_number(
            'Pick a number?',
            required=True,
            enable_min=True,
            min_value=4,
            enable_max=True,
            max_value=10,
        )

        # Create a submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)

        # Empty
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Send number
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 7})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 7)

        # Update answer
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 8})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 8)

        # Out of range
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 0})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 8)

        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 11})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 8)


        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'ABC'})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 8)

        # UTF
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': '四'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, NumberAnswer))
        self.assertEqual(answer.number, 4)
