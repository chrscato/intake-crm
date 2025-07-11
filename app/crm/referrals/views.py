from math import radians, sin, cos, asin, sqrt
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Case, When, BooleanField
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView
from django.views.decorators.http import require_POST

from .forms import ReferralForm, ReferralFilterForm, ReferralBulkActionForm
from .models import Provider, Referral


def dashboard(request):
    """Dashboard view with key metrics and statistics."""
    
    # Get date range for filtering (last 30 days by default)
    days = request.GET.get('days', 30)
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=int(days))
    
    # Base queryset
    referrals = Referral.objects.filter(created_at__range=(start_date, end_date))
    
    # Key metrics
    total_referrals = referrals.count()
    
    # Calculate processed referrals using the is_processed property logic
    processed_referrals = referrals.filter(
        Q(patient_name__isnull=False) | 
        Q(order_number__isnull=False) | 
        Q(referring_provider_name__isnull=False) |
        Q(intake_client_company__isnull=False)
    ).exclude(
        Q(patient_name='') & 
        Q(order_number='') & 
        Q(referring_provider_name='') &
        Q(intake_client_company='')
    ).count()
    
    unprocessed_referrals = total_referrals - processed_referrals
    urgent_referrals = referrals.filter(priority='Urgent').count()
    
    # Processing rate
    processing_rate = (processed_referrals / total_referrals * 100) if total_referrals > 0 else 0
    
    # Priority breakdown
    priority_stats = referrals.values('priority').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activity
    recent_referrals = Referral.objects.order_by('-created_at')[:10]
    
    # Gender distribution
    gender_stats = referrals.values('patient_gender').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top referring providers
    top_providers = referrals.values('referring_provider_name').annotate(
        count=Count('id')
    ).filter(referring_provider_name__isnull=False).exclude(
        referring_provider_name=''
    ).order_by('-count')[:10]
    
    # Top client companies
    top_clients = referrals.values('intake_client_company').annotate(
        count=Count('id')
    ).filter(intake_client_company__isnull=False).exclude(
        intake_client_company=''
    ).order_by('-count')[:10]
    
    context = {
        'total_referrals': total_referrals,
        'processed_referrals': processed_referrals,
        'unprocessed_referrals': unprocessed_referrals,
        'urgent_referrals': urgent_referrals,
        'processing_rate': round(processing_rate, 1),
        'priority_stats': priority_stats,
        'recent_referrals': recent_referrals,
        'gender_stats': gender_stats,
        'top_providers': top_providers,
        'top_clients': top_clients,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'referrals/dashboard.html', context)


def referral_list(request):
    """List view with pagination, filtering, and search using individual database fields."""
    
    # Get filter form
    filter_form = ReferralFilterForm(request.GET)
    
    # Build queryset with filters
    queryset = Referral.objects.all()
    
    if filter_form.is_valid():
        # Search filter - search across multiple individual fields
        search = filter_form.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient_name__icontains=search) |
                Q(email_id__icontains=search) |
                Q(order_number__icontains=search) |
                Q(intake_client_company__icontains=search) |
                Q(referring_provider_name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(intake_client_name__icontains=search) |
                Q(intake_adjuster_name__icontains=search)
            )
        
        # Status filter - use the is_processed logic
        status = filter_form.cleaned_data.get('status')
        if status == 'processed':
            queryset = queryset.filter(
                Q(patient_name__isnull=False) | 
                Q(order_number__isnull=False) | 
                Q(referring_provider_name__isnull=False) |
                Q(intake_client_company__isnull=False)
            ).exclude(
                Q(patient_name='') & 
                Q(order_number='') & 
                Q(referring_provider_name='') &
                Q(intake_client_company='')
            )
        elif status == 'unprocessed':
            queryset = queryset.filter(
                Q(patient_name__isnull=True) | 
                Q(patient_name='')
            ).filter(
                Q(order_number__isnull=True) | 
                Q(order_number='')
            ).filter(
                Q(referring_provider_name__isnull=True) | 
                Q(referring_provider_name='')
            ).filter(
                Q(intake_client_company__isnull=True) | 
                Q(intake_client_company='')
            )
        
        # Priority filter
        priority = filter_form.cleaned_data.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Date range filters
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Patient gender filter
        patient_gender = filter_form.cleaned_data.get('patient_gender')
        if patient_gender:
            queryset = queryset.filter(patient_gender=patient_gender)
        
        # Referring provider filter
        referring_provider_name = filter_form.cleaned_data.get('referring_provider_name')
        if referring_provider_name:
            queryset = queryset.filter(
                referring_provider_name__icontains=referring_provider_name
            )
        
        # Client company filter
        intake_client_company = filter_form.cleaned_data.get('intake_client_company')
        if intake_client_company:
            queryset = queryset.filter(
                intake_client_company__icontains=intake_client_company
            )
    
    # Order by created date (newest first)
    queryset = queryset.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    
    try:
        referrals = paginator.page(page)
    except PageNotAnInteger:
        referrals = paginator.page(1)
    except EmptyPage:
        referrals = paginator.page(paginator.num_pages)
    
    # Bulk action form
    bulk_form = ReferralBulkActionForm()
    
    # Quick stats for the current filtered results
    total_count = queryset.count()
    
    # Calculate processed count using the same logic
    processed_count = queryset.filter(
        Q(patient_name__isnull=False) | 
        Q(order_number__isnull=False) | 
        Q(referring_provider_name__isnull=False) |
        Q(intake_client_company__isnull=False)
    ).exclude(
        Q(patient_name='') & 
        Q(order_number='') & 
        Q(referring_provider_name='') &
        Q(intake_client_company='')
    ).count()
    
    urgent_count = queryset.filter(priority='Urgent').count()
    
    context = {
        'referrals': referrals,
        'filter_form': filter_form,
        'bulk_form': bulk_form,
        'total_count': total_count,
        'processed_count': processed_count,
        'urgent_count': urgent_count,
        'processing_rate': round((processed_count / total_count * 100) if total_count > 0 else 0, 1),
    }
    
    return render(request, 'referrals/referral_list.html', context)


