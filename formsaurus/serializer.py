from formsaurus.models import Question


class Serializer:
    @classmethod
    def survey(cls, survey):
        return {
            'id': str(survey.id),
            'name': survey.name,
            'published': survey.published,
        }

    @classmethod
    def submission(cls, submission):
        return {
            'id': str(submission.id),
            'is_preview': submission.is_preview,
        }

    @classmethod
    def common_parameters(cls, parameters):
        return {
            'image_url': parameters.image_url,
            'video_url': parameters.video_url,
        }

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
            'description': question.description,
            'type': question.question_type,
            'required': question.required,
            'parameters': Serializer.parameters(question),
        }
        if question.question_type == 'MC' or question.question_type == 'PC' or question.question_type == 'DD':
            result['choices'] = []
            for choice in question.choice_set.all():
                result['choices'].append(Serializer.choice(choice))
        elif question.question_type == 'OS':
            result['choices'] = []
            start = 1 if question.parameters.start_at_one else 0
            end = start + question.parameters.number_of_steps
            for n in range(start, end):
                result['choices'].append({'choice': n})
        elif question.question_type == 'R_':
            result['choices'] = []
            end = question.parameters.number_of_steps
            for n in range(0, end):
                result['choices'].append({'choice': n})

        return result

    @classmethod
    def choice(cls, choice):
        return {
            'id': choice.id,
            'choice': choice.choice,
            'image_url': choice.image_url,
        }
