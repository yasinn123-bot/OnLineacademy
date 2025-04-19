from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CustomUser, Course
import uuid

class Certificate(models.Model):
    """Model representing a completion certificate for a course"""
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='certificate_records', 
        verbose_name=_('User')
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='certificate_records', 
        verbose_name=_('Course')
    )
    verification_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Verification ID'))
    issue_date = models.DateField(auto_now_add=True, verbose_name=_('Issue Date'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Certificate')
        verbose_name_plural = _('Certificates')
        unique_together = ('user', 'course')
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.course.title}"
