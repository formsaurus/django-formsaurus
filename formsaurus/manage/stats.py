from django.db.models import Count, Sum, Case, When, Value, IntegerField
from formsaurus.models import (Question, MultipleChoiceAnswer, PictureChoiceAnswer, OpinionScaleAnswer, YesNoAnswer, LegalAnswer, RatingAnswer, DropdownAnswer)

class Stats:
    @classmethod
    def answers(cls, survey):
        stats = {}
        for question in survey.questions:
            if question.question_type == Question.MULTIPLE_CHOICE:
                answers = MultipleChoiceAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('choices').annotate(count=Count('choices')).values('choices', 'count')

                stats_map = {}
                for row in answers:
                    stats_map[row['choices']] = row['count']

                rows = {}
                for choice in question.choice_set.all():
                    rows[choice.choice] = stats_map[choice.id] if choice.id in stats_map else 0
                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.PHONE_NUMBER:
                pass
            elif question.question_type == Question.SHORT_TEXT:
                pass
            elif question.question_type == Question.LONG_TEXT:
                pass
            elif question.question_type == Question.PICTURE_CHOICE:
                answers = PictureChoiceAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('choices').annotate(count=Count('choices')).values('choices', 'count')

                stats_map = {}
                for row in answers:
                    stats_map[row['choices']] = row['count']

                rows = {}
                for choice in question.choice_set.all():
                    rows[choice.choice] = stats_map[choice.id] if choice.id in stats_map else 0
                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.YES_NO:
                answers = YesNoAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('yes').annotate(count=Count('yes')).values('yes', 'count')
                stats_map = {}
                for row in answers:
                    stats_map[row['yes']] = row['count']
                rows = {}
                rows['Yes'] = stats_map[True] if True in stats_map else 0
                rows['No'] = stats_map[False] if False in stats_map else 0

                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.EMAIL:
                pass
            elif question.question_type == Question.OPINION_SCALE:
                answers = OpinionScaleAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('opinion').annotate(count=Count('opinion')).values('opinion', 'count')
                stats_map = {}
                for row in answers:
                    stats_map[row['opinion']] = row['count']
                parameters = question.parameters
                start = 1 if parameters.start_at_one else 0
                end = start + parameters.number_of_steps

                rows = {}
                for index in range(start, end):
                    rows[index] = stats_map[index] if index in stats_map else 0

                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.RATING:
                answers = RatingAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('rating').annotate(count=Count('rating')).values('rating', 'count')
                stats_map = {}
                for row in answers:
                    stats_map[row['rating']] = row['count']
                parameters = question.parameters
                end = parameters.number_of_steps

                rows = {}
                for index in range(0, end):
                    rows[index] = stats_map[index] if index in stats_map else 0

                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.DATE:
                pass
            elif question.question_type == Question.NUMBER:
                pass
            elif question.question_type == Question.DROPDOWN:
                answers = DropdownAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('choices').annotate(count=Count('choices')).values('choices', 'count')
                stats_map = {}
                for row in answers:
                    stats_map[row['choices']] = row['count']

                rows = {}
                for choice in question.choice_set.all():
                    rows[choice.choice] = stats_map[choice.id] if choice.id in stats_map else 0

                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.LEGAL:
                answers = LegalAnswer.objects.filter(
                    question=question,
                    submission__survey=survey,
                    submission__completed=True,
                    submission__is_preview=False,
                ).values('accept').annotate(count=Count('accept')).values('accept', 'count')
                stats_map = {}
                for row in answers:
                    stats_map[row['accept']] = row['count']
                rows = {}
                rows['Accept'] = stats_map[True] if True in stats_map else 0
                rows['Does Not Accept'] = stats_map[False] if False in stats_map else 0

                stats[str(question.id)] = {
                    'question': question.question,
                    'stats': rows,
                }
            elif question.question_type == Question.FILE_UPLOAD:
                pass

        return stats

