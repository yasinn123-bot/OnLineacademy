from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.utils import timezone
import uuid

from .models import Certificate
from core.models import CustomUser, Course, UserProgress


@login_required
def generate_certificate(request, course_id):
    """Generate a certificate for a completed course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user has already a certificate for this course
    existing_certificate = Certificate.objects.filter(user=request.user, course=course).first()
    if existing_certificate:
        return redirect('certificate:view_certificate', certificate_id=existing_certificate.id)
    
    # Check if user has completed the course
    user_progress = UserProgress.objects.filter(user=request.user, course=course).first()
    
    if not user_progress or not user_progress.is_completed:
        messages.error(request, _('You must complete the course before generating a certificate.'))
        return redirect('course-detail', pk=course.id)
    
    # Create new certificate
    certificate = Certificate.objects.create(
        user=request.user,
        course=course
    )
    
    return redirect('certificate:view_certificate', certificate_id=certificate.id)


@login_required
def view_certificate(request, certificate_id):
    """View a certificate"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Ensure the user is either the certificate owner or an admin
    if request.user != certificate.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to view this certificate.'))
        return redirect('home')
    
    context = {
        'certificate': certificate,
        'course': certificate.course,
        'user': certificate.user,
    }
    
    return render(request, 'certificate/certificate_view.html', context)


@require_GET
def verify_certificate(request):
    """Verify the authenticity of a certificate"""
    verification_id = request.GET.get('verification_id')
    certificate = None
    
    if verification_id:
        try:
            # Convert string to UUID
            uuid_obj = uuid.UUID(verification_id)
            certificate = Certificate.objects.filter(verification_id=uuid_obj).first()
        except (ValueError, TypeError):
            # If verification_id is not a valid UUID
            pass
    
    context = {
        'certificate': certificate,
        'verification_id': verification_id
    }
    
    return render(request, 'certificate/certificate_verify.html', context)


@login_required
def download_certificate(request, certificate_id):
    """Download certificate as HTML for printing"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Ensure the user is either the certificate owner or an admin
    if request.user != certificate.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to download this certificate.'))
        return redirect('home')
    
    # Prepare context for the template
    context = {
        'certificate': certificate,
        'course': certificate.course,
        'user': certificate.user,
        'today': timezone.now(),
        'print_version': True
    }
    
    return render(request, 'certificate/certificate_pdf.html', context)
