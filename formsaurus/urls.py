from django.urls import path
from django.views.generic import TemplateView
from formsaurus import views

app_name = 'formsaurus'
urlpatterns = [
     path('form/<uuid:survey_id>', views.SurveyView.as_view(), name='survey'),
     path('form/<uuid:survey_id>/<uuid:question_id>/<uuid:submission_id>', views.QuestionView.as_view(), name='question'),
     path('form/completed/<uuid:survey_id>/<uuid:submission_id>', views.CompletedView.as_view(), name='completed'),
     
     # MANAGEMENT
     path('manage/form/add', views.SurveyAddView.as_view(), name='survey_add'),
     path('manage/form/create/<uuid:survey_id>', views.SurveyWizardView.as_view(), name='survey_wizard'),
     
     path('manage/form/create/<uuid:survey_id>/add', views.AddQuestionView.as_view(), name='survey_add_question'),
     path('manage/form/create/<uuid:survey_id>/add/<slug:question_type>', views.AddQuestionView.as_view(), name='survey_add_question'),

     path('manage/form/list', views.SurveysView.as_view(), name='surveys'),
]