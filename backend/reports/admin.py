<<<<<<< HEAD
# reports/admin.py
from django.contrib import admin
from .models import SavedReport, ReportExport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'is_public', 'created_at']
    list_filter = ['report_type', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['export_id', 'report_type', 'status', 'file_format', 'created_at']
    list_filter = ['status', 'report_type', 'file_format', 'created_at']
    search_fields = ['export_id']
    readonly_fields = ['created_at']
=======
from django.contrib import admin

# Register your models here.
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
