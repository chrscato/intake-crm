import uuid
from django.db import models


class Referral(models.Model):
    """ORM mapping for the existing ``referrals`` table."""

    # Primary key and email fields
    id = models.AutoField(primary_key=True)
    email_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier for the email")
    email_subject = models.CharField(max_length=500, blank=True, null=True, help_text="Subject line of the email")
    email_from = models.CharField(max_length=255, blank=True, null=True, help_text="Sender email address")
    email_received_datetime = models.CharField(max_length=100, blank=True, null=True, help_text="When the email was received")
    referral = models.BooleanField(null=True, blank=True, help_text="Whether this is a referral")
    
    # Employer information
    employer_address = models.TextField(blank=True, null=True, help_text="Employer's address")
    employer_email = models.CharField(max_length=255, blank=True, null=True, help_text="Employer's email address")
    
    # Medical diagnosis information
    injury_description = models.TextField(blank=True, null=True, help_text="Description of the injury")
    diagnosis_code = models.CharField(max_length=50, blank=True, null=True, help_text="Diagnosis code")
    icd_code = models.CharField(max_length=20, blank=True, null=True, help_text="ICD-10 diagnosis code")
    diagnosis_description = models.TextField(blank=True, null=True, help_text="Detailed diagnosis description")
    
    # Intake client information
    intake_client_company = models.CharField(max_length=255, blank=True, null=True, help_text="Client company name")
    intake_client_email = models.CharField(max_length=255, blank=True, null=True, help_text="Client email address")
    intake_client_name = models.CharField(max_length=255, blank=True, null=True, help_text="Client contact name")
    intake_client_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Client phone number")
    
    # Intake adjuster information
    intake_adjuster_name = models.CharField(max_length=255, blank=True, null=True, help_text="Adjuster name")
    intake_adjuster_email = models.CharField(max_length=255, blank=True, null=True, help_text="Adjuster email address")
    intake_adjuster_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Adjuster phone number")
    
    # Patient information
    patient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Patient's full name")
    patient_gender = models.CharField(
        max_length=10, 
        blank=True, 
        null=True, 
        choices=[
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other'),
            ('U', 'Unknown')
        ],
        help_text="Patient's gender"
    )
    patient_id = models.CharField(max_length=100, blank=True, null=True, help_text="Patient identifier")
    patient_dob = models.CharField(max_length=50, blank=True, null=True, help_text="Patient's date of birth")
    patient_doi = models.CharField(max_length=50, blank=True, null=True, help_text="Patient's date of injury")
    patient_address = models.TextField(blank=True, null=True, help_text="Patient's address")
    patient_email = models.CharField(max_length=255, blank=True, null=True, help_text="Patient's email address")
    patient_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Patient's phone number")
    
    # Order and procedure information
    order_number = models.CharField(max_length=100, blank=True, null=True, help_text="Order/reference number")
    intake_preferred_provider = models.CharField(max_length=255, blank=True, null=True, help_text="Preferred provider for intake")
    intake_requested_procedure = models.TextField(blank=True, null=True, help_text="Requested medical procedure(s)")
    intake_instructions = models.TextField(blank=True, null=True, help_text="Special instructions for intake")
    patient_instructions = models.TextField(blank=True, null=True, help_text="Instructions for the patient")
    
    # Priority and urgency
    priority = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        choices=[
            ('Urgent', 'Urgent'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
            ('Routine', 'Routine')
        ],
        help_text="Priority level of the referral"
    )
    
    # Referring provider information
    referring_provider_name = models.CharField(max_length=255, blank=True, null=True, help_text="Referring provider's name")
    referring_provider_npi = models.CharField(max_length=20, blank=True, null=True, help_text="Referring provider's NPI number")
    referring_provider_address = models.TextField(blank=True, null=True, help_text="Referring provider's address")
    referring_provider_email = models.CharField(max_length=255, blank=True, null=True, help_text="Referring provider's email")
    referring_provider_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Referring provider's phone")
    
    # Processing and attachment information
    processed_attachments = models.TextField(blank=True, null=True, help_text="JSON array of processed attachments")
    
    # Provider assignment
    assigned_provider = models.CharField(max_length=50, blank=True, null=True, help_text="PrimaryKey of the assigned provider")
    
    # Geocoding and location information
    latitude = models.FloatField(blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.FloatField(blank=True, null=True, help_text="Longitude coordinate")
    geocoded_at = models.DateTimeField(blank=True, null=True, help_text="When geocoding was performed")
    geocoding_status = models.CharField(max_length=50, blank=True, null=True, help_text="Status of geocoding process")
    
    # File storage information
    raw_s3_key = models.CharField(max_length=512, blank=True, null=True, help_text="S3 key for raw file")
    extracted_json = models.CharField(max_length=512, blank=True, null=True, help_text="Path to extracted JSON file")
    corrected_json = models.CharField(max_length=512, blank=True, null=True, help_text="Path to corrected JSON file")
    
    # Processing status
    processed = models.BooleanField(default=False, help_text="Whether this referral has been processed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated")

    class Meta:
        managed = False  # Database tables are created by helper scripts
        db_table = "referrals"
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.email_id} - {self.patient_name or 'Unknown Patient'}"

    @property
    def is_urgent(self) -> bool:
        """Check if this referral is marked as urgent."""
        return self.priority == 'Urgent'

    @property
    def has_patient_info(self) -> bool:
        """Check if basic patient information is available."""
        return bool(self.patient_name and self.patient_dob)

    @property
    def has_provider_info(self) -> bool:
        """Check if referring provider information is available."""
        return bool(self.referring_provider_name and self.referring_provider_npi)

    @property
    def is_processed(self) -> bool:
        """Check if this referral has been processed (based on having data)."""
        return bool(
            self.patient_name or 
            self.order_number or 
            self.referring_provider_name or
            self.intake_client_company
        )


class Provider(models.Model):
    """ORM mapping for the ``providers`` table."""

    # Primary key - using UUIDField since the database column contains UUID values
    id = models.UUIDField(primary_key=True, db_column='PrimaryKey')
    
    # Map to the actual column names in the database
    dba_name_billing_name = models.CharField(max_length=255, db_column='"DBA Name Billing Name"')
    address_full = models.CharField(max_length=255, db_column='"Address 1 Full"')
    billing_name = models.CharField(max_length=255, blank=True, db_column='"Billing Name"')
    tin = models.CharField(max_length=50, blank=True, db_column='"TIN"')
    npi = models.CharField(max_length=50, blank=True, db_column='"NPI"')
    provider_type = models.CharField(max_length=100, blank=True, db_column='"Provider Type"')
    latitude = models.FloatField(null=True, blank=True, db_column='"Latitude"')
    longitude = models.FloatField(null=True, blank=True, db_column='"Longitude"')

    class Meta:
        managed = False
        db_table = "providers"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.dba_name_billing_name
