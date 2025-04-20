from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .models import Doctor, Specialization, Contact, Patient, Disease, MedicalHistory
from .serializers import (DoctorSerializer, SpecializationSerializer, ContactSerializer,
                          PatientSerializer, DiseaseSerializer, MedicalHistorySerializer)
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import CustomUser, Course, Material
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from core.views import get_user_role

# Create your views here.

class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticated]

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_specialization(self, request):
        specialization_id = request.query_params.get('specialization_id')
        if specialization_id:
            doctors = Doctor.objects.filter(specialization_id=specialization_id)
            serializer = self.get_serializer(doctors, many=True)
            return Response(serializer.data)
        return Response({"error": "Specialization ID is required"}, status=400)

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contact.objects.all()
        return Contact.objects.filter(user=user)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = self.get_serializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({"error": "Patient profile not found"}, status=404)

class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [permissions.IsAuthenticated]

class MedicalHistoryViewSet(viewsets.ModelViewSet):
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MedicalHistory.objects.all()
        
        try:
            patient = Patient.objects.get(user=user)
            return MedicalHistory.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            try:
                doctor = Doctor.objects.get(user=user)
                return MedicalHistory.objects.filter(doctor=doctor)
            except Doctor.DoesNotExist:
                return MedicalHistory.objects.none()
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status = request.query_params.get('status')
        if status is not None:
            queryset = self.get_queryset().filter(status=status)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"error": "Status parameter is required"}, status=400)

@login_required
def doctor_dashboard(request):
    """
    Display the doctor dashboard with dynamic data from the database
    """
    user = request.user
    user_role = get_user_role(user)
    
    # Verify the user is a doctor
    if user_role != 'doctor':
        return redirect('dashboard')
    
    try:
        # Get the doctor profile
        doctor = Doctor.objects.get(user=user)
        
        # Get courses created by this doctor
        created_courses = Course.objects.filter(author=user).select_related('author')
        created_materials = Material.objects.filter(author=user).select_related('course')
        
        # Get patients under this doctor's care
        patients = Patient.objects.filter(
            medical_histories__doctor=doctor
        ).distinct().select_related('user')
        
        # Get contacts for these patients
        patient_ids = [patient.user_id for patient in patients]
        contacts = Contact.objects.filter(user_id__in=patient_ids)
        
        # Create a dictionary of patient contacts
        patient_contacts = {}
        for contact in contacts:
            if contact.code == 'phone':  # Only include phone contacts
                patient_contacts[contact.user_id] = contact.value
        
        # Get medical histories for this doctor
        medical_histories = MedicalHistory.objects.filter(
            doctor=doctor
        ).select_related('patient', 'disease', 'patient__user')
        
        # Count statistics
        active_patients_count = medical_histories.filter(
            status=MedicalHistory.DiseaseStatus.DURING_TREATMENT
        ).values('patient').distinct().count()
        
        cured_patients_count = medical_histories.filter(
            status=MedicalHistory.DiseaseStatus.CURED
        ).values('patient').distinct().count()
        
        # Prepare data for the template
        patients_data = []
        for patient in patients:
            contact = patient_contacts.get(patient.user_id, 'Не указан')
            patients_data.append({
                'id': patient.user_id,
                'name': patient.user.get_full_name(),
                'contact': contact
            })
        
        # Prepare medical history data
        histories_data = []
        for history in medical_histories:
            histories_data.append({
                'patient_name': history.patient.user.get_full_name(),
                'disease_name': history.disease.name,
                'status': history.status,
                'status_display': history.get_status_display(),
                'id': history.id
            })
        
        # Get disease and disease status enumerations for reference
        disease_statuses = [
            {'id': 1, 'number': 0, 'name': 'Cured', 'description': 'Статус для вылеченных болезней'},
            {'id': 2, 'number': 1, 'name': 'DuringTreatment', 'description': 'В процессе лечения'},
        ]
        
        diseases = Disease.objects.all()
        
        context = {
            'doctor': doctor,
            'created_courses': created_courses,
            'created_materials': created_materials,
            'user_role': user_role,
            'patients': patients_data,
            'medical_histories': histories_data,
            'courses_count': created_courses.count(),
            'active_patients_count': active_patients_count,
            'cured_patients_count': cured_patients_count,
            'disease_statuses': disease_statuses,
            'diseases': diseases,
        }
        
        return render(request, 'core/doctor_dashboard.html', context)
    
    except Doctor.DoesNotExist:
        # If the user is registered as a doctor role but doesn't have a doctor profile
        context = {
            'created_courses': Course.objects.filter(author=user).select_related('author'),
            'user_role': user_role,
            'needs_profile': True,
        }
        return render(request, 'core/doctor_dashboard.html', context)

@login_required
def mark_medical_history_as_cured(request, history_id):
    """
    Mark a medical history record as cured
    """
    if request.method == 'POST':
        try:
            history = MedicalHistory.objects.get(id=history_id, doctor__user=request.user)
            history.status = MedicalHistory.DiseaseStatus.CURED
            history.save()
            messages.success(request, f'Пациент {history.patient.user.get_full_name()} помечен как вылеченный')
        except MedicalHistory.DoesNotExist:
            messages.error(request, 'История болезни не найдена или у вас нет прав для её редактирования')
    
    return redirect('doctor_dashboard')
