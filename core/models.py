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
    last_access = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username}'s progress in {self.course.title}"
