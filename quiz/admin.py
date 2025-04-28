from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer

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
    list_display = ('title', 'course', 'total_questions', 'passing_score', 'is_published', 'created_at')
    list_filter = ('is_published', 'course')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'course')
        }),
        ('Settings', {
            'fields': ('time_limit', 'passing_score', 'is_published')
        }),
    )

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'choices', 'text_answer', 'is_correct', 'points_earned')
    can_delete = False

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'start_time', 'end_time', 'score', 'is_passed')
    list_filter = ('quiz', 'is_completed', 'start_time')
    search_fields = ('user__username', 'user__email', 'quiz__title')
    readonly_fields = ('user', 'quiz', 'start_time', 'end_time', 'score', 'is_completed')
    inlines = [StudentAnswerInline]
    
    def has_add_permission(self, request):
        return False

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_earned')
    list_filter = ('is_correct', 'attempt__quiz')
    search_fields = ('attempt__user__username', 'question__text')
    readonly_fields = ('attempt', 'question', 'choices', 'text_answer', 'is_correct', 'points_earned')
