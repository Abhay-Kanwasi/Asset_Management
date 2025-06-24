from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Asset(models.Model):
    name = models.CharField(
        max_length=200, 
        validators=[MinLengthValidator(2)],
        help_text="Name of the asset"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Detailed description of the asset"
    )
    service_time = models.DateTimeField(
        help_text="When the asset needs to be serviced"
    )
    expiration_time = models.DateTimeField(
        help_text="When the asset expires"
    )
    is_serviced = models.BooleanField(
        default=False,
        help_text="Whether the asset has been serviced"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service_time']),
            models.Index(fields=['expiration_time']),
            models.Index(fields=['is_serviced']),
        ]

    def __str__(self):
        return f"{self.name} (Service: {self.service_time}, Expires: {self.expiration_time})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.service_time and self.expiration_time:
            if self.service_time >= self.expiration_time:
                raise ValidationError("Service time must be before expiration time")

    @property
    def is_expired(self):
        return timezone.now() > self.expiration_time

    @property
    def is_service_overdue(self):
        return timezone.now() > self.service_time and not self.is_serviced


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('service', 'Service Reminder'),
        ('expiration', 'Expiration Reminder'),
    ]
    
    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['asset', 'notification_type']),
            models.Index(fields=['sent_at']),
        ]
        # Prevent duplicate notifications for same asset and type within a short time
        constraints = [
            models.UniqueConstraint(
                fields=['asset', 'notification_type'],
                name='unique_notification_per_asset_type'
            )
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.asset.name}"


class Violation(models.Model):
    VIOLATION_TYPES = [
        ('expired', 'Asset Expired'),
        ('not_serviced', 'Service Overdue'),
    ]
    
    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name='violations'
    )
    violation_type = models.CharField(
        max_length=20, 
        choices=VIOLATION_TYPES
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset', 'violation_type']),
            models.Index(fields=['created_at']),
        ]
        # Prevent duplicate violations for same asset and type
        constraints = [
            models.UniqueConstraint(
                fields=['asset', 'violation_type'],
                name='unique_violation_per_asset_type'
            )
        ]

    def __str__(self):
        return f"{self.get_violation_type_display()} for {self.asset.name}"
