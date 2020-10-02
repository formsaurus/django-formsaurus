import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (Survey, Submission, WebsiteAnswer)

User = get_user_model()

class WebsiteTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
    
    def test_required_url(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_website(
            'Website',
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

        # Submit invalid answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': 'not_a_url'})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Submit answer
        url = 'http://example.com'
        updated_url = 'http://formsaurus.com'
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': url})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, WebsiteAnswer))
        self.assertEqual(answer.url, url)
        # Update Answer
        response = self.client.post(reverse('formsaurus:question', args=[survey.id, question.id, submission.id]), {'answer': updated_url})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, WebsiteAnswer))
        self.assertEqual(answer.url, updated_url)


