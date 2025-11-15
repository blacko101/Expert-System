# support_app/admin.py
from django.contrib import admin
from .models import Case

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('id','user','created_at','status')
    readonly_fields = ('created_at','updated_at')
    list_filter = ('status','created_at')
    search_fields = ('id',)
