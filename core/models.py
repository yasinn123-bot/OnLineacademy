from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', _('Врач')),
        ('student', _('Студент')),
        ('parent', _('Родитель'))
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='student')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses')
    is_published = models.BooleanField(default=False)
    language = models.CharField(max_length=10, choices=(
        ('ru', _('Русский')),
        ('en', _('Английский')),
        ('ky', _('Кыргызский'))
    ), default='ru')
    
    def __str__(self):
        return self.title
    
    @property
    def lesson_count(self):
        """Return total number of lessons in the course"""
        count = 0
        for module in self.modules.all():
            count += module.lessons.count()
        return count
    
    @property
    def quiz_count(self):
        """Return total number of quizzes in the course"""
        count = 0
        for module in self.modules.all():
            if module.quiz:
                count += 1
        return count
    
    @property
    def total_duration(self):
        """Return total estimated time to complete the course in minutes"""
        duration = 0
        for module in self.modules.all():
            for lesson in module.lessons.all():
                duration += lesson.estimated_time
            if module.quiz:
                duration += module.quiz.time_limit
        return duration


class Module(models.Model):
    """Course module - a group of related lessons and a quiz"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage for this module"""
        from django.db.models import Count
        
        # Get total lessons in this module
        total_lessons = self.lessons.count()
        if total_lessons == 0:
            return 0
            
        # This is calculated per user in the view
        # This property is only used as a read-only property
        return 0
    
    @property
    def completed(self):
        """Check if all lessons and quiz in this module are completed"""
        # This is calculated per user in the view
        # This property is only used as a read-only property
        return False

    def get_progress_for_user(self, user):
        """Get progress percentage for a specific user"""
        # Get user progress for the course
        from .models import UserProgress
        
        try:
            user_progress = UserProgress.objects.get(user=user, course=self.course)
            # Count total and completed lessons
            total_lessons = self.lessons.count()
            if total_lessons == 0:
                return 0, False
                
            completed_lessons = user_progress.lessons_completed.filter(module=self).count()
            progress_percentage = (completed_lessons / total_lessons) * 100
            is_completed = (completed_lessons == total_lessons)
            
            # Check if module has a quiz and it's completed
            if hasattr(self, 'quiz') and self.quiz:
                is_completed = is_completed and (self.quiz in user_progress.tests_completed.all())
            
            return round(progress_percentage), is_completed
        except UserProgress.DoesNotExist:
            return 0, False


class Lesson(models.Model):
    """A lesson within a module - contains multiple content steps"""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    estimated_time = models.PositiveIntegerField(default=15, help_text=_('Estimated time to complete in minutes'))
    quiz = models.OneToOneField('quiz.Quiz', on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson')
    
    class Meta:
        ordering = ['order']
        unique_together = ('module', 'order')
    
    def __str__(self):
        return self.title
    
    @property
    def course(self):
        """Get the course that this lesson belongs to"""
        return self.module.course
    
    @property
    def is_current(self):
        """Check if this is the current lesson for the user to study"""
        # Logic to be implemented
        return False

    def is_finished(self, user):
        """Check if the specified user has completed this lesson"""
        from .models import UserProgress
        try:
            # Get user progress for this course
            progress = UserProgress.objects.get(user=user, course=self.course)
            
            # Check if this lesson is in completed_lessons
            return self in progress.lessons_completed.all()
        except UserProgress.DoesNotExist:
            return False


class LessonContent(models.Model):
    """Individual content step within a lesson"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=100)
    content = models.TextField(help_text=_('HTML content for this step'))
    order = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='lesson_images/', null=True, blank=True)
    code_snippet = models.TextField(blank=True, null=True, help_text=_('Optional code snippet for this step'))
    
    class Meta:
        ordering = ['order']
        unique_together = ('lesson', 'order')
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class AdditionalResource(models.Model):
    """Additional learning resources for a lesson"""
    RESOURCE_TYPES = (
        ('video', _('Видео')),
        ('document', _('Документ')),
        ('link', _('Ссылка')),
    )
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='additional_resources')
    title = models.CharField(max_length=100)
    url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='link')
    
    def __str__(self):
        return self.title


class LearningOutcome(models.Model):
    """Learning outcomes for a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_outcomes')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.text


class MaterialType(models.TextChoices):
    VIDEO = 'video', _('Видео')
    PRESENTATION = 'presentation', _('Презентация')
    DOCUMENT = 'document', _('Документ')
    PROTOCOL = 'protocol', _('Протокол')
    RESEARCH = 'research', _('Исследование')
    RECOMMENDATION = 'recommendation', _('Рекомендация')


class Material(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='materials/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='materials', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials', null=True, blank=True)
    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        default=MaterialType.DOCUMENT
    )
    language = models.CharField(max_length=10, choices=(
        ('ru', _('Русский')),
        ('en', _('Английский')),
        ('ky', _('Кыргызский'))
    ), default='ru')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.material.name}"


class Test(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    passing_score = models.PositiveIntegerField(default=70)  # Percentage to pass
    language = models.CharField(max_length=10, choices=(
        ('ru', _('Русский')),
        ('en', _('Английский')),
        ('ky', _('Кыргызский'))
    ), default='ru')
    
    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text[:50]


class Certificate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=50, unique=True)
    score = models.FloatField()
    
    def __str__(self):
        return f"Certificate for {self.user.username} - {self.course.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    materials_completed = models.ManyToManyField(Material, related_name='completed_by')
    tests_completed = models.ManyToManyField(Test, related_name='completed_by')
    lessons_completed = models.ManyToManyField(Lesson, related_name='completed_by')
    lesson_steps_completed = models.JSONField(default=dict, blank=True, help_text=_('JSON containing lesson_id:step_number pairs for completed steps'))
    last_access = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username}'s progress in {self.course.title}"
