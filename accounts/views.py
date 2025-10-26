from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User as DjangoUser
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Allows:
      - GET /api/users/ → list (admin only)
      - GET /api/users/{id}/ → retrieve (self or admin)
      - POST /api/users/ → register (open to anyone)
      - PUT/PATCH (self or admin)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":  # Allow open registration
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = serializer.save(
            password=make_password(serializer.validated_data.get("password")),
            is_active=True
        )

        # Generate verification token and URL
        token = default_token_generator.make_token(user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{user.pk}/{token}/"

        # Send verification email
        if getattr(settings, "EMAIL_HOST", None):
            send_mail(
                subject="Verify your Spotter account",
                message=f"Hello {user.username},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(id=user.id)

class PasswordResetView(APIView):
    """
    POST /api/password-reset/
    Allows a user to reset their password given their username and a new password (with confirmation).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not username or not new_password or not confirm_password:
            return Response(
                {"error": "Username, new_password, and confirm_password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
            user.password = make_password(new_password)
            user.save()

            # Optional: send confirmation email
            if getattr(settings, "EMAIL_HOST", None):
                send_mail(
                    "Your Password Has Been Reset",
                    f"Hello {user.username},\n\nYour password has been successfully reset.",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )

            return Response({"success": "Password reset successful."})
        except User.DoesNotExist:
            return Response(
                {"error": "User with that username not found."},
                status=status.HTTP_404_NOT_FOUND
            )
