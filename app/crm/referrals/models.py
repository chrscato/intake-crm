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

    dba_name_billing_name = models.CharField(max_length=255)
    address_full = models.CharField(max_length=255)
    billing_name = models.CharField(max_length=255, blank=True)
    tin = models.CharField(max_length=50, blank=True)
    npi = models.CharField(max_length=50, blank=True)
    provider_type = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "providers"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.dba_name_billing_name
