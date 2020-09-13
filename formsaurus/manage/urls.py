from django.urls import path
from formsaurus.manage import views as manage

app_name = 'formsaurus_manage'
urlpatterns = [
    path('manage', manage.ManageView.as_view(), name='manage'),
    path('manage/form/add', manage.SurveyAddView.as_view(), name='survey_add'),
    path('manage/form/create/<uuid:survey_id>',
         manage.SurveyWizardView.as_view(), name='survey_wizard'),
    path('manage/form/publish/<uuid:survey_id>',
         manage.PublishSurveyView.as_view(), name='survey_publish'),
    path('manage/form/create/<uuid:survey_id>/add',
         manage.AddQuestionView.as_view(), name='survey_add_question'),
    path('manage/form/create/<uuid:survey_id>/add/<slug:question_type>',
         manage.AddQuestionView.as_view(), name='survey_add_question'),
    path('manage/form/create/<uuid:survey_id>/field',
         manage.HiddenFieldView.as_view(), name='survey_add_hidden_field'),
    path('manage/form/delete/<uuid:survey_id>',
         manage.DeleteSurveyView.as_view(), name='survey_delete'),
    path('manage/form/list', manage.SurveysView.as_view(), name='surveys'),
    path('manage/form/submissions/<uuid:survey_id>',
         manage.SubmissionsView.as_view(), name='submissions'),
    path('manage/form/submissions/<uuid:survey_id>/<uuid:submission_id>',
         manage.SubmissionView.as_view(), name='submission'),
]