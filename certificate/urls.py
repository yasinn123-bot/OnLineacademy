from django.urls import path
from . import views

app_name = 'certificate'

urlpatterns = [
    path('generate/<int:course_id>/', views.generate_certificate, name='generate_certificate'),
    path('view/<int:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('verify/', views.verify_certificate, name='verify'),
    path('download/<int:certificate_id>/', views.download_certificate, name='download_certificate'),
] 