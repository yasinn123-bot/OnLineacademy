from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'issue_date', 'verification_id')
    list_filter = ('issue_date', 'course')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'course__title')
    date_hierarchy = 'issue_date'
    readonly_fields = ('verification_id', 'issue_date', 'created_at', 'updated_at')
