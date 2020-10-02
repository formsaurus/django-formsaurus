import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Survey, Submission, LegalAnswer)

User = get_user_model()


class LegalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()

    def test_not_required_yes_no(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_legal(
            'Do you accept?',
            required=False,
        )

        # Create a submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)

        question = survey.first_question
        self.assertIsNotNone(question)

        # Send empty answer to non required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))

        # Update answer to Yes
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'accept'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, LegalAnswer))
        self.assertTrue(answer.accept)

        # Update answer to No
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'no_accept'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        # We need to make sure we don't record multiple answers!
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, LegalAnswer))
        self.assertFalse(answer.accept)

    def test_required_yes_no(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_legal(
            'Do you accept?',
            required=True,
        )

        # Redirects to a submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)

        question = survey.first_question
        self.assertIsNotNone(question)

        # Get question
        response = self.client.get(reverse('formsaurus:question', args=[
                                   survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)

        # Send empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Send invalid answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'Soccer'})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Send answer Yes
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'accept'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, LegalAnswer))
        self.assertTrue(answer.accept)

        # Send answer No
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'no_accept'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        # We need to make sure we don't record multiple answers!
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, LegalAnswer))
        self.assertFalse(answer.accept)
