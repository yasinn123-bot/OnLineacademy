from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Doctor, Specialization, Contact, Patient, Disease, MedicalHistory
from .serializers import (DoctorSerializer, SpecializationSerializer, ContactSerializer,
                          PatientSerializer, DiseaseSerializer, MedicalHistorySerializer)
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import CustomUser

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
