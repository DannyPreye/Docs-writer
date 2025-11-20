from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_prefix = "api/v1"

urlpatterns = [
    path("admin/", admin.site.urls),

    # API Documentation
    path(f"{api_prefix}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(f"{api_prefix}/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(f"{api_prefix}/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # API Routes
    path(f"{api_prefix}/auth/", include("accounts.urls"), name="authentication"),
    path(f"{api_prefix}/projects/", include("projects.urls")),
]
