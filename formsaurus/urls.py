from django.urls import path
from formsaurus import views

app_name = 'formsaurus'
urlpatterns = [
    path('form/<uuid:survey_id>', views.SurveyView.as_view(), name='survey'),
    path('form/<uuid:survey_id>/<uuid:question_id>/<uuid:submission_id>',
         views.QuestionView.as_view(), name='question'),
    path('form/completed/<uuid:survey_id>/<uuid:submission_id>',
         views.CompletedView.as_view(), name='completed'),
]
