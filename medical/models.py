from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CustomUser

# Enumerations
class DiseaseStatus(models.IntegerChoices):
    CURED = 0, _('Вылечен')
    DURING_TREATMENT = 1, _('В процессе лечения')

# Basic User Model (already exists as CustomUser in core app)
# We'll extend functionality with related models

class Doctor(models.Model):
    """
    Doctor model that extends CustomUser through a OneToOne relationship
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    specialization = models.ForeignKey('Specialization', on_delete=models.CASCADE, related_name='doctors')
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization.name}"
    
    class Meta:
        verbose_name = _('Врач')
        verbose_name_plural = _('Врачи')

class Specialization(models.Model):
    """
    Medical specialization direction
    """
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Направление')
        verbose_name_plural = _('Направления')

class Contact(models.Model):
    """
    Contact information for users
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contacts')
    code = models.CharField(max_length=50)  # Type of contact (email, phone, etc)
    value = models.CharField(max_length=50)  # Actual contact value
    
    def __str__(self):
        return f"{self.user.username} - {self.code}: {self.value}"
    
    class Meta:
        verbose_name = _('Контакт')
        verbose_name_plural = _('Контакты')

class Patient(models.Model):
    """
    Patient model that extends CustomUser through a OneToOne relationship
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    
    def __str__(self):
        return f"Patient: {self.user.first_name} {self.user.last_name}"
    
    class Meta:
        verbose_name = _('Пациент')
        verbose_name_plural = _('Пациенты')

class Disease(models.Model):
    """
    Disease catalog
    """
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Болезнь')
        verbose_name_plural = _('Болезни')

class MedicalHistory(models.Model):
    """
    Medical history record linking patients, diseases and doctors
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='patient_cases')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patient_cases')
    status = models.IntegerField(choices=DiseaseStatus.choices, default=DiseaseStatus.DURING_TREATMENT)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.patient} - {self.disease} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = _('История болезни')
        verbose_name_plural = _('Истории болезней')
