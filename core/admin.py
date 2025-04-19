from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Course, Material, Comment, Test, 
    Question, Answer, Certificate, UserProgress
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'bio', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'first_name', 'last_name', 'bio', 'profile_picture')}),
    )

class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

class TestInline(admin.TabularInline):
    model = Test
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'language', 'is_published', 'created_at')
    list_filter = ('is_published', 'language', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    inlines = [MaterialInline, TestInline]

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'material_type', 'course', 'author', 'language', 'created_at')
    list_filter = ('material_type', 'language', 'created_at')
    search_fields = ('name', 'description', 'author__username')

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'passing_score', 'language', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'points')
    list_filter = ('test', 'points')
    search_fields = ('text',)
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('text',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'material', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'user', 'course', 'score', 'issued_at')
    list_filter = ('issued_at', 'course')
    search_fields = ('certificate_id', 'user__username', 'course__title')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'last_access')
    list_filter = ('course', 'last_access')
    search_fields = ('user__username', 'course__title')
    filter_horizontal = ('materials_completed', 'tests_completed')

# Register all models with admin
admin.site.register(CustomUser, CustomUserAdmin)
