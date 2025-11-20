from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Project, Source, Research, Outline, Section
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    ProjectCreateSerializer,
    SourceSerializer,
    ResearchSerializer,
    OutlineSerializer,
    SectionSerializer,
)


class IsProjectOwner(permissions.BasePermission):
    """Permission to only allow owners of a project to access it"""

    def has_object_permission(self, request, view, obj):
        # For Project objects, check user directly
        if isinstance(obj, Project):
            return obj.user == request.user
        # For related objects (Source, Research, Outline, Section), check through project
        if hasattr(obj, 'project'):
            return obj.project.user == request.user
        return False

    def has_permission(self, request, view):
        # For nested viewsets, check project ownership via project_pk
        if hasattr(view, 'kwargs') and 'project_pk' in view.kwargs:
            try:
                project = Project.objects.get(id=view.kwargs['project_pk'])
                return project.user == request.user
            except Project.DoesNotExist:
                return False
        return True


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing projects"""

    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """Return only projects owned by the current user"""
        return Project.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return ProjectListSerializer
        elif self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @extend_schema(
        summary="List all projects",
        description="Get a list of all projects owned by the authenticated user",
        responses={200: ProjectListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new project",
        description="Create a new thesis writing project",
        request=ProjectCreateSerializer,
        responses={201: ProjectSerializer, 400: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                "Create Project Example",
                value={
                    "topic": "Prevalence of Poorly Fitting Dentures in Elderly Nigerians",
                    "citation_style": "APA",
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a project",
        description="Get detailed information about a specific project including sources, research, outline, and sections",
        responses={200: ProjectSerializer, 404: OpenApiTypes.OBJECT},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a project",
        description="Update project information (topic, citation_style, status)",
        request=ProjectSerializer,
        responses={200: ProjectSerializer, 400: OpenApiTypes.OBJECT},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update a project",
        description="Partially update project information",
        request=ProjectSerializer,
        responses={200: ProjectSerializer, 400: OpenApiTypes.OBJECT},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a project",
        description="Delete a project and all its associated data",
        responses={204: None, 404: OpenApiTypes.OBJECT},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Get project sources",
        description="Get all research sources for a project",
        responses={200: SourceSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def sources(self, request, pk=None):
        """Get all sources for a project"""
        project = self.get_object()
        sources = project.sources.all()
        serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get project research",
        description="Get research results for a project",
        responses={200: ResearchSerializer, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def research(self, request, pk=None):
        """Get research results for a project"""
        project = self.get_object()
        try:
            research = project.research
            serializer = ResearchSerializer(research)
            return Response(serializer.data)
        except Research.DoesNotExist:
            return Response(
                {"detail": "Research not found for this project"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Get project outline",
        description="Get outline structure for a project",
        responses={200: OutlineSerializer, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def outline(self, request, pk=None):
        """Get outline for a project"""
        project = self.get_object()
        try:
            outline = project.outline
            serializer = OutlineSerializer(outline)
            return Response(serializer.data)
        except Outline.DoesNotExist:
            return Response(
                {"detail": "Outline not found for this project"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Get project sections",
        description="Get all written sections for a project",
        responses={200: SectionSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def sections(self, request, pk=None):
        """Get all sections for a project"""
        project = self.get_object()
        sections = project.sections.filter(parent_section=None)  # Only top-level sections
        serializer = SectionSerializer(sections, many=True)
        return Response(serializer.data)


class SourceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing research sources"""

    serializer_class = SourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """Return sources for projects owned by the current user"""
        project_id = self.kwargs.get("project_pk")
        return Source.objects.filter(project_id=project_id, project__user=self.request.user)

    def perform_create(self, serializer):
        """Set project when creating a source"""
        project_id = self.kwargs.get("project_pk")
        project = Project.objects.get(id=project_id, user=self.request.user)
        serializer.save(project=project)

    @extend_schema(
        summary="List project sources",
        description="Get all research sources for a specific project",
        responses={200: SourceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a source",
        description="Add a new research source to a project",
        request=SourceSerializer,
        responses={201: SourceSerializer, 400: OpenApiTypes.OBJECT},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a source",
        description="Get detailed information about a specific source",
        responses={200: SourceSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a source",
        description="Update source information",
        request=SourceSerializer,
        responses={200: SourceSerializer, 400: OpenApiTypes.OBJECT},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a source",
        description="Remove a source from a project",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ResearchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing research results (read-only)"""

    serializer_class = ResearchSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """Return research for projects owned by the current user"""
        project_id = self.kwargs.get("project_pk")
        return Research.objects.filter(project_id=project_id, project__user=self.request.user)

    @extend_schema(
        summary="Get project research",
        description="Get research results for a specific project",
        responses={200: ResearchSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class OutlineViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing outlines (read-only)"""

    serializer_class = OutlineSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """Return outlines for projects owned by the current user"""
        project_id = self.kwargs.get("project_pk")
        return Outline.objects.filter(project_id=project_id, project__user=self.request.user)

    @extend_schema(
        summary="Get project outline",
        description="Get outline structure for a specific project",
        responses={200: OutlineSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class SectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing written sections"""

    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """Return sections for projects owned by the current user"""
        project_id = self.kwargs.get("project_pk")
        return Section.objects.filter(project_id=project_id, project__user=self.request.user)

    def perform_create(self, serializer):
        """Set project when creating a section"""
        project_id = self.kwargs.get("project_pk")
        project = Project.objects.get(id=project_id, user=self.request.user)
        serializer.save(project=project)

    @extend_schema(
        summary="List project sections",
        description="Get all written sections for a specific project",
        responses={200: SectionSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a section",
        description="Add a new written section to a project",
        request=SectionSerializer,
        responses={201: SectionSerializer, 400: OpenApiTypes.OBJECT},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a section",
        description="Get detailed information about a specific section including subsections",
        responses={200: SectionSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a section",
        description="Update section content and metadata",
        request=SectionSerializer,
        responses={200: SectionSerializer, 400: OpenApiTypes.OBJECT},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a section",
        description="Remove a section from a project",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
