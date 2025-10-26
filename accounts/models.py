from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_driver = models.BooleanField(default=True)
    cdl_number = models.CharField(max_length=50, blank=True, null=True)
    home_terminal = models.CharField(max_length=200, blank=True, null=True)
    time_zone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return self.username
