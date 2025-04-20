from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'doctors', views.DoctorViewSet)
router.register(r'specializations', views.SpecializationViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'medical-histories', views.MedicalHistoryViewSet)
router.register(r'diseases', views.DiseaseViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('mark-as-cured/<int:history_id>/', views.mark_medical_history_as_cured, name='mark_medical_history_as_cured'),
] 