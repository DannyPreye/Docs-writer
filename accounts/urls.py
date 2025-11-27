from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema

from accounts.serializers import MyTokenObtainPairSerializer
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),

    path("login/", TokenObtainPairView.as_view(serializer_class=MyTokenObtainPairSerializer), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.update_profile_view, name="update_profile"),
    path("change-password/", views.change_password_view, name="change_password"),
    path("resend-verification-email/", views.resend_verification_email_view, name="resend_verification_email"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
]

