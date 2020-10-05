
import secrets

from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from formsaurus.models import (Survey, HiddenField, Question, RuleSet, BooleanCondition, RatingParameters, DateParameters, QuestionParameter)

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate a sample Survey'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=str)
        parser.add_argument('--title', type=str)
        parser.add_argument('--published', action='store_true')

    def handle(self, *args, **options):
        if 'user_id' in options and options['user_id'] is not None:
            user = User.objects.get(pk=options['user_id'])        
        else:
            user = User.objects.get(pk=1)
        
        survey_name = options['title'] if 'title' in options and options['title'] is not None and options['title'] != "" else 'Sample Survey'
        survey = Survey.objects.create(
            name=survey_name,
            user=user,
            published=options['published'],
        )
        survey.add_hidden_field('email')

        # self.add_logic(survey)
        # self.add_simple(survey)
        # self.add_multiple_choice(survey)
        # self.add_one_of_each(survey)
        # self.add_one_of_each(survey, orientation=QuestionParameter.FLOAT)
        # self.add_one_of_each(survey, orientation=QuestionParameter.SPLIT)
        self.add_one_of_each(survey, orientation=QuestionParameter.BACKGROUND, opacity=20)
        # self.add_upload(survey)
        # self.add_multiple_choices(survey)
        # self.add_multiple_choices_with_others(survey)

        print(f"Created survey {survey.id}")
        for question in survey.question_set.all():
            print(f"{question.question_type} {question.question} {question.parameters}")
        print(f"http://localhost:8003/form/{survey.id}")

    def add_upload(self, survey):
        q1 = survey.add_file_upload('Upload submission', required=True)

    def add_simple(self, survey):
        q1 = survey.add_yes_no('Do you struggle with budgeting?', required=True)
        q2 = survey.add_opinion_scale('How much do you struggle?', required=True)
        q3 = survey.add_thank_you_screen('Thank you!')


    def add_multiple_choices(self, survey):
        _ = survey.add_multiple_choice('Randomize, Not Required, Single Selection', randomize=True, required=False, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Required, Single Selection', required=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Not Required, Multiple Selection', required=False, multiple_selection=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Required, Multiple Selection', required=True, multiple_selection=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])

    def add_multiple_choices_with_others(self, survey):
        _ = survey.add_multiple_choice('Other, Not Required, Single Selection', other_option=True, required=False, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Other, Required, Single Selection', other_option=True, required=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Other, Not Required, Multiple Selection', other_option=True, required=False, multiple_selection=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])
        _ = survey.add_multiple_choice('Other, Required, Multiple Selection', other_option=True, required=True, multiple_selection=True, choices=['Vanilla', 'Chocolate', 'Strawberry'])


    def add_multiple_choice(self, survey):
        q1 = survey.add_multiple_choice('Flavor?', choices=['Vanilla', 'Chocolate', 'Strawberry'])

    def add_logic(self, survey):
        q1 = survey.add_yes_no('Do you struggle with budgeting?', required=True)
        q2 = survey.add_opinion_scale('How much do you struggle?', required=True)
        q3 = survey.add_thank_you_screen('Thank you!')

        r1 = RuleSet.objects.create(
            question = q1,
            jump_to = q3,
            index = 0,
        )
        print(f"RuleSet {r1.id}")
          
        condition = BooleanCondition.objects.create(
            ruleset=r1,
            index=0,
            tested=q1,
            match=BooleanCondition.IS,
            boolean=False,
        )
        print(f"Condition {condition.id}")

    def add_one_of_each(self, survey, orientation=QuestionParameter.STACK, opacity=None):
        # question, description=None, button_label='Start', image_url=None, video_url=None
        survey.add_welcome_screen(
            'Customer Survey',
            description='This is a survey',
            button_label="Let's Go",
            image_url='https://images.unsplash.com/photo-1495443942462-81f29560f7e0?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1352&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question,required=True,description=None,multiple_selection=False,randomize=False,other_option=False,choices=[],vertical_alignment=False,image_url=None,video_url=None):
        survey.add_multiple_choice(
            'Eye Color',
            description="T'as beaux yeux.",
            required=True,
            multiple_selection=True,
            other_option=True,
            choices=['Blue', 'Brown', 'Green'],
            image_url='https://images.unsplash.com/photo-1533073526757-2c8ca1df9f1c?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=True, description=None, default_country_code=1,image_url=None,video_url=None):
        survey.add_phone_number(
            'Phone Number',
            description="What's Up Doc?",
            required=True,
            default_country_code=33,
            image_url='https://images.unsplash.com/photo-1520923642038-b4259acecbd7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1306&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None):
        survey.add_short_text(
            'Catch Phrase',
            description='Something Funny',
            required=True,
            limit_character=True,
            limit=32,
            image_url='https://images.unsplash.com/photo-1531502884512-547607eec96f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=True, description=None, limit_character=False, limit=None, image_url=None, video_url=None):
        survey.add_long_text(
            'Bio',
            description='Tell me about yourself',
            required=True,
            limit_character=True,
            limit=1024,
            image_url='https://images.unsplash.com/photo-1544531585-f14f463149ec?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )
        #question, description=None, button_label='Next', show_quotation_mark=True, image_url=None, video_url=None):
        survey.add_statement(
            '1 + 1 = 2',
            description='Or is that not the case?',
            button_label='Yay Math!',
            show_quotation_mark=True,
            image_url='https://images.unsplash.com/photo-1542621334-a254cf47733d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        #    def add_picture_choice(self, question, required=False, description=None, multiple_selection=False, randomize=False, other_option=False, choices=[], show_labels=False, supersize=False, image_url=None, video_url=None):
        survey.add_picture_choice(
            'Cutest?',
            required=True,
            description='Do I really have to choose?',
            multiple_selection=True,
            other_option=True,
            choices=[
                {
                    'label': 'Cat',
                    'image_url': 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1283&q=80',
                },
                {
                    'label': 'Dog',
                    'image_url': 'https://images.unsplash.com/photo-1565726166189-e9814a05ffde?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
                },
            ],
            show_labels=True,
            supersize=True,
            image_url='https://images.unsplash.com/photo-1468849169681-0b89c0d8aeab?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=984&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, image_url=None, video_url=None):
        survey.add_yes_no(
            'Are you right handed?',
            description="It's for science",
            required=True,
            image_url='https://images.unsplash.com/photo-1516382022989-cd771ab91fb1?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1267&q=80',
            orientation=orientation,
            opacity=opacity,
        )
        # question, required=False, description=None, image_url=None, video_url=None):
        survey.add_email(
            'Email',
            required=True,
            description='We promise not to spam',
            image_url='https://images.unsplash.com/photo-1528747045269-390fe33c19f2?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, start_at_one=True, number_of_steps=11, show_labels=False, left_label=None, center_label=None, right_label=None, image_url=None, video_url=None):
        survey.add_opinion_scale(
            'Opinion?',
            description='We want to know',
            required=True,
            start_at_one=True,
            number_of_steps=10,
            show_labels=True,
            left_label='Left',
            center_label='Center',
            right_label='Right',
            image_url='https://images.unsplash.com/photo-1522148543752-8cdaa654a796?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1351&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        #question, required=False, description=None, number_of_steps=5, shape='S', image_url=None, video_url=None):
        survey.add_rating(
            'Rating',
            required=True,
            description='How was it?',
            number_of_steps=6,
            shape=RatingParameters.STAR,
            image_url='https://images.unsplash.com/photo-1521967906867-14ec9d64bee8?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, date_format='A', date_separator='/', image_url=None, video_url=None):
        survey.add_date(
            'Date of Birth',
            description='So we can wish you a happy birthday',
            required=True,
            date_format=DateParameters.YYYYMMDD,
            date_separator= DateParameters.SLASH,
            image_url='https://images.unsplash.com/photo-1464347601390-25e2842a37f7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1385&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, enable_min=False, min_value=None, enable_max=False, max_value=None, image_url=None, video_url=None):
        survey.add_number(
            'Number',
            required=True,
            description='Counting on you',
            enable_min=True,
            min_value=0,
            enable_max=True,
            max_value=10,
            image_url='https://images.unsplash.com/photo-1590753684039-6adc03c5d6dc?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1188&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, randomize=False, alphabetical=False, choices=[], image_url=None, video_url=None):
        survey.add_dropdown(
            'Dropdown', 
            required=True,
            description='Choices',
            choices=['Option 1', 'Option 2'],
            image_url='https://images.unsplash.com/photo-1502298411556-0b02524812cb?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, image_url=None, video_url=None):
        survey.add_legal(
            'Do you agree?',
            required=True,
            description='Our lawyers asked us',
            image_url='https://images.unsplash.com/photo-1575505586569-646b2ca898fc?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1205&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, image_url=None, video_url=None):
        survey.add_website(
            'URL',
            required=True,
            description='So we can visit',
            image_url='https://images.unsplash.com/photo-1516383274235-5f42d6c6426d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1353&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, required=False, description=None, image_url=None, video_url=None, orientation=None, position_x=None, position_y=None, opacity=None
        survey.add_file_upload(
            'Upload Something',
            description='Show us your work',
            required=True,
            image_url='https://images.unsplash.com/photo-1589447388175-ac47d31be950?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1950&q=80',
            orientation=orientation,
            opacity=opacity,
        )

        # question, description=None, show_button=True, button_label='Done', button_link=None, show_social_media=True, image_url=None, video_url=None
        survey.add_thank_you_screen(
            'Thank You!',
            description='This was quite a journey',
            show_button=True,
            button_label='Hasta La Vista Baby!',
            button_link='https://poit.ch',
            show_social_media=True,
            image_url='https://images.unsplash.com/photo-1530242269066-86e5a3a480ba?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80',
            orientation=orientation,
            opacity=opacity,
        )

