from django.db import models

class Referral(models.Model):
    email_id       = models.CharField(max_length=255, unique=True)
    raw_s3_key     = models.CharField(max_length=512, blank=True)
    extracted_json = models.JSONField(null=True, blank=True)
    corrected_json = models.JSONField(null=True, blank=True)
    processed      = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.email_id
