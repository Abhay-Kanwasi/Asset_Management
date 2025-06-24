import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Asset, Notification, Violation
from .serializers import (AssetSerializer, CheckResultSerializer,
                          NotificationSerializer, ViolationSerializer)

logger = logging.getLogger(__name__)

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    
    @swagger_auto_schema(
        operation_description="Mark an asset as serviced",
        responses={200: "Asset marked as serviced"}
    )
    @action(detail=True, methods=['post'])
    def mark_serviced(self, request, pk=None):
        asset = self.get_object()
        asset.is_serviced = True
        asset.save()
        return Response({
            'message': f'Asset {asset.name} marked as serviced',
            'asset': AssetSerializer(asset).data
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        queryset = Notification.objects.all()
        asset_id = self.request.query_params.get('asset', None)
        notification_type = self.request.query_params.get('type', None)
        
        if asset_id is not None:
            queryset = queryset.filter(asset=asset_id)
        if notification_type is not None:
            queryset = queryset.filter(notification_type=notification_type)
            
        return queryset


class ViolationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Violation.objects.all()
    serializer_class = ViolationSerializer
    
    def get_queryset(self):
        queryset = Violation.objects.all()
        asset_id = self.request.query_params.get('asset', None)
        violation_type = self.request.query_params.get('type', None)
        
        if asset_id is not None:
            queryset = queryset.filter(asset=asset_id)
        if violation_type is not None:
            queryset = queryset.filter(violation_type=violation_type)
            
        return queryset


@swagger_auto_schema(
    method='post',
    operation_description="Run periodic checks for asset notifications and violations",
    responses={
        200: CheckResultSerializer,
        500: "Internal server error"
    }
)
@api_view(['POST'])
def run_checks(request):
    """
    Periodic task to check for assets that need notifications or violations.
    
    This endpoint:
    1. Checks for assets within 15 minutes of service/expiration time
    2. Creates notifications for upcoming deadlines
    3. Creates violations for overdue assets
    """
    try:
        with transaction.atomic():
            now = timezone.now()
            reminder_threshold = now + timedelta(minutes=15)
            
            notifications_created = 0
            violations_created = 0
            details = {
                'notifications': [],
                'violations': []
            }
            
            # Get all assets that might need checking
            assets = Asset.objects.all()
            
            for asset in assets:
                # Check for service reminders (15 minutes before service time)
                if (asset.service_time > now and 
                    asset.service_time <= reminder_threshold and 
                    not asset.is_serviced):
                    
                    notification, created = Notification.objects.get_or_create(
                        asset=asset,
                        notification_type='service',
                        defaults={
                            'message': f'Service reminder: Asset "{asset.name}" needs service at {asset.service_time}'
                        }
                    )
                    if created:
                        notifications_created += 1
                        details['notifications'].append({
                            'asset': asset.name,
                            'type': 'service',
                            'time': asset.service_time.isoformat()
                        })
                
                # Check for expiration reminders (15 minutes before expiration)
                if (asset.expiration_time > now and 
                    asset.expiration_time <= reminder_threshold):
                    
                    notification, created = Notification.objects.get_or_create(
                        asset=asset,
                        notification_type='expiration',
                        defaults={
                            'message': f'Expiration reminder: Asset "{asset.name}" expires at {asset.expiration_time}'
                        }
                    )
                    if created:
                        notifications_created += 1
                        details['notifications'].append({
                            'asset': asset.name,
                            'type': 'expiration',
                            'time': asset.expiration_time.isoformat()
                        })
                
                # Check for service violations (service time passed and not serviced)
                if asset.service_time <= now and not asset.is_serviced:
                    violation, created = Violation.objects.get_or_create(
                        asset=asset,
                        violation_type='not_serviced',
                        defaults={
                            'description': f'Service overdue: Asset "{asset.name}" was due for service at {asset.service_time}'
                        }
                    )
                    if created:
                        violations_created += 1
                        details['violations'].append({
                            'asset': asset.name,
                            'type': 'not_serviced',
                            'due_time': asset.service_time.isoformat()
                        })
                
                # Check for expiration violations (expiration time passed)
                if asset.expiration_time <= now:
                    violation, created = Violation.objects.get_or_create(
                        asset=asset,
                        violation_type='expired',
                        defaults={
                            'description': f'Asset expired: Asset "{asset.name}" expired at {asset.expiration_time}'
                        }
                    )
                    if created:
                        violations_created += 1
                        details['violations'].append({
                            'asset': asset.name,
                            'type': 'expired',
                            'expired_time': asset.expiration_time.isoformat()
                        })
            
            result_data = {
                'notifications_created': notifications_created,
                'violations_created': violations_created,
                'message': f'Check completed. Created {notifications_created} notifications and {violations_created} violations.',
                'details': details
            }
            
            serializer = CheckResultSerializer(data=result_data)
            serializer.is_valid(raise_exception=True)
            logger.info('Run checks successfull.')
            return Response(serializer.data, status=status.HTTP_200_OK)
            
    except Exception as error:
        logger.error(f'Error during running checks: {str(error)}')
        return Response(
            {'error': f'Error running checks: {str(error)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )