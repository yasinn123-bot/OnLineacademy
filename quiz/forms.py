from django import forms
from .models import Quiz, Question, Choice
from core.models import Course
from django.utils.translation import gettext_lazy as _

class QuizForm(forms.ModelForm):
    """Form for creating and editing quizzes"""
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'course', 'time_limit', 'passing_score', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите название теста')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Опишите тест')}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 180}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses based on user role
        if user:
            if user.is_staff:
                self.fields['course'].queryset = Course.objects.all()
            else:
                self.fields['course'].queryset = Course.objects.filter(author=user)
        
        # Make course optional
        self.fields['course'].required = False
        self.fields['course'].empty_label = _('Независимый тест (не связан с курсом)')

class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions"""
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'explanation', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Введите текст вопроса')}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Объяснение ответа (необязательно)')}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    # Fields for handling choices
    choice_texts = forms.CharField(widget=forms.Textarea, required=False)
    correct_choices = forms.CharField(widget=forms.HiddenInput, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['explanation'].required = False
        self.fields['order'].initial = 0

    def save(self, quiz=None, commit=True):
        instance = super().save(commit=False)
        if quiz:
            instance.quiz = quiz
        
        if commit:
            instance.save()
            
            # Process choices if provided
            if self.cleaned_data.get('choice_texts'):
                choice_texts = self.cleaned_data['choice_texts'].splitlines()
                correct_indices = [int(i) for i in self.cleaned_data.get('correct_choices', '').split(',') if i.strip()]
                
                # Delete existing choices
                instance.choices.all().delete()
                
                # Create new choices
                for i, text in enumerate(choice_texts):
                    if text.strip():
                        Choice.objects.create(
                            question=instance,
                            text=text.strip(),
                            is_correct=(i in correct_indices)
                        )
        
        return instance 