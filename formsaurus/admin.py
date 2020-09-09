from django.contrib import admin
from django.contrib.auth import get_user_model
from formsaurus.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = ['short_id', 'question', 'next', 'created_at']

    def next(self, obj):
        return obj.next_question.short_id if obj.next_question is not None else ''

