from datetime import timedelta
from time import timezone
import uuid
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, VerificationToken
from config import settings


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Check if user is verified
        if not self.user.is_verified:
            raise serializers.ValidationError(
                {
                    "detail": "Your account is not verified. Please verify your email address before logging in."
                }
            )

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "is_verified": self.user.is_verified,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "created_at": self.user.created_at,
            "updated_at": self.user.updated_at,
        }

        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()

        # create verification token
        verification_token = VerificationToken.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(hours=24),
        )
        verification_token.save()

        # Todo:send verification email
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
class VerificationTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate_token(self, value):
        # get email from initial data
        email = self.initial_data.get("email")
        if not VerificationToken.objects.filter(email=email, token=value).exists():
            raise serializers.ValidationError("Invalid token.")
        return value

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Invalid email.")
        return value
    def validate(self, attrs):
        token = attrs.get("token")
        user_token = VerificationToken.objects.get(token=token)
        if user_token.expires_at < timezone.now():
            raise serializers.ValidationError("Token has expired.")
        return attrs
    def create(self, validated_data):
        token = validated_data.get("token")
        user_token = VerificationToken.objects.get(token=token)
        user = user_token.user
        user.is_verified = True
        user.save()
        user_token.delete()
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Invalid email.")
        return value
    def create(self, validated_data):
        email = validated_data.get("email")
        user = User.objects.get(email=email)
        # create verification token
        verification_token = VerificationToken.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(hours=24),
        )
        verification_token.save()
        # Todo:send verification email
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Invalid email.")
        return value
    def create(self, validated_data):
        email = validated_data.get("email")
        user = User.objects.get(email=email)
        # create password reset token
        password_reset_token = VerificationToken.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(hours=24),
        )
        password_reset_token.save()
        # Todo:send password reset email
        return user

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    def validate_token(self, value):
        if not VerificationToken.objects.filter(token=value).exists():
            raise serializers.ValidationError("Invalid token.")
        return value
    def create(self, validated_data):
       user = User.objects.get(email=validated_data.get("email"))
       user.set_password(validated_data.get("new_password"))
       user.save()
       return user


class PasswordResetForAuthenticatedUserSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data.get("new_password"))
        user.save()
        return user


class UpdateUserProfileSerializer(serializers.Serializer):
    """Serializer for updating user profile information"""

    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value):
        """Validate username uniqueness if provided"""
        if value:
            user = self.context['request'].user
            if User.objects.filter(username=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError("A user with this username already exists.")
        return value

    def update(self, instance, validated_data):
        """Update user profile fields"""
        # Update only provided fields (partial update support)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Return user data after update"""
        return UserProfileSerializer(instance).data
