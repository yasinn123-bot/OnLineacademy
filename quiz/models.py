from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CustomUser, Course, Module

class Quiz(models.Model):
    """Quiz model with more interactive features than Test model"""
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='quiz', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    time_limit = models.PositiveIntegerField(default=30, help_text=_('Time limit in minutes'))
    passing_score = models.PositiveIntegerField(default=70, help_text=_('Percentage required to pass'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')
        indexes = [
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())
    
    @property
    def total_questions(self):
        return self.questions.count()

class Question(models.Model):
    """Quiz question with different question types"""
    QUESTION_TYPES = (
        ('single', _('Единственный выбор')),
        ('multiple', _('Множественный выбор')),
        ('true_false', _('Верно/Неверно')),
        ('short_answer', _('Короткий ответ')),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single', db_index=True)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text=_('Объяснение правильного ответа'))
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    
    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]
    
    def __str__(self):
        return self.text[:50]

class Choice(models.Model):
    """Answer choice for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)
    
    def __str__(self):
        return self.text[:50]

class QuizAttempt(models.Model):
    """Record of a student's attempt at a quiz"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['quiz', 'user']),
            models.Index(fields=['user', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s attempt at {self.quiz.title}"
    
    @property
    def time_taken(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None
    
    @property
    def score_percentage(self):
        if self.score is not None and self.quiz.total_points > 0:
            return (self.score / self.quiz.total_points) * 100
        return 0
    
    @property
    def is_passed(self):
        return self.score_percentage >= self.quiz.passing_score if self.is_completed else False

class StudentAnswer(models.Model):
    """Student's answer to a question"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    choices = models.ManyToManyField(Choice, blank=True, related_name='selected_by')
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)
    
    def __str__(self):
        return f"Answer to {self.question} by {self.attempt.user.username}"
