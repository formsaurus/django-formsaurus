import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission, ShortTextAnswer)

User = get_user_model()

class ShortTextTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
    
    def test_required_short_text(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_short_text(
            'Customer Survey',
            required=True,
            limit_character=True,
            limit=25,
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
        short_text = '0123456789'
        updated_text = '9876543210'
        too_long = '012345678901234567890123456789'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': short_text})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, ShortTextAnswer))
        self.assertEqual(answer.short_text, short_text)
        # Update Answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': updated_text})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, ShortTextAnswer))
        self.assertEqual(answer.short_text, updated_text)
        # Reject too long
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': too_long})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, ShortTextAnswer))
        self.assertEqual(answer.short_text, updated_text)


