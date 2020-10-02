import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission, EmailAnswer)

User = get_user_model()

class EmailTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
    
    def test_required_email(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_email(
            'Customer Survey',
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

        # Submit empty answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Submit answer
        email = 'maurice@example.com'
        updated_email = 'andre@example.com'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': email})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, EmailAnswer))
        self.assertEqual(answer.email, email)
        # Update Answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': updated_email})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, EmailAnswer))
        self.assertEqual(answer.email, updated_email)
