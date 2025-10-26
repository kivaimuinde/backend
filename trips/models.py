from django.db import models
from django.conf import settings

class Trip(models.Model):
    CYCLE_CHOICES = [
        ('70/8', '70 hours / 8 days'),
        ('60/7', '60 hours / 7 days'),
    ]

    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    created_at = models.DateTimeField(auto_now_add=True)

    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used_hours = models.FloatField(default=0.0)

    cycle = models.CharField(
        max_length=10,
        choices=CYCLE_CHOICES,
        default='70/8'
    )
    fuel_stop_every_miles = models.IntegerField(default=1000)
    pickup_time_minutes = models.IntegerField(default=60)
    dropoff_time_minutes = models.IntegerField(default=60)

    route_distance_miles = models.FloatField(blank=True, null=True)
    route_duration_seconds = models.IntegerField(blank=True, null=True)
    route_polyline = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.pickup_location.title()} → {self.dropoff_location.title()} by {self.driver.username}"

        
class ELDLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    grid = models.JSONField(blank=True, null=True)

    miles_today = models.FloatField(default=0.0)
    driving_hours = models.FloatField(default=0.0)
    on_duty_hours = models.FloatField(default=0.0)
    sleeper_hours = models.FloatField(default=0.0)
    off_duty_hours = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ELD Log {self.date} for Trip {self.trip.id}"
