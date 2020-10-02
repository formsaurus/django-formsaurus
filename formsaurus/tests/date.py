import datetime
from dateutil import parser
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission, DateAnswer)

User = get_user_model()

class DateTestCase(TestCase):
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
        survey.add_date(
            'Birthday?',
            required=True,
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
        date = '2020/09/01'
        updated_date = '2020/12/25'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': date})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, DateAnswer))
        self.assertEqual(answer.date, parser.parse(date).date())
        # Update answeer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': updated_date})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, DateAnswer))
        self.assertEqual(answer.date, parser.parse(updated_date).date())

        # Invalid input
        invalid = 'invalid'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': invalid})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, DateAnswer))
        self.assertEqual(answer.date, parser.parse(updated_date).date())

