""" Define helper template tags """
import os

from django import template
from django.utils.safestring import mark_safe

from urllib.parse import urlparse
from formsaurus.models import Question, RatingParameters

register = template.Library()


@register.filter
def question_type_name(question_type):
    """Returns name for a given type"""
    return Question.type_name(question_type)


@register.filter
def filename(path):
    return os.path.basename(path)

@register.simple_tag
def setvar(val=None):
    return val

@register.filter
def shape_fontawesome(shape):
    if shape.shape == RatingParameters.STARS:
        return mark_safe(f'<i class="fas fa-star"></i>')
    elif shape.shape == RatingParameters.HEARTS:
        return mark_safe(f'<i class="fas fa-heart"></i>')
    elif shape.shape == RatingParameters.USERS:
        return mark_safe(f'<i class="fas fa-user"></i>')
    elif shape.shape == RatingParameters.THUMBS:
        return mark_safe(f'<i class="fas fa-thumbs-up"></i>')
    elif shape.shape == RatingParameters.CROWNS:
        return mark_safe(f'<i class="fas fa-crown"></i>')
    elif shape.shape == RatingParameters.CATS:
        return mark_safe(f'<i class="fas fa-cat"></i>')
    elif shape.shape == RatingParameters.DOGS:
        return mark_safe(f'<i class="fas fa-dog"></i>')
    elif shape.shape == RatingParameters.CIRCLES:
        return mark_safe(f'<i class="fas fa-circle"></i>')
    elif shape.shape == RatingParameters.FLAGS:
        return mark_safe(f'<i class="fas fa-flag"></i>')
    elif shape.shape == RatingParameters.DROPLETS:
        return mark_safe(f'<i class="fas fa-raindrops"></i>')
    elif shape.shape == RatingParameters.TICKS:
        return mark_safe(f'<i class="fas fa-check"></i>')
    elif shape.shape == RatingParameters.LIGHTBULBS:
        return mark_safe(f'<i class="fas fa-lightbulb"></i>')
    elif shape.shape == RatingParameters.TROPHIES:
        return mark_safe(f'<i class="fas fa-trophy"></i>')
    elif shape.shape == RatingParameters.CLOUDS:
        return mark_safe(f'<i class="fas fa-cloud"></i>')
    elif shape.shape == RatingParameters.THUNDERBOLTS:
        return mark_safe(f'<i class="fas fa-bolt"></i>')
    elif shape.shape == RatingParameters.PENCILS:
        return mark_safe(f'<i class="fas fa-pencil-alt"></i>')
    elif shape.shape == RatingParameters.SKULLS:
        return mark_safe(f'<i class="fas fa-skull"></i>')