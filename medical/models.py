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
    """Model representing doctors (dcr_Doctor)"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    specialization = models.ForeignKey('Specialization', on_delete=models.CASCADE, related_name='doctors', verbose_name=_("Направление"))
    qualification = models.CharField(_("Квалификация"), max_length=100)
    experience_years = models.PositiveIntegerField(_("Стаж (в годах)"))
    
    class Meta:
        verbose_name = _("Врач")
        verbose_name_plural = _("Врачи")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization.name}"

class Specialization(models.Model):
    """Model representing medical specializations (dcr_Specialization)"""
    name = models.CharField(_("Название"), max_length=50)
    
    class Meta:
        verbose_name = _("Направление")
        verbose_name_plural = _("Направления")
    
    def __str__(self):
        return self.name

class Contact(models.Model):
    """Model representing contacts (dcr_Contacts)"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contacts', verbose_name=_("Пользователь"))
    code = models.CharField(_("Код контакта"), max_length=50)
    value = models.CharField(_("Контакт"), max_length=50)
    
    class Meta:
        verbose_name = _("Контакт")
        verbose_name_plural = _("Контакты")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.code}: {self.value}"

class Patient(models.Model):
    """Model representing patients (dcr_Patients)"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    
    class Meta:
        verbose_name = _("Пациент")
        verbose_name_plural = _("Пациенты")
    
    def __str__(self):
        return self.user.get_full_name()

class Disease(models.Model):
    """Model representing diseases (dcr_Disease)"""
    name = models.CharField(_("Название"), max_length=50)
    description = models.TextField(_("Описание"), max_length=500, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Болезнь")
        verbose_name_plural = _("Болезни")
    
    def __str__(self):
        return self.name

class MedicalHistory(models.Model):
    """Model representing medical history (dcr_MedicalHistory)"""
    class DiseaseStatus(models.IntegerChoices):
        CURED = 0, _('Вылечен')
        DURING_TREATMENT = 1, _('В процессе лечения')
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_histories', verbose_name=_("Пациент"))
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='medical_histories', verbose_name=_("Болезнь"))
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_histories', verbose_name=_("Лечащий врач"))
    status = models.IntegerField(_("Статус болезни"), choices=DiseaseStatus.choices, default=DiseaseStatus.DURING_TREATMENT)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True, null=True)
    
    class Meta:
        verbose_name = _("История болезни")
        verbose_name_plural = _("Истории болезней")
    
    def __str__(self):
        return f"{self.patient} - {self.disease} ({self.get_status_display()})"
