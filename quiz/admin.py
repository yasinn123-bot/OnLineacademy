from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('quiz', 'question_type')
    search_fields = ('text', 'quiz__title')
    inlines = [ChoiceInline]

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'total_questions', 'passing_score', 'is_published', 'created_at')
    list_filter = ('is_published', 'course', 'author')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'course', 'author')
        }),
        ('Settings', {
            'fields': ('time_limit', 'passing_score', 'is_published')
        }),
    )

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'selected_choices', 'text_answer', 'is_correct', 'points_earned')
    can_delete = False

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'started_at', 'completed_at', 'score', 'passed')
    list_filter = ('quiz', 'passed', 'started_at')
    search_fields = ('user__username', 'user__email', 'quiz__title')
    readonly_fields = ('user', 'quiz', 'started_at', 'completed_at', 'score', 'passed')
    inlines = [AnswerInline]
    
    def has_add_permission(self, request):
        return False

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_earned', 'created_at')
    list_filter = ('is_correct', 'attempt__quiz')
    search_fields = ('attempt__user__username', 'question__text')
    readonly_fields = ('attempt', 'question', 'selected_choices', 'text_answer', 'is_correct', 'points_earned')
