"""
URL Configuration for API endpoints
"""
from django.urls import path
from . import views

urlpatterns = [
    # System endpoints
    path('system/variables', views.get_system_variables, name='system_variables'),
    path('health', views.health_check, name='health_check'),
    
    # Chatbot endpoints
    path('chatbot/input', views.chatbot_input, name='chatbot_input'),
    
    # Diagnosis endpoints
    path('diagnosis/run', views.run_diagnosis_endpoint, name='run_diagnosis'),
    
    # Rules endpoints
    path('rules', views.get_rules, name='get_rules'),
]