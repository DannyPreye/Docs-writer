from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,
    SourceViewSet,
    ResearchViewSet,
    OutlineViewSet,
    SectionViewSet,
)

app_name = "projects"

# Create router and register viewsets
router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")

# Nested routes for project-related resources
nested_router = DefaultRouter()
nested_router.register(
    r"projects/(?P<project_pk>\d+)/sources",
    SourceViewSet,
    basename="project-source"
)
nested_router.register(
    r"projects/(?P<project_pk>\d+)/research",
    ResearchViewSet,
    basename="project-research"
)
nested_router.register(
    r"projects/(?P<project_pk>\d+)/outline",
    OutlineViewSet,
    basename="project-outline"
)
nested_router.register(
    r"projects/(?P<project_pk>\d+)/sections",
    SectionViewSet,
    basename="project-section"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(nested_router.urls)),
]

