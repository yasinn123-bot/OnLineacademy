from django.contrib import admin
from .models import Doctor, Specialization, Contact, Patient, Disease, MedicalHistory

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'qualification', 'experience_years')
    list_filter = ('specialization', 'experience_years')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'qualification')

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'value')
    list_filter = ('code',)
    search_fields = ('user__username', 'value')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'disease', 'doctor', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'doctor', 'disease')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'disease__name', 'doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'start_date'
