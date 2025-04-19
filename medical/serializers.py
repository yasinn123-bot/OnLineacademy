from rest_framework import serializers
from .models import Doctor, Specialization, Contact, Patient, Disease, MedicalHistory
from core.models import CustomUser

class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']

class DoctorSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=CustomUser.objects.all())
    user_details = serializers.SerializerMethodField()
    specialization_details = SpecializationSerializer(source='specialization', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['user_id', 'user_details', 'specialization', 'specialization_details', 
                 'qualification', 'experience_years']
    
    def get_user_details(self, obj):
        return {
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'email': obj.user.email,
            'role': obj.user.role
        }

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'user', 'code', 'value']

class PatientSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=CustomUser.objects.all())
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['user_id', 'user_details']
    
    def get_user_details(self, obj):
        return {
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'email': obj.user.email,
            'role': obj.user.role
        }

class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'description']

class MedicalHistorySerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    disease_details = DiseaseSerializer(source='disease', read_only=True)
    doctor_details = DoctorSerializer(source='doctor', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MedicalHistory
        fields = ['id', 'patient', 'patient_details', 'disease', 'disease_details', 
                 'doctor', 'doctor_details', 'status', 'status_display', 
                 'start_date', 'end_date', 'notes'] 