""" Define helper template tags """
import os

from django import template
from django.utils.safestring import mark_safe

from urllib.parse import urlparse
from formsaurus.models import Question

register = template.Library()


@register.filter
def question_type_name(question_type):
    """Returns name for a given type"""
    return Question.type_name(question_type)


@register.filter
def embed(video_url):
    # TODO pass dimensions as parameters
    uri = urlparse(video_url)
    if uri.netloc.endswith('youtube.com'):
        parts = uri.query.split('&')
        for part in parts:
            if part.startswith('v='):
                video_id = part[2:]
        return mark_safe(f'<iframe width="1000" height="558" src="https://{uri.netloc}/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>')
    elif uri.netloc.endswith('vimeo.com'):
        return mark_safe(f'<iframe width="1000" height="558" src="{video_url}&autoplay=1" frameborder="0"></iframe>')
    return ""

@register.filter
def filename(path):
    return os.path.basename(path)