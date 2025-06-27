from django.contrib import admin
from .models import Referral
@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('email_id', 'processed', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
