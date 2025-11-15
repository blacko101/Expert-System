# support_app/urls.py
from django.urls import path
from .views import DiagnoseView

app_name = 'support_app'

urlpatterns = [
    path('diagnose/', DiagnoseView.as_view(), name='diagnose'),
]
