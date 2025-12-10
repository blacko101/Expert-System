"""
URL configuration for expert_support project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('support_app.api.urls')),
]