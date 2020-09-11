""" Define helper template tags """
from django import template
from formsaurus.models import Question

register = template.Library()

@register.filter
def question_type_name(question_type):
    """Returns name for a given type"""
    return Question.type_name(question_type)
