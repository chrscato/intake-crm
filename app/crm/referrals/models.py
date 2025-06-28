from django.db import models


class Referral(models.Model):
    """Minimal ORM mapping for the existing ``referrals`` table."""

    email_id = models.CharField(max_length=255, unique=True)
    raw_s3_key = models.CharField(max_length=512, blank=True)
    extracted_json = models.JSONField(null=True, blank=True)
    corrected_json = models.JSONField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Database tables are created by helper scripts
        db_table = "referrals"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.email_id


class Provider(models.Model):
    """ORM mapping for the ``providers`` table."""

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
