import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission)

User = get_user_model()

class WelcomeScreenTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
    
    def test_welcome_screen(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_welcome_screen(
            'Customer Survey',
            description='This is a survey',
            button_label="Let's Go",
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

        # Submit answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 302)

        # Do not record answers for Welcome Screen
        answers = submission.answers()
        self.assertEqual(0, len(answers))


