from django.contrib import admin
from django.utils.html import format_html
from .models import Referral


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('email_id', 'patient_name', 'order_number', 'priority', 'is_processed_display', 'created_at')
    list_filter = ('priority', 'patient_gender', 'created_at', 'referring_provider_name', 'intake_client_company')
    search_fields = ('email_id', 'patient_name', 'order_number', 'intake_client_company', 'referring_provider_name')
    readonly_fields = ('created_at', 'updated_at', 'email_id')
    
    fieldsets = (
        ('Email Information', {
            'fields': ('email_id', 'email_subject', 'email_from', 'email_received_datetime', 'referral')
        }),
        ('Patient Information', {
            'fields': ('patient_name', 'patient_gender', 'patient_id', 'patient_dob', 'patient_doi', 
                      'patient_address', 'patient_email', 'patient_phone')
        }),
        ('Order Information', {
            'fields': ('order_number', 'priority', 'intake_preferred_provider', 'intake_requested_procedure')
        }),
        ('Medical Information', {
            'fields': ('injury_description', 'diagnosis_code', 'icd_code', 'diagnosis_description')
        }),
        ('Client Information', {
            'fields': ('intake_client_company', 'intake_client_email', 'intake_client_name', 'intake_client_phone')
        }),
        ('Adjuster Information', {
            'fields': ('intake_adjuster_name', 'intake_adjuster_email', 'intake_adjuster_phone')
        }),
        ('Referring Provider', {
            'fields': ('referring_provider_name', 'referring_provider_npi', 'referring_provider_address',
                      'referring_provider_email', 'referring_provider_phone')
        }),
        ('Instructions', {
            'fields': ('intake_instructions', 'patient_instructions')
        }),
        ('Employer Information', {
            'fields': ('employer_address', 'employer_email')
        }),
        ('System Information', {
            'fields': ('processed_attachments', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_processed_display(self, obj):
        """Display processed status with colored badge."""
        if obj.is_processed:
            return format_html('<span style="color: green;">✓ Processed</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    is_processed_display.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related()
    
    def has_add_permission(self, request):
        """Allow adding new referrals."""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deleting referrals."""
        return True
