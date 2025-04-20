from django.contrib import admin
from .models import Doctor, Specialization, Patient, Contact, Disease, MedicalHistory

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'qualification', 'experience_years')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization__name')
    list_filter = ('specialization', 'experience_years')

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'value')
    search_fields = ('user__username', 'value')
    list_filter = ('code',)

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'disease', 'doctor', 'status', 'created_at', 'updated_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'disease__name')
    list_filter = ('status', 'created_at')
    date_hierarchy = 'created_at'
