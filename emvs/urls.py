"""
URL configuration for Enhanced Merchant Verification System.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('merchant_verification.urls')),
    path('api/', include('merchant_verification.api.urls')),
]
