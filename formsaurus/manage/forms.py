from django import forms
from formsaurus.models import (Question, Survey, WelcomeParameters, ThankYouParameters,
                               MultipleChoiceParameters, PhoneNumberParameters, ShortTextParameters, LongTextParameters, StatementParameters,
                               PictureChoiceParameters, YesNoParameters, EmailParameters, OpinionScaleParameters, RatingParameters, DateParameters,
                               NumberParameters, DropdownParameters, LegalParameters, FileUploadParameters, PaymentParameters, WebsiteParameters, HiddenField)


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['name']


class HiddenFieldForm(forms.ModelForm):
    class Meta:
        model = HiddenField
        fields = ['name']


class AddQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question', 'description', 'question_type', 'required']


class WelcomeParametersForm(forms.ModelForm):
    class Meta:
        model = WelcomeParameters
        fields = ['button_label', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class ThankYouParametersForm(forms.ModelForm):
    class Meta:
        model = ThankYouParameters
        fields = ['show_button', 'button_label', 'button_link',
                  'show_social_media', 'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class MultipleChoiceParametersForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceParameters
        fields = ['multiple_selection', 'randomize',
                  'other_option', 'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class PhoneNumberParametersForm(forms.ModelForm):
    class Meta:
        model = PhoneNumberParameters
        fields = ['default_country_code', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class ShortTextParametersForm(forms.ModelForm):
    class Meta:
        model = ShortTextParameters
        fields = ['limit_character', 'limit', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class LongTextParametersForm(forms.ModelForm):
    class Meta:
        model = LongTextParameters
        fields = ['limit_character', 'limit', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class StatementParametersForm(forms.ModelForm):
    class Meta:
        model = StatementParameters
        fields = ['button_label', 'show_quotation_mark',
                  'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class PictureChoiceParametersForm(forms.ModelForm):
    class Meta:
        model = PictureChoiceParameters
        fields = ['multiple_selection', 'randomize', 'other_option', 'show_labels', 'supersize',
                  'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class YesNoParametersForm(forms.ModelForm):
    class Meta:
        model = YesNoParameters
        fields = ['image_url', 'video_url', 'orientation',
                  'position_x', 'position_y', 'opacity']


class EmailParametersForm(forms.ModelForm):
    class Meta:
        model = EmailParameters
        fields = ['image_url', 'video_url', 'orientation',
                  'position_x', 'position_y', 'opacity']


class OpinionScaleParametersForm(forms.ModelForm):
    class Meta:
        model = OpinionScaleParameters
        fields = ['start_at_one', 'number_of_steps', 'show_labels',
                  'left_label', 'center_label', 'right_label', 'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class RatingParametersForm(forms.ModelForm):
    class Meta:
        model = RatingParameters
        fields = ['number_of_steps', 'shape', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class DateParametersForm(forms.ModelForm):
    class Meta:
        model = DateParameters
        fields = ['date_format', 'date_separator', 'image_url',
                  'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class NumberParametersForm(forms.ModelForm):
    class Meta:
        model = NumberParameters
        fields = ['enable_min', 'min_value', 'enable_max',
                  'max_value', 'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class DropdownParametersForm(forms.ModelForm):
    class Meta:
        model = DropdownParameters
        fields = ['randomize', 'alphabetical', 'image_url', 'video_url',
                  'orientation', 'position_x', 'position_y', 'opacity']


class LegalParametersForm(forms.ModelForm):
    class Meta:
        model = LegalParameters
        fields = ['image_url', 'video_url', 'orientation',
                  'position_x', 'position_y', 'opacity']


class FileUploadParametersForm(forms.ModelForm):
    class Meta:
        model = FileUploadParameters
        fields = ['image_url', 'video_url', 'orientation',
                  'position_x', 'position_y', 'opacity']


class PaymentParametersForm(forms.ModelForm):
    class Meta:
        model = PaymentParameters
        fields = ['currency', 'price', 'stripe_token',
                  'button_label', 'image_url', 'video_url', 'orientation', 'position_x', 'position_y', 'opacity']


class WebsiteParametersForm(forms.ModelForm):
    class Meta:
        model = WebsiteParameters
        fields = ['image_url', 'video_url', 'orientation',
                  'position_x', 'position_y', 'opacity']
