from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Course, Material, MaterialType

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
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
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