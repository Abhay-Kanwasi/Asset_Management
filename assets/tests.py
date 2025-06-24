from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Asset, Notification, Violation


class AssetModelTestCase(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.service_time = self.now + timedelta(hours=1)
        self.expiration_time = self.now + timedelta(days=1)
        
    def test_asset_creation(self):
        asset = Asset.objects.create(
            name="Test Asset",
            description="Test Description",
            service_time=self.service_time,
            expiration_time=self.expiration_time
        )
        self.assertEqual(asset.name, "Test Asset")
        self.assertFalse(asset.is_serviced)
        self.assertFalse(asset.is_expired)
        self.assertFalse(asset.is_service_overdue)

    def test_asset_properties(self):
        # Test expired asset
        expired_asset = Asset.objects.create(
            name="Expired Asset",
            service_time=self.now - timedelta(hours=2),
            expiration_time=self.now - timedelta(hours=1)
        )
        self.assertTrue(expired_asset.is_expired)
        self.assertTrue(expired_asset.is_service_overdue)

    def test_asset_clean_validation(self):
        """Test model clean method validation"""
        asset = Asset(
            name="Invalid Asset",
            service_time=self.expiration_time,
            expiration_time=self.service_time
        )
        with self.assertRaises(ValidationError):
            asset.clean()

    def test_asset_str_representation(self):
        """Test string representation"""
        asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.service_time,
            expiration_time=self.expiration_time
        )
        expected_str = f"Test Asset (Service: {self.service_time}, Expires: {self.expiration_time})"
        self.assertEqual(str(asset), expected_str)

    def test_asset_edge_cases(self):
        """Test edge cases for asset properties"""
        # Asset exactly at current time
        exact_time_asset = Asset.objects.create(
            name="Exact Time Asset",
            service_time=self.now,
            expiration_time=self.now + timedelta(hours=1)
        )
        # Should be considered overdue
        self.assertTrue(exact_time_asset.is_service_overdue)

        # Asset with very close times
        close_times_asset = Asset.objects.create(
            name="Close Times Asset",
            service_time=self.now + timedelta(minutes=1),
            expiration_time=self.now + timedelta(minutes=2)
        )
        self.assertFalse(close_times_asset.is_expired)
        self.assertFalse(close_times_asset.is_service_overdue)

class NotificationModelTestCase(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.now + timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )

    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='Test message'
        )
        self.assertEqual(notification.asset, self.asset)
        self.assertEqual(notification.notification_type, 'service')

    def test_notification_str_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='Test message'
        )
        expected_str = f"Service Reminder for {self.asset.name}"
        self.assertEqual(str(notification), expected_str)

    def test_duplicate_notification_constraint(self):
        """Test unique constraint for notifications"""
        Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='First message'
        )
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                asset=self.asset,
                notification_type='service',
                message='Duplicate message'
            )

class ViolationModelTestCase(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.now - timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )

    def test_violation_creation(self):
        """Test violation creation"""
        violation = Violation.objects.create(
            asset=self.asset,
            violation_type='not_serviced',
            description='Test violation'
        )
        self.assertEqual(violation.asset, self.asset)
        self.assertEqual(violation.violation_type, 'not_serviced')

    def test_violation_str_representation(self):
        """Test violation string representation"""
        violation = Violation.objects.create(
            asset=self.asset,
            violation_type='not_serviced',
            description='Test violation'
        )
        expected_str = f"Service Overdue for {self.asset.name}"
        self.assertEqual(str(violation), expected_str)

    def test_duplicate_violation_constraint(self):
        """Test unique constraint for violations"""
        Violation.objects.create(
            asset=self.asset,
            violation_type='not_serviced',
            description='First violation'
        )
        with self.assertRaises(IntegrityError):
            Violation.objects.create(
                asset=self.asset,
                violation_type='not_serviced',
                description='Duplicate violation'
            )

class AssetAPITestCase(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        self.service_time = self.now + timedelta(hours=1)
        self.expiration_time = self.now + timedelta(days=1)
        
    def test_create_asset(self):
        data = {
            'name': 'Test Asset',
            'description': 'Test Description',
            'service_time': self.service_time.isoformat(),
            'expiration_time': self.expiration_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)

    def test_invalid_asset_creation(self):
        # Service time after expiration time
        data = {
            'name': 'Invalid Asset',
            'service_time': self.expiration_time.isoformat(),
            'expiration_time': self.service_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asset_with_past_times(self):
        """Test creating asset with past times (should fail)"""
        past_time = self.now - timedelta(hours=1)
        data = {
            'name': 'Past Asset',
            'service_time': past_time.isoformat(),
            'expiration_time': self.expiration_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asset_empty_name(self):
        """Test creating asset with empty name"""
        data = {
            'name': '',
            'service_time': self.service_time.isoformat(),
            'expiration_time': self.expiration_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asset_short_name(self):
        """Test creating asset with too short name"""
        data = {
            'name': 'A',
            'service_time': self.service_time.isoformat(),
            'expiration_time': self.expiration_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asset_invalid_datetime_format(self):
        """Test creating asset with invalid datetime format"""
        data = {
            'name': 'Test Asset',
            'service_time': 'invalid-datetime',
            'expiration_time': self.expiration_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_assets_empty(self):
        """Test getting all assets when none exist"""
        response = self.client.get('/api/assets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_single_asset_not_found(self):
        """Test getting non-existent asset"""
        response = self.client.get('/api/assets/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_asset_partial(self):
        """Test partial update of asset"""
        asset = Asset.objects.create(
            name="Original Asset",
            service_time=self.service_time,
            expiration_time=self.expiration_time
        )
        data = {'name': 'Updated Asset'}
        response = self.client.patch(f'/api/assets/{asset.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        asset.refresh_from_db()
        self.assertEqual(asset.name, 'Updated Asset')

    def test_update_nonexistent_asset(self):
        """Test updating non-existent asset"""
        data = {'name': 'Updated Asset'}
        response = self.client.put('/api/assets/999/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_asset(self):
        """Test deleting an asset"""
        asset = Asset.objects.create(
            name="To Delete",
            service_time=self.service_time,
            expiration_time=self.expiration_time
        )
        response = self.client.delete(f'/api/assets/{asset.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asset.objects.filter(id=asset.id).exists())

    def test_delete_nonexistent_asset(self):
        """Test deleting non-existent asset"""
        response = self.client.delete('/api/assets/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_asset_serviced(self):
        asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.service_time,
            expiration_time=self.expiration_time
        )
        response = self.client.post(f'/api/assets/{asset.id}/mark_serviced/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        asset.refresh_from_db()
        self.assertTrue(asset.is_serviced)

    def test_mark_nonexistent_asset_serviced(self):
        """Test marking non-existent asset as serviced"""
        response = self.client.post('/api/assets/999/mark_serviced/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class NotificationAPITestCase(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        self.asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.now + timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )

    def test_get_notifications_empty(self):
        """Test getting notifications when none exist"""
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_notifications_with_data(self):
        """Test getting notifications with data"""
        Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='Test notification'
        )
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_notifications_by_asset(self):
        """Test filtering notifications by asset"""
        asset2 = Asset.objects.create(
            name="Asset 2",
            service_time=self.now + timedelta(hours=2),
            expiration_time=self.now + timedelta(days=2)
        )
        Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='Notification 1'
        )
        Notification.objects.create(
            asset=asset2,
            notification_type='expiration',
            message='Notification 2'
        )
        
        response = self.client.get(f'/api/notifications/?asset={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_notifications_by_type(self):
        """Test filtering notifications by type"""
        Notification.objects.create(
            asset=self.asset,
            notification_type='service',
            message='Service notification'
        )
        
        response = self.client.get('/api/notifications/?type=service')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

class ViolationAPITestCase(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        self.asset = Asset.objects.create(
            name="Test Asset",
            service_time=self.now - timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )

    def test_get_violations_empty(self):
        """Test getting violations when none exist"""
        response = self.client.get('/api/violations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_violations_by_asset(self):
        """Test filtering violations by asset"""
        asset2 = Asset.objects.create(
            name="Asset 2",
            service_time=self.now - timedelta(hours=2),
            expiration_time=self.now - timedelta(hours=1)
        )
        Violation.objects.create(
            asset=self.asset,
            violation_type='not_serviced',
            description='Violation 1'
        )
        Violation.objects.create(
            asset=asset2,
            violation_type='expired',
            description='Violation 2'
        )
        
        response = self.client.get(f'/api/violations/?asset={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_violations_by_type(self):
        """Test filtering violations by type"""
        Violation.objects.create(
            asset=self.asset,
            violation_type='not_serviced',
            description='Not serviced violation'
        )
        
        response = self.client.get('/api/violations/?type=not_serviced')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

class ChecksAPITestCase(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        
    def test_run_checks_notifications(self):
        # Create asset that needs service reminder
        Asset.objects.create(
            name="Service Due Soon",
            service_time=self.now + timedelta(minutes=10),
            expiration_time=self.now + timedelta(days=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 1)
        self.assertEqual(Notification.objects.count(), 1)

    def test_run_checks_violations(self):
        # Create overdue asset
        Asset.objects.create(
            name="Overdue Asset",
            service_time=self.now - timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['violations_created'], 1)
        self.assertEqual(Violation.objects.count(), 1)

    def test_run_checks_no_actions_needed(self):
        """Test run checks when no actions are needed"""
        # Create asset with future times
        Asset.objects.create(
            name="Future Asset",
            service_time=self.now + timedelta(days=1),
            expiration_time=self.now + timedelta(days=2)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 0)
        self.assertEqual(response.data['violations_created'], 0)

    def test_run_checks_duplicate_prevention(self):
        """Test that duplicate notifications/violations are not created"""
        # Create asset that needs service reminder
        Asset.objects.create(
            name="Service Due Soon",
            service_time=self.now + timedelta(minutes=10),
            expiration_time=self.now + timedelta(days=1)
        )
        
        # First run
        response1 = self.client.post('/api/run-checks/')
        self.assertEqual(response1.data['notifications_created'], 1)
        
        # Second run - should not create duplicates
        response2 = self.client.post('/api/run-checks/')
        self.assertEqual(response2.data['notifications_created'], 0)
        
        # Total notifications should still be 1
        self.assertEqual(Notification.objects.count(), 1)

    def test_run_checks_edge_case_exactly_15_minutes(self):
        """Test asset exactly 15 minutes before service time"""
        Asset.objects.create(
            name="Exactly 15 Min Asset",
            service_time=self.now + timedelta(minutes=15),
            expiration_time=self.now + timedelta(days=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 1)

    def test_run_checks_edge_case_just_over_15_minutes(self):
        """Test asset just over 15 minutes before service time"""
        Asset.objects.create(
            name="Over 15 Min Asset",
            service_time=self.now + timedelta(minutes=16),
            expiration_time=self.now + timedelta(days=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 0)

    def test_run_checks_serviced_asset_no_violation(self):
        """Test that serviced assets don't create violations"""
        Asset.objects.create(
            name="Serviced Overdue Asset",
            service_time=self.now - timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1),
            is_serviced=True
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['violations_created'], 0)

    def test_run_checks_both_notifications_and_violations(self):
        """Test creating both notifications and violations in one run"""
        # Asset needing service reminder
        Asset.objects.create(
            name="Service Due Soon",
            service_time=self.now + timedelta(minutes=10),
            expiration_time=self.now + timedelta(days=1)
        )
        
        # Overdue asset
        Asset.objects.create(
            name="Overdue Asset",
            service_time=self.now - timedelta(hours=1),
            expiration_time=self.now + timedelta(days=1)
        )
        
        # Expired asset
        Asset.objects.create(
            name="Expired Asset",
            service_time=self.now - timedelta(hours=2),
            expiration_time=self.now - timedelta(hours=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 1)
        self.assertEqual(response.data['violations_created'], 2)

    @patch('assets.views.timezone.now')
    def test_run_checks_with_mocked_time(self, mock_now):
        """Test run checks with mocked current time"""
        fixed_time = timezone.now()
        mock_now.return_value = fixed_time
        
        Asset.objects.create(
            name="Mock Time Asset",
            service_time=fixed_time + timedelta(minutes=10),
            expiration_time=fixed_time + timedelta(days=1)
        )
        
        response = self.client.post('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notifications_created'], 1)

class EdgeCaseTestCase(APITestCase):
    def test_asset_with_same_service_and_expiration_time(self):
        """Test asset with same service and expiration time (should fail)"""
        same_time = timezone.now() + timedelta(hours=1)
        data = {
            'name': 'Same Time Asset',
            'service_time': same_time.isoformat(),
            'expiration_time': same_time.isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asset_with_very_long_name(self):
        """Test asset with very long name"""
        long_name = 'A' * 201  # Exceeds max_length of 200
        data = {
            'name': long_name,
            'service_time': (timezone.now() + timedelta(hours=1)).isoformat(),
            'expiration_time': (timezone.now() + timedelta(days=1)).isoformat()
        }
        response = self.client.post('/api/assets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination_with_many_assets(self):
        """Test pagination with many assets"""
        # Create 25 assets (more than default page size of 20)
        for i in range(25):
            Asset.objects.create(
                name=f"Asset {i}",
                service_time=timezone.now() + timedelta(hours=i+1),
                expiration_time=timezone.now() + timedelta(days=i+1)
            )
        
        response = self.client.get('/api/assets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])

    def test_invalid_http_methods(self):
        """Test invalid HTTP methods on endpoints"""
        # Try POST on detail endpoint (should be PUT/PATCH)
        response = self.client.post('/api/assets/1/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try DELETE on run-checks (should be POST)
        response = self.client.delete('/api/run-checks/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_concurrent_run_checks(self):
        """Test concurrent run checks calls"""
        Asset.objects.create(
            name="Concurrent Test Asset",
            service_time=timezone.now() + timedelta(minutes=10),
            expiration_time=timezone.now() + timedelta(days=1)
        )
        
        # Simulate concurrent calls
        response1 = self.client.post('/api/run-checks/')
        response2 = self.client.post('/api/run-checks/')
        
        # Both should succeed, but only one should create notification
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        total_notifications = response1.data['notifications_created'] + response2.data['notifications_created']
        self.assertEqual(total_notifications, 1)
        self.assertEqual(Notification.objects.count(), 1)