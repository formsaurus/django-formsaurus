import datetime
import os

from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Survey, Submission, FileUploadAnswer)

User = get_user_model()


class FileUploadTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()

    def test_required_file_upload(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_file_upload(
            'Photo?',
            required=True,
        )

        # Get submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        response = self.client.get(reverse('formsaurus:question', args=[
                                   survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)

        # Empty
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))

        # Send File
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(BASE_DIR, 'tests/yes_no.py')) as fp:
            response = self.client.post(reverse('formsaurus:question', args=[
                                        survey.id, question.id, submission.id]), {'file': fp})
            self.assertEqual(response.status_code, 302)
            answers = submission.answers()
            self.assertEqual(1, len(answers))
            answer = answers[0]
            self.assertTrue(isinstance(answer, FileUploadAnswer))
            self.assertIsNotNone(answer.file)
            self.assertEqual(answer.file, f'files/survey/{survey.id}/{submission.id}/yes_no.py')

