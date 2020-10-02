import datetime
from django.test import Client, TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from formsaurus.models import (
    Choice, Survey, Submission, PictureChoiceAnswer)

User = get_user_model()



class PictureChoiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.client = Client()
        self.choices=[
                {
                    'label': 'Cat',
                    'image_url': 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1283&q=80',
                },
                {
                    'label': 'Dog',
                    'image_url': 'https://images.unsplash.com/photo-1565726166189-e9814a05ffde?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
                },
            ]

    def test_required_single_picture_choice(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_picture_choice(
            "What's your favorite flavor?",
            required=True,
            choices=self.choices,
        )
        # Prepare for submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        # Send empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))
        choices = Choice.objects.filter(
            question=question,
        )
        self.assertEqual(2, len(choices))
        # Send one choice to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': choices[0].id})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[0].id)
        # Changing choice
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': choices[1].id})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[1].id)
        # Cannot submit multiple choices
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': [choices[0].id, choices[1].id]})
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[1].id)


    def test_required_multiple_picture_choice(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_picture_choice(
            "What's your favorite flavor?",
            required=True,
            multiple_selection=True,
            choices=self.choices,
        )
        # Prepare for submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)
        # Send empty answer to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]))
        self.assertEqual(response.status_code, 200)
        answers = submission.answers()
        self.assertEqual(0, len(answers))
        choices = Choice.objects.filter(
            question=question,
        )
        self.assertEqual(2, len(choices))
        # Send one choice to required question
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': choices[0].id})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[0].id)
        # Update to multiple choices
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': [choices[0].id, choices[1].id]})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(2, len(answer.choices.all()))
        first = answer.choices.all()[0]
        second = answer.choices.all()[1]
        if first.id == choices[1].id:
            self.assertEqual(second.id, choices[0].id)
        else:
            self.assertEqual(second.id, choices[1].id)


    def test_required_other_picture_choice(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_picture_choice(
            "What's your favorite flavor?",
            required=True,
            multiple_selection=False,
            other_option=True,
            choices=self.choices,
        )
        # Prepare for submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)

        # Send Other
        another = 'Other Choice'
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': another})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(0, len(answer.choices.all()))
        self.assertEqual(answer.other, another)


    def test_required_other_multiple_picture_choice(self):
        survey = Survey.objects.create(
            name='Test Survey',
            user=self.user,
            published=True,
        )
        survey.add_picture_choice(
            "What's your favorite flavor?",
            required=True,
            multiple_selection=True,
            other_option=True,
            choices=self.choices,
        )
        # Prepare for submission
        response = self.client.get(
            reverse('formsaurus:survey', args=[survey.id]))
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(survey=survey)
        self.assertIsNotNone(submission)
        question = survey.first_question
        self.assertIsNotNone(question)

        choices = Choice.objects.filter(
            question=question,
        )
        self.assertEqual(2, len(choices))

        # Send Other + Choice
        another = 'Other Choice'
        response = self.client.post(reverse('formsaurus:question', args=[
                                    survey.id, question.id, submission.id]), {'answer': [another, choices[0].id]})
        self.assertEqual(response.status_code, 302)
        answers = submission.answers()
        self.assertEqual(1, len(answers))
        answer = answers[0]
        self.assertTrue(isinstance(answer, PictureChoiceAnswer))
        self.assertEqual(1, len(answer.choices.all()))
        self.assertEqual(answer.other, another)
        picked = answer.choices.first()
        self.assertEqual(picked.id, choices[0].id)