def referral_create(request):
    """Create a new referral using individual database fields."""
    
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save()  # Saves directly to individual database columns
            messages.success(request, f'Referral "{referral.email_id}" created successfully.')
            return redirect('referral_detail', pk=referral.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReferralForm()
    
    context = {
        'form': form,
        'mode': 'create',
        'title': 'Create New Referral',
    }
    
    return render(request, 'referrals/referral_form.html', context)


def referral_detail(request, pk):
    """Detail view with edit functionality using individual database fields."""
    
    referral = get_object_or_404(Referral, pk=pk)
    
    if request.method == 'POST':
        form = ReferralForm(request.POST, instance=referral)
        if form.is_valid():
            form.save()  # Saves directly to individual database columns
            messages.success(request, f'Referral "{referral.email_id}" updated successfully.')
            return redirect('referral_detail', pk=referral.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReferralForm(instance=referral)
    
    # Get navigation (prev/next)
    all_referrals = Referral.objects.order_by('-created_at')
    current_index = list(all_referrals.values_list('pk', flat=True)).index(referral.pk)
    
    prev_referral = None
    next_referral = None
    
    if current_index > 0:
        prev_referral = all_referrals[current_index - 1]
    if current_index < len(all_referrals) - 1:
        next_referral = all_referrals[current_index + 1]
    
    context = {
        'form': form,
        'referral': referral,
        'mode': 'edit',
        'title': f'Edit Referral: {referral.email_id}',
        'prev_referral': prev_referral,
        'next_referral': next_referral,
    }
    
    return render(request, 'referrals/referral_form.html', context)


class ReferralDeleteView(DeleteView):
    """Delete view with confirmation."""
    
    model = Referral
    template_name = 'referrals/referral_confirm_delete.html'
    success_url = reverse_lazy('referral_list')
    
    def delete(self, request, *args, **kwargs):
        referral = self.get_object()
        messages.success(request, f'Referral "{referral.email_id}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


@require_POST
def referral_bulk_action(request):
    """Handle bulk actions on referrals using individual database fields."""
    
    form = ReferralBulkActionForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        referral_ids = form.cleaned_data['referral_ids'].split(',')
        
        if not referral_ids or referral_ids == ['']:
            messages.error(request, 'No referrals selected.')
            return redirect('referral_list')
        
        referrals = Referral.objects.filter(pk__in=referral_ids)
        
        if action == 'mark_processed':
            # Mark as processed by setting key fields
            count = referrals.update(
                patient_name=Case(
                    When(patient_name__isnull=True, then='Processed'),
                    default='patient_name'
                ),
                order_number=Case(
                    When(order_number__isnull=True, then='PROCESSED'),
                    default='order_number'
                )
            )
            messages.success(request, f'{count} referral(s) marked as processed.')
        elif action == 'mark_unprocessed':
            # Mark as unprocessed by clearing key fields
            count = referrals.update(
                patient_name='',
                order_number='',
                referring_provider_name='',
                intake_client_company=''
            )
            messages.success(request, f'{count} referral(s) marked as unprocessed.')
        elif action == 'delete':
            count = referrals.count()
            referrals.delete()
            messages.success(request, f'{count} referral(s) deleted successfully.')
        else:
            messages.error(request, 'Invalid action selected.')
    else:
        messages.error(request, 'Invalid form data.')
    
    return redirect('referral_list')


def referral_export(request):
    """Export referrals to CSV using individual database fields."""
    
    from django.http import HttpResponse
    import csv
    
    # Get filtered queryset (reuse filter logic from referral_list)
    filter_form = ReferralFilterForm(request.GET)
    queryset = Referral.objects.all()
    
    if filter_form.is_valid():
        # Apply same filters as referral_list
        search = filter_form.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient_name__icontains=search) |
                Q(email_id__icontains=search) |
                Q(order_number__icontains=search) |
                Q(intake_client_company__icontains=search) |
                Q(referring_provider_name__icontains=search) |
                Q(patient_id__icontains=search)
            )
        
        status = filter_form.cleaned_data.get('status')
        if status == 'processed':
            queryset = queryset.filter(
                Q(patient_name__isnull=False) | 
                Q(order_number__isnull=False) | 
                Q(referring_provider_name__isnull=False) |
                Q(intake_client_company__isnull=False)
            ).exclude(
                Q(patient_name='') & 
                Q(order_number='') & 
                Q(referring_provider_name='') &
                Q(intake_client_company='')
            )
        elif status == 'unprocessed':
            queryset = queryset.filter(
                Q(patient_name__isnull=True) | 
                Q(patient_name='')
            ).filter(
                Q(order_number__isnull=True) | 
                Q(order_number='')
            ).filter(
                Q(referring_provider_name__isnull=True) | 
                Q(referring_provider_name='')
            ).filter(
                Q(intake_client_company__isnull=True) | 
                Q(intake_client_company='')
            )
        
        priority = filter_form.cleaned_data.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        patient_gender = filter_form.cleaned_data.get('patient_gender')
        if patient_gender:
            queryset = queryset.filter(patient_gender=patient_gender)
        
        referring_provider_name = filter_form.cleaned_data.get('referring_provider_name')
        if referring_provider_name:
            queryset = queryset.filter(
                referring_provider_name__icontains=referring_provider_name
            )
        
        intake_client_company = filter_form.cleaned_data.get('intake_client_company')
        if intake_client_company:
            queryset = queryset.filter(
                intake_client_company__icontains=intake_client_company
            )
    
    queryset = queryset.order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="referrals_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header with individual database fields
    field_names = [
        'Email ID', 'Patient Name', 'Order Number', 'Priority', 'Status',
        'Patient DOB', 'Patient DOI', 'Patient Gender', 'Patient Phone',
        'Referring Provider', 'Referring Provider NPI', 'Client Company',
        'Adjuster Name', 'Adjuster Email', 'Created Date'
    ]
    writer.writerow(field_names)
    
    # Write data using individual database fields
    for referral in queryset:
        # Determine status based on is_processed logic
        status = 'Processed' if referral.is_processed else 'Unprocessed'
        
        writer.writerow([
            referral.email_id,
            referral.patient_name or '',
            referral.order_number or '',
            referral.priority or '',
            status,
            referral.patient_dob or '',
            referral.patient_doi or '',
            referral.get_patient_gender_display() if referral.patient_gender else '',
            referral.patient_phone or '',
            referral.referring_provider_name or '',
            referral.referring_provider_npi or '',
            referral.intake_client_company or '',
            referral.intake_adjuster_name or '',
            referral.intake_adjuster_email or '',
            referral.created_at.strftime('%Y-%m-%d %H:%M:%S') if referral.created_at else '',
        ])
    
    return response


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
    
    # Check if referral has valid coordinates and convert to float
    try:
        ref_lat = float(referral.latitude) if referral.latitude is not None else None
        ref_lon = float(referral.longitude) if referral.longitude is not None else None
    except (ValueError, TypeError):
        ref_lat = None
        ref_lon = None
    
    if ref_lat is not None and ref_lon is not None:
        all_providers = Provider.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        enriched = []
        
        for p in all_providers:
            try:
                # Convert provider coordinates to float
                p_lat = float(p.latitude) if p.latitude is not None else None
                p_lon = float(p.longitude) if p.longitude is not None else None
                
                if p_lat is None or p_lon is None:
                    continue
                    
                distance = _haversine(ref_lat, ref_lon, p_lat, p_lon)
                p.distance = distance
                enriched.append(p)
            except (ValueError, TypeError):
                # Skip providers with invalid coordinates
                continue
                
        providers = sorted(enriched, key=lambda x: x.distance)[:10]
    
    return render(request, 'referrals/provider_selection.html', {
        'referral': referral,
        'providers': providers,
    })


@require_POST
def assign_provider(request, pk):
    """Assign a provider to a referral."""
    referral = get_object_or_404(Referral, pk=pk)
    provider_id = request.POST.get('provider_id')
    
    if not provider_id:
        messages.error(request, 'No provider selected.')
        return redirect('provider_selection', pk=referral.pk)
    
    try:
        provider = Provider.objects.get(id=provider_id)
        referral.assigned_provider = provider_id
        referral.save()
        
        messages.success(
            request, 
            f'Provider "{provider.dba_name_billing_name}" has been assigned to referral "{referral.email_id}".'
        )
        return redirect('referral_detail', pk=referral.pk)
        
    except Provider.DoesNotExist:
        messages.error(request, 'Selected provider not found.')
        return redirect('provider_selection', pk=referral.pk)
    except Exception as e:
        messages.error(request, f'Error assigning provider: {str(e)}')
        return redirect('provider_selection', pk=referral.pk)
