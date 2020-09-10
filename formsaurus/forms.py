from django import forms
from formsaurus.models import (Question, Survey, WelcomeParameters, ThankYouParameters,
                               MultipleChoiceParameters, PhoneNumberParameters, ShortTextParameters, LongTextParameters, StatementParameters)


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['name']


class AddQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question', 'description', 'question_type', 'required']


class WelcomeParametersForm(forms.ModelForm):
    class Meta:
        model = WelcomeParameters
        fields = ['button_label', 'image_url', 'video_url']


class ThankYouParametersForm(forms.ModelForm):
    class Meta:
        model = ThankYouParameters
        fields = ['show_button', 'button_label', 'button_link',
                  'show_social_media', 'image_url', 'video_url']


class MultipleChoiceParametersForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceParameters
        fields = ['multiple_selection', 'randomize',
                  'other_option', 'image_url', 'video_url']


class PhoneNumberParametersForm(forms.ModelForm):
    class Meta:
        model = PhoneNumberParameters
        fields = ['default_country_code', 'image_url', 'video_url']


class ShortTextParametersForm(forms.ModelForm):
    class Meta:
        model = ShortTextParameters
        fields = ['limit_character', 'limit', 'image_url', 'video_url']


class LongTextParametersForm(forms.ModelForm):
    class Meta:
        model = LongTextParameters
        fields = ['limit_character', 'limit', 'image_url', 'video_url']

class StatementParametersForm(forms.ModelForm):
    class Meta:
        model = StatementParameters
        fields = ['button_label', 'show_quotation_mark', 'image_url', 'video_url']
