import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Survey, Submission, YesNoAnswer)

User = get_user_model()


class YesNoTestCase(TestCase):
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
        survey.add_yes_no(
            'Are you right handed?',
            description="It's for science",
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
                                    survey.id, question.id, submission.id]), {'answer': 'Yes'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, YesNoAnswer))
        self.assertTrue(answer.yes)

        # Update answer to No
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'No'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        # We need to make sure we don't record multiple answers!
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, YesNoAnswer))
        self.assertFalse(answer.yes)

    def test_required_yes_no(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_yes_no(
            'Are you right handed?',
            description="It's for science",
            required=True,
            image_url='https://images.unsplash.com/photo-1516382022989-cd771ab91fb1?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1267&q=80',
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
                                    survey.id, question.id, submission.id]), {'answer': 'Yes'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, YesNoAnswer))
        self.assertTrue(answer.yes)

        # Send answer No
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 'No'})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        # We need to make sure we don't record multiple answers!
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, YesNoAnswer))
        self.assertFalse(answer.yes)
