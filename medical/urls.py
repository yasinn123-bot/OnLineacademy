from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DoctorViewSet, SpecializationViewSet, ContactViewSet,
                   PatientViewSet, DiseaseViewSet, MedicalHistoryViewSet)

router = DefaultRouter()
router.register(r'doctors', DoctorViewSet)
router.register(r'specializations', SpecializationViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'diseases', DiseaseViewSet)
router.register(r'medical-history', MedicalHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 