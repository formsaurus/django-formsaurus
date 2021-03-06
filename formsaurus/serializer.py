import random

from django.conf import settings
from urllib.parse import urlparse
from formsaurus.models import (
    Question, Condition, TextCondition, NumberCondition, ChoiceCondition, BooleanCondition, DateCondition)


class ObjectDict(object):
    def __init__(self, d):
        self.__dict__ = d

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

class Serializer:
    @classmethod
    def survey(cls, survey):
        return survey.to_dict()

    @classmethod
    def submission(cls, submission):
        return {
            'id': str(submission.id),
            'is_preview': submission.is_preview,
        }

    @classmethod
    def common_parameters(cls, parameters):
        result = {}
        if parameters.image_url is not None:
            result['image_url'] = parameters.image_url
        if parameters.video_url is not None:
            result['video'] = {}
            result['video']['url'] = parameters.video_url
            result['video']['image'] = parameters.image_url
            uri = urlparse(parameters.video_url)
            if uri.netloc.endswith('youtube.com'):
                result['video']['source'] = 'youtube'
                parts = uri.query.split('&')
                for part in parts:
                    if part.startswith('v='):
                        video_id = part[2:]
                        result['video']['video_id'] = video_id
                        break

            elif uri.netloc.endswith('vimeo.com'):
                result['video']['source'] = 'vimeo'
            else:
                result['video']['source'] = 'other'
        if parameters.orientation is not None:
            result['orientation'] = parameters.orientation
            result['position_x'] = parameters.position_x if parameters.position_x is not None else 50
            result['position_y'] = parameters.position_y if parameters.position_y is not None else 50
            result['opacity'] = parameters.opacity if parameters.opacity is not None else 1.0
        return result

    @classmethod
    def ws_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['button_label'] = parameters.button_label
        return p

    @classmethod
    def ts_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['show_button'] = parameters.show_button
        p['button_label'] = parameters.button_label
        p['button_link'] = parameters.button_link
        p['show_social_media'] = parameters.show_social_media
        return p

    @classmethod
    def mc_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['multiple_selection'] = parameters.multiple_selection
        p['randomize'] = parameters.randomize
        p['other_option'] = parameters.other_option
        return p

    @classmethod
    def pn_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['default_country_code'] = parameters.default_country_code
        return p

    @classmethod
    def st_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['limit_character'] = parameters.limit_character
        p['limit'] = parameters.limit
        return p

    @classmethod
    def lt_parameters(cls, parameters):
        return Serializer.st_parameters(parameters)

    @classmethod
    def s__parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['button_label'] = parameters.button_label
        p['show_quotation_mark'] = parameters.show_quotation_mark
        return p

    @classmethod
    def pc_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['multiple_selection'] = parameters.multiple_selection
        p['randomize'] = parameters.randomize
        p['other_option'] = parameters.other_option
        p['show_labels'] = parameters.show_labels
        p['supersize'] = parameters.supersize
        return p

    @classmethod
    def yn_parameters(cls, parameters):
        return Serializer.common_parameters(parameters)

    @classmethod
    def e__parameters(cls, parameters):
        return Serializer.common_parameters(parameters)

    @classmethod
    def os_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['start_at_one'] = parameters.start_at_one
        p['number_of_steps'] = parameters.number_of_steps
        p['show_labels'] = parameters.show_labels
        p['left_label'] = parameters.left_label
        p['center_label'] = parameters.center_label
        p['right_label'] = parameters.right_label
        return p

    @classmethod
    def r__parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['number_of_steps'] = parameters.number_of_steps
        p['shape'] = parameters.shape
        return p

    @classmethod
    def d__parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['format'] = parameters.format
        return p

    @classmethod
    def n__parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['enable_min'] = parameters.enable_min
        p['min_value'] = parameters.min_value
        p['enable_max'] = parameters.enable_max
        p['max_value'] = parameters.max_value
        return p

    @classmethod
    def dd_parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['randomize'] = parameters.randomize
        p['alphabetical'] = parameters.alphabetical
        return p

    @classmethod
    def l__parameters(cls, parameters):
        return Serializer.common_parameters(parameters)

    @classmethod
    def fu_parameters(cls, parameters):
        return Serializer.common_parameters(parameters)

    @classmethod
    def p__parameters(cls, parameters):
        p = Serializer.common_parameters(parameters)
        p['currency'] = parameters.currency
        p['price'] = parameters.price
        p['stripe_token'] = parameters.stripe_token
        p['button_label'] = parameters.button_label
        return p

    @classmethod
    def w__parameters(cls, parameters):
        return Serializer.common_parameters(parameters)

    @classmethod
    def parameters(cls, question):
        if question.question_type == Question.WELCOME_SCREEN:
            return Serializer.ws_parameters(question.parameters)
        elif question.question_type == Question.THANK_YOU_SCREEN:
            return Serializer.ts_parameters(question.parameters)
        elif question.question_type == Question.MULTIPLE_CHOICE:
            return Serializer.mc_parameters(question.parameters)
        elif question.question_type == Question.PHONE_NUMBER:
            return Serializer.pn_parameters(question.parameters)
        elif question.question_type == Question.SHORT_TEXT:
            return Serializer.st_parameters(question.parameters)
        elif question.question_type == Question.LONG_TEXT:
            return Serializer.lt_parameters(question.parameters)
        elif question.question_type == Question.STATEMENT:
            return Serializer.s__parameters(question.parameters)
        elif question.question_type == Question.PICTURE_CHOICE:
            return Serializer.pc_parameters(question.parameters)
        elif question.question_type == Question.YES_NO:
            return Serializer.yn_parameters(question.parameters)
        elif question.question_type == Question.EMAIL:
            return Serializer.e__parameters(question.parameters)
        elif question.question_type == Question.OPINION_SCALE:
            return Serializer.os_parameters(question.parameters)
        elif question.question_type == Question.RATING:
            return Serializer.r__parameters(question.parameters)
        elif question.question_type == Question.DATE:
            return Serializer.d__parameters(question.parameters)
        elif question.question_type == Question.NUMBER:
            return Serializer.n__parameters(question.parameters)
        elif question.question_type == Question.DROPDOWN:
            return Serializer.dd_parameters(question.parameters)
        elif question.question_type == Question.LEGAL:
            return Serializer.l__parameters(question.parameters)
        elif question.question_type == Question.FILE_UPLOAD:
            return Serializer.fu_parameters(question.parameters)
        elif question.question_type == Question.PAYMENT:
            return Serializer.p__parameters(question.parameters)
        elif question.question_type == Question.WEBSITE:
            return Serializer.w__parameters(question.parameters)
        return {}

    @classmethod
    def question(cls, question):
        result = {
            'id': str(question.id),
            'question': question.question,
            'type': question.question_type,
            'required': question.required,
            'parameters': Serializer.parameters(question),
        }
        # if question.next_question_id is not None:
        result['next_question'] = str(question.next_question_id)
        if question.description is not None and question.description != "":
            result['description'] = question.description
        if question.question_type in [Question.MULTIPLE_CHOICE, Question.PICTURE_CHOICE, Question.DROPDOWN]:
            result['choices'] = []
            index = 0
            choices = []
            for choice in question.choice_set.order_by('position').all():
                choices.append(choice)
            if 'randomize' in result['parameters'] and result['parameters']['randomize']:
                random.shuffle(choices)
            if 'other_option' in result['parameters'] and result['parameters']['other_option']:
                choices.append(ObjectDict({
                    'id': '',
                    'choice': 'Other',
                    'position': len(choices),
                }))

            for choice in choices:
                result['choices'].append(Serializer.choice(choice, index))
                index = index + 1
        elif question.question_type == Question.OPINION_SCALE:
            result['choices'] = []
            start = 1 if question.parameters.start_at_one else 0
            end = start + question.parameters.number_of_steps
            for n in range(start, end):
                result['choices'].append({'choice': n})
        elif question.question_type == Question.RATING:
            result['choices'] = []
            end = question.parameters.number_of_steps
            for n in range(0, end):
                result['choices'].append({'choice': n})

        return result

    @classmethod
    def choice(cls, choice, index=None):
        result = {
            'id': str(choice.id),
            'choice': choice.choice,
            'image_url': choice.image_url,
            'position': choice.position,
        }
        if index is not None:
            result['keycode'] = 97+index
            result['letter'] = chr(65+index)
        return result

    @classmethod
    def ruleset(cls, ruleset):
        return {
            'id': str(ruleset.id),
            'question': Serializer.question(ruleset.question),
            'jump_to': Serializer.question(ruleset.jump_to),
            'index': ruleset.index,
        }

    @classmethod
    def condition(cls, condition):
        if isinstance(condition, TextCondition):
            return Serializer.text_condition(condition)
        elif isinstance(condition, NumberCondition):
            return Serializer.number_condition(condition)
        elif isinstance(condition, ChoiceCondition):
            return Serializer.choice_condition(condition)
        elif isinstance(condition, BooleanCondition):
            return Serializer.boolean_condition(condition)
        elif isinstance(condition, DateCondition):
            return Serializer.date_condition(condition)
        else:
            return None


    @classmethod
    def condition_type(cls, condition):
        if isinstance(condition, TextCondition):
            return Condition.TEXT
        elif isinstance(condition, NumberCondition):
            return Condition.NUMBER
        elif isinstance(condition, ChoiceCondition):
            return Condition.CHOICE
        elif isinstance(condition, BooleanCondition):
            return Condition.BOOLEAN
        elif isinstance(condition, DateCondition):
            return Condition.DATE
        else:
            return None

    @classmethod
    def base_condition(cls, condition):
        return {
            'id': str(condition.id),
            'index': condition.index,
            'tested': Serializer.question(condition.tested),
            'operand': condition.operand,
            'type': Serializer.condition_type(condition),
        }

    @classmethod
    def text_condition(cls, condition):
        hashmap = Serializer.base_condition(condition)
        hashmap['match'] = condition.match
        hashmap['pattern'] = condition.pattern
        return hashmap

    @classmethod
    def number_condition(cls, condition):
        hashmap = Serializer.base_condition(condition)
        hashmap['match'] = condition.match
        hashmap['pattern'] = condition.pattern
        return hashmap

    @classmethod
    def choice_condition(cls, condition):
        hashmap = Serializer.base_condition(condition)
        hashmap['match'] = condition.match
        hashmap['pattern'] = Serializer.choice(condition.choice)
        return hashmap

    @classmethod
    def boolean_condition(cls, condition):
        hashmap = Serializer.base_condition(condition)
        hashmap['match'] = condition.match
        hashmap['pattern'] = condition.boolean
        return hashmap

    @classmethod
    def date_condition(cls, condition):
        hashmap = Serializer.base_condition(condition)
        hashmap['match'] = condition.match
        hashmap['pattern'] = condition.date
        return hashmap


    @classmethod
    def hidden_field(cls, field):
        return {
            'id': str(field.id),
            'name': field.name,
        }