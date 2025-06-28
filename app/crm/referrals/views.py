from math import radians, sin, cos, asin, sqrt
from django.shortcuts import get_object_or_404, render

from .forms import ReferralForm
from .models import Provider, Referral


def referral_list(request):
    referrals = Referral.objects.all().order_by('-created_at')[:100]
    return render(request, 'referrals/referral_list.html', {'referrals': referrals})


def referral_detail(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    if request.method == 'POST':
        form = ReferralForm(request.POST, instance=referral)
        if form.is_valid():
            form.save()
    else:
        form = ReferralForm(instance=referral)
    return render(request, 'referrals/referral_detail.html', {'form': form, 'referral': referral})


def _haversine(lat1, lon1, lat2, lon2):
    # Distance in miles between two (lat, lon) pairs
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def provider_selection(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    providers = []
    if referral.latitude is not None and referral.longitude is not None:
        all_providers = Provider.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        enriched = []
        for p in all_providers:
            if p.latitude is None or p.longitude is None:
                continue
            distance = _haversine(referral.latitude, referral.longitude, p.latitude, p.longitude)
            p.distance = distance
            enriched.append(p)
        providers = sorted(enriched, key=lambda x: x.distance)[:10]
    return render(request, 'referrals/provider_selection.html', {
        'referral': referral,
        'providers': providers,
    })
