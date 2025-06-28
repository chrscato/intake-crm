from django import forms
from .models import Referral

class ReferralForm(forms.ModelForm):
    class Meta:
        model = Referral
        exclude = ('id', 'created_at', 'updated_at')
