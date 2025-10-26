from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'is_driver', 'cdl_number', 'home_terminal', 'time_zone'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'is_driver': {'required': False},
        }

    def create(self, validated_data):
        """Ensure password is hashed when creating new users."""
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.password = make_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Hash password on updates too (e.g., password reset)."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.password = make_password(password)
            user.save()
        return user
