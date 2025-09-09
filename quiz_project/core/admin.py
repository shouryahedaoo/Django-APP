from django.contrib import admin
from .models import Category, Quiz, Question, Option

class OptionInline(admin.TabularInline):
    model = Option
    extra = 2  # minimum 2 options
    max_num = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]



from django.contrib import admin
from .models import Category, Quiz, Question, Option, Attempt, Answer

# Inline for adding options to a question directly
class OptionInline(admin.TabularInline):
    model = Option
    extra = 2
    max_num = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')
    inlines = [OptionInline]

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)

class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total', 'completed_at')
    list_filter = ('quiz', 'user')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option')

# Register models
admin.site.register(Category)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Answer, AnswerAdmin)

from .models import Question
Question.objects.all()