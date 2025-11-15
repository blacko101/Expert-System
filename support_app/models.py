# support_app/models.py
from django.db import models
from django.contrib.auth import get_user_model

class Case(models.Model):
    STATUS_CHOICES = [('new','New'),('diag','Diagnosed'),('closed','Closed')]
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    symptoms = models.JSONField(help_text="Input facts provided by user")
    diagnoses = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Case {self.id} ({self.status})"
