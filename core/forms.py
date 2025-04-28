from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Course, Material, MaterialType, Comment, Module, Lesson, LessonContent

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'language', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'description', 'file', 'material_type', 'language', 'course']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'material_type': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MaterialForm, self).__init__(*args, **kwargs)
        if user:
            # Only show courses created by this user
            self.fields['course'].queryset = Course.objects.filter(author=user)
            
            # For doctors, restrict material types to only text-based options
            if user.role == 'doctor':
                self.fields['material_type'].choices = [
                    (MaterialType.DOCUMENT, _('Документ')),
                    (MaterialType.PROTOCOL, _('Протокол')),
                    (MaterialType.RESEARCH, _('Исследование')),
                    (MaterialType.RECOMMENDATION, _('Рекомендация'))
                ] 

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Напишите ваш комментарий...')}),
        }
        labels = {
            'content': '',
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'course']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Например: Введение в педиатрическую онкологию')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Краткое описание содержания модуля')
            }),
            'course': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].empty_label = _('Выберите курс')

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'module', 'estimated_time']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Например: Диагностика лейкемии')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Краткое описание урока')
            }),
            'module': forms.Select(attrs={'class': 'form-select'}),
            'estimated_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': _('Время в минутах')
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['module'].empty_label = _('Выберите модуль')

class LessonContentForm(forms.ModelForm):
    class Meta:
        model = LessonContent
        fields = ['title', 'content', 'image', 'code_snippet']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Заголовок этого шага')
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control rich-text-editor',
                'rows': 8,
                'placeholder': _('Основное содержание шага')
            }),
            'code_snippet': forms.Textarea(attrs={
                'class': 'form-control code-editor',
                'rows': 5,
                'placeholder': _('Код для примера (если необходимо)')
            }),
        }
        
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 10:
            raise forms.ValidationError(_('Пожалуйста, добавьте больше содержания для этого шага.'))
        return content 