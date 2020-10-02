import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission, PhoneNumberAnswer)

User = get_user_model()

class PhoneNumberTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
    
    def test_required_phone_number(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_phone_number(
            'Phone Number?',
            required=True,
            default_country_code=33,
        )
      
        # Redirects to a submission
        response = self.client.get(reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        response = self.client.get(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)

        # Submit empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Submit answer to required question
        first_number = '3384345677'
        second_number = '3384345699'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': first_number})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PhoneNumberAnswer))
        self.assertEqual(answer.phone_number, first_number)
        # Update answeer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': second_number})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PhoneNumberAnswer))
        self.assertEqual(answer.phone_number, second_number)


    def test_optional_phone_number(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_phone_number(
            'Phone Number?',
            required=False,
            default_country_code=33,
        )
      
        # Redirects to a submission
        response = self.client.get(reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        response = self.client.get(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)

        # Submit empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))

        # Submit answer to required question
        first_number = '3384345677'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': first_number})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PhoneNumberAnswer))
        self.assertEqual(answer.phone_number, first_number)
