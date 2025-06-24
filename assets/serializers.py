from rest_framework import serializers
from django.utils import timezone
from .models import Asset, Notification, Violation

class AssetSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()
    is_service_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'description', 'service_time', 'expiration_time',
            'is_serviced', 'is_expired', 'is_service_overdue', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('service_time') and data.get('expiration_time'):
            if data['service_time'] >= data['expiration_time']:
                raise serializers.ValidationError(
                    "Service time must be before expiration time"
                )
        
        # Validate that times are in the future for new assets
        if not self.instance:  # Creating new asset
            now = timezone.now()
            if data.get('service_time') and data['service_time'] <= now:
                raise serializers.ValidationError(
                    "Service time must be in the future"
                )
            if data.get('expiration_time') and data['expiration_time'] <= now:
                raise serializers.ValidationError(
                    "Expiration time must be in the future"
                )
        
        return data


class NotificationSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'asset', 'asset_name', 'notification_type', 
            'message', 'sent_at'
        ]
        read_only_fields = ['sent_at']


class ViolationSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    
    class Meta:
        model = Violation
        fields = [
            'id', 'asset', 'asset_name', 'violation_type', 
            'description', 'created_at'
        ]
        read_only_fields = ['created_at']


class CheckResultSerializer(serializers.Serializer):
    notifications_created = serializers.IntegerField()
    violations_created = serializers.IntegerField()
    message = serializers.CharField()
    details = serializers.DictField()