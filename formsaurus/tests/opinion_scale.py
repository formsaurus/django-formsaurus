import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Survey, Submission, OpinionScaleAnswer)

User = get_user_model()


class OpinionScaleTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()

    def test_required_opinion_scale(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_opinion_scale(
            'How much do you like it?',
            required=True,
            start_at_one=True,
            number_of_steps=10,
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

        # Send opinion
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 5})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, OpinionScaleAnswer))
        self.assertEqual(answer.opinion, 5)

        # Update answer
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 6})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, OpinionScaleAnswer))
        self.assertEqual(answer.opinion, 6)

        # Out of range
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 0})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, OpinionScaleAnswer))
        self.assertEqual(answer.opinion, 6)

        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 11})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, OpinionScaleAnswer))
        self.assertEqual(answer.opinion, 6)

    def test_required_start_at_0_opinion_scale(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_opinion_scale(
            'How much do you like it?',
            required=True,
            start_at_one=False,
            number_of_steps=10,
        )
        # Create a submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        # Out of range
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': -1})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': 10})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))
