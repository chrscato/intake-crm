import json
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Referral


class ReferralForm(forms.ModelForm):
    """Form for creating and editing referrals using actual database columns."""
    
    class Meta:
        model = Referral
        fields = [
            # Email and metadata fields
            'email_id', 'email_subject', 'email_from', 'email_received_datetime', 'referral',
            
            # Employer information
            'employer_address', 'employer_email',
            
            # Medical diagnosis information
            'injury_description', 'diagnosis_code', 'icd_code', 'diagnosis_description',
            
            # Intake client information
            'intake_client_company', 'intake_client_email', 'intake_client_name', 'intake_client_phone',
            
            # Intake adjuster information
            'intake_adjuster_name', 'intake_adjuster_email', 'intake_adjuster_phone',
            
            # Patient information
            'patient_name', 'patient_gender', 'patient_id', 'patient_dob', 'patient_doi',
            'patient_address', 'patient_email', 'patient_phone',
            
            # Order and procedure information
            'order_number', 'intake_preferred_provider', 'intake_requested_procedure',
            'intake_instructions', 'patient_instructions',
            
            # Priority and urgency
            'priority',
            
            # Referring provider information
            'referring_provider_name', 'referring_provider_npi', 'referring_provider_address',
            'referring_provider_email', 'referring_provider_phone',
            
            # Processing and attachment information
            'processed_attachments',
        ]
        widgets = {
            # Email and metadata fields
            'email_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Email ID (auto-generated)'
            }),
            'email_subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email subject line'
            }),
            'email_from': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'sender@example.com'
            }),
            'email_received_datetime': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD HH:MM:SS'
            }),
            'referral': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # Employer information
            'employer_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Employer address'
            }),
            'employer_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'employer@company.com'
            }),
            
            # Medical diagnosis information
            'injury_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description of the injury'
            }),
            'diagnosis_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Diagnosis code'
            }),
            'icd_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ICD-10 code'
            }),
            'diagnosis_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed diagnosis description'
            }),
            
            # Intake client information
            'intake_client_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client company name'
            }),
            'intake_client_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'client@company.com'
            }),
            'intake_client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client contact name'
            }),
            'intake_client_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            
            # Intake adjuster information
            'intake_adjuster_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adjuster name'
            }),
            'intake_adjuster_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'adjuster@company.com'
            }),
            'intake_adjuster_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            
            # Patient information
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patient full name'
            }),
            'patient_gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'patient_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patient identifier'
            }),
            'patient_dob': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'patient_doi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'patient_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Patient address'
            }),
            'patient_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'patient@email.com'
            }),
            'patient_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            
            # Order and procedure information
            'order_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Order/reference number'
            }),
            'intake_preferred_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred provider'
            }),
            'intake_requested_procedure': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Requested medical procedure(s)'
            }),
            'intake_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special instructions for intake'
            }),
            'patient_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Instructions for the patient'
            }),
            
            # Priority and urgency
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Referring provider information
            'referring_provider_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referring provider name'
            }),
            'referring_provider_npi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NPI number'
            }),
            'referring_provider_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Provider address'
            }),
            'referring_provider_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'provider@clinic.com'
            }),
            'referring_provider_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            
            # Processing and attachment information
            'processed_attachments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'JSON array of processed attachments'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email_id readonly for existing records
        if self.instance and self.instance.pk:
            self.fields['email_id'].widget.attrs['readonly'] = 'readonly'
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_processed_attachments(self):
        """Validate that processed_attachments is valid JSON if provided."""
        data = self.cleaned_data.get('processed_attachments')
        if data:
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_('Please enter valid JSON format for processed attachments.'))
        return data

    def clean_intake_requested_procedure(self):
        """Validate that intake_requested_procedure is valid JSON if provided."""
        data = self.cleaned_data.get('intake_requested_procedure')
        if data:
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_('Please enter valid JSON format for requested procedures.'))
        return data


class ReferralFilterForm(forms.Form):
    """Filter form for referral list view."""
    
    # Search fields
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by patient name, email ID, order number...'
        }),
        help_text="Search across patient name, email ID, order number, and other fields"
    )
    
    # Status filter (based on is_processed property)
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Statuses'),
            ('processed', 'Processed'),
            ('unprocessed', 'Unprocessed'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filter by processing status"
    )
    
    # Priority filter
    priority = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Priorities'),
            ('Urgent', 'Urgent'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
            ('Routine', 'Routine'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filter by priority level"
    )
    
    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From date'
        }),
        help_text="Filter referrals created from this date"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To date'
        }),
        help_text="Filter referrals created up to this date"
    )
    
    # Patient gender filter
    patient_gender = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Genders'),
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other'),
            ('U', 'Unknown'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filter by patient gender"
    )
    
    # Referring provider filter
    referring_provider_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Referring provider name'
        }),
        help_text="Filter by referring provider name"
    )
    
    # Client company filter
    intake_client_company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client company name'
        }),
        help_text="Filter by client company"
    )

    def clean(self):
        """Validate date range if both dates are provided."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_('Start date must be before or equal to end date.'))
        
        return cleaned_data


class ReferralBulkActionForm(forms.Form):
    """Form for bulk actions on referrals."""
    
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('mark_processed', 'Mark as Processed'),
            ('mark_unprocessed', 'Mark as Unprocessed'),
            ('delete', 'Delete Selected'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Choose an action to perform on selected referrals"
    )
    
    referral_ids = forms.CharField(
        widget=forms.HiddenInput(),
        help_text="Comma-separated list of referral IDs"
    )
