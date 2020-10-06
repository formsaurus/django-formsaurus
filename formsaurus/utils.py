from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_survey_model():
    try:
        if hasattr(settings, 'FORMSAURUS_SURVEY_MODEL'):
            return apps.get_model(settings.FORMSAURUS_SURVEY_MODEL, require_ready=False)
        else:
            return apps.get_model('formsaurus.Survey', require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("FOMSAURUS_SURVEY_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured("FOMSAURUS_SURVEY_MODEL refers to model '%s' that has not been installed" % settings.FOMSAURUS_SURVEY_MODEL)