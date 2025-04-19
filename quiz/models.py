from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CustomUser, Course

class Quiz(models.Model):
    """
    Quiz model for creating quizzes tied to courses or standalone
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time_limit = models.IntegerField(help_text=_("Time limit in minutes"), default=30)
    passing_score = models.PositiveIntegerField(default=70, help_text=_("Percentage needed to pass"))
    is_published = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Тест')
        verbose_name_plural = _('Тесты')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def total_questions(self):
        return self.questions.count()
        
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())

class QuestionType(models.TextChoices):
    SINGLE_CHOICE = 'single', _('Один вариант')
    MULTIPLE_CHOICE = 'multiple', _('Несколько вариантов')
    TRUE_FALSE = 'true_false', _('Верно/Неверно')
    SHORT_ANSWER = 'short_answer', _('Короткий ответ')

class Question(models.Model):
    """
    Question model for quiz questions
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE
    )
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, null=True, help_text=_("Explanation shown after answering"))
    image = models.ImageField(upload_to='quiz_images/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Вопрос')
        verbose_name_plural = _('Вопросы')
        ordering = ['order']
    
    def __str__(self):
        return self.text[:50]

class Choice(models.Model):
    """
    Choice model for question choices/options
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Вариант ответа')
        verbose_name_plural = _('Варианты ответов')
    
    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    """
    Quiz attempt tracking
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Попытка теста')
        verbose_name_plural = _('Попытки тестов')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"
    
    @property
    def is_completed(self):
        return self.completed_at is not None
    
    @property
    def score_percentage(self):
        if not self.score or not self.quiz.total_points:
            return 0
        return round((self.score / self.quiz.total_points) * 100)

class Answer(models.Model):
    """
    User answers to questions
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For single/multiple choice questions
    selected_choices = models.ManyToManyField(Choice, blank=True)
    
    # For short answer questions
    text_answer = models.CharField(max_length=255, blank=True, null=True)
    
    # Scoring
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)
    
    class Meta:
        verbose_name = _('Ответ')
        verbose_name_plural = _('Ответы')
    
    def __str__(self):
        return f"Answer to {self.question}"
