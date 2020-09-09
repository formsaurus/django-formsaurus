from django.urls import path
from django.views.generic import TemplateView
from formsaurus import views

app_name = 'formsaurus'
urlpatterns = [
     path('', views.index, name='index'),
     path('form/<uuid:survey_id>', views.survey, name='survey'),
     path('form/<uuid:survey_id>/<uuid:question_id>', views.question, name='first_question'),
     path('form/<uuid:survey_id>/<uuid:question_id>/<uuid:submission_id>', views.question, name='question'),
     path('form/completed/<uuid:survey_id>/<uuid:submission_id>', views.completed, name='completed'),
]