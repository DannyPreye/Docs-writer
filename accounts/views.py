from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    VerificationTokenSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetForAuthenticatedUserSerializer,
    ResendVerificationEmailSerializer,
    UpdateUserProfileSerializer,
)


@extend_schema(
    summary="Register a new user",
    description="Create a new user account with email and password",
    request=UserRegistrationSerializer,
    responses={201: UserRegistrationSerializer, 400: OpenApiTypes.OBJECT},
    examples=[
        OpenApiExample(
            "Registration Example",
            value={
                "email": "john@example.com",
                "password": "securepassword123",
                "confirm_password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
    ],
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(
    summary="Get user profile",
    description="Retrieve the authenticated user's profile information",
    responses={200: UserProfileSerializer},
    tags=["user"]
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    """Get user profile endpoint"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Verify email",
    description="Verify email using a verification token",
    request=VerificationTokenSerializer,
    responses={200: UserProfileSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def verify_email_view(request):
    """Verify email endpoint"""
    serializer = VerificationTokenSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {

                "message": "Email verified successfully",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Forgot password",
    description="Forgot password for a user",
    request=PasswordResetSerializer,
    responses={200: UserProfileSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def forgot_password_view(request):
    """Reset password endpoint"""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Password reset successfully",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Reset password",
    description="Reset password for a user",
    request=PasswordResetConfirmSerializer,
    responses={200: UserProfileSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def reset_password_view(request):
    """Reset password endpoint"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Password reset successfully",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Reset password for authenticated user",
    description="Reset password for an authenticated user",
    request=PasswordResetForAuthenticatedUserSerializer,
    responses={200: UserProfileSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """Reset password for authenticated user endpoint"""
    serializer = PasswordResetForAuthenticatedUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Password reset successfully",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    summary="Resend verification email",
    description="Resend verification email for a user",
    request=ResendVerificationEmailSerializer,
    responses={200: UserProfileSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def resend_verification_email_view(request):
    """Resend verification email endpoint"""
    serializer = ResendVerificationEmailSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        return Response(
            {
                "message": "Verification email resent successfully",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Update user profile",
    description="Update user profile information",
    request=UpdateUserProfileSerializer,
    responses={200: UserProfileSerializer},
    tags=["user"]
)
@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_profile_view(request):
    """Update user profile endpoint"""
    serializer = UpdateUserProfileSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


