from django.urls import path
from . import views

urlpatterns = [
    path('', views.referral_list, name='referral_list'),
    path('referral/<int:pk>/', views.referral_detail, name='referral_detail'),
    path('referral/<int:pk>/providers/', views.provider_selection, name='provider_selection'),
]
