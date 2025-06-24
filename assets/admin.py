from django.contrib import admin
from .models import Asset, Notification, Violation

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_time', 'expiration_time', 'is_serviced', 'is_expired', 'created_at']
    list_filter = ['is_serviced', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'notification_type', 'sent_at']
    list_filter = ['notification_type', 'sent_at']
    search_fields = ['asset__name', 'message']

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'violation_type', 'created_at']
    list_filter = ['violation_type', 'created_at']
    search_fields = ['asset__name', 'description']
