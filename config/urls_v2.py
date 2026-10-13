"""Isolated API v2 URLs; legacy production URL configuration is unchanged."""
from django.urls import include, path

urlpatterns = [
    path('api/v2/', include('tenancy_v2.urls')),
]
