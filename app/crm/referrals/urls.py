from django.urls import path
from . import views

urlpatterns = [
    path('', views.referral_list, name='referral_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('referral/<int:pk>/', views.referral_detail, name='referral_detail'),
    path('referral/<int:pk>/providers/', views.provider_selection, name='provider_selection'),
    path('referral/<int:pk>/assign-provider/', views.assign_provider, name='assign_provider'),
    path('referral/create/', views.referral_create, name='referral_create'),
    path('referral/<int:pk>/delete/', views.ReferralDeleteView.as_view(), name='referral_delete'),
    path('referral/bulk-action/', views.referral_bulk_action, name='referral_bulk_action'),
    path('referral/export/', views.referral_export, name='referral_export'),
]
