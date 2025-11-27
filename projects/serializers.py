from django.conf import settings
from rest_framework import serializers
from projects.tasks import run_thesis_writing_flow
from .models import (
    Project,
    Source,
    Research,
    Outline,
    OutlineSection,
    Section,
)


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for research sources"""

    source_type_display = serializers.CharField(source="get_source_type_display", read_only=True)

    class Meta:
        model = Source
        fields = [
            "id",
            "title",
            "source_type",
            "source_type_display",
            "authors",
            "publication_year",
            "url",
            "doi",
            "abstract",
            "key_findings",
            "summary",
            "full_content",
            "relevance_score",
            "relevance_reason",
            "citation_text",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ResearchSerializer(serializers.ModelSerializer):
    """Serializer for research results"""

    class Meta:
        model = Research
        fields = [
            "id",
            "research_summary",
            "research_gaps",
            "recommendations",
            "total_sources_found",
            "pdf_sources_count",
            "web_sources_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OutlineSectionSerializer(serializers.ModelSerializer):
    """Serializer for outline sections with nested subsections"""

    subsections = serializers.SerializerMethodField()
    is_top_level = serializers.BooleanField(read_only=True)

    class Meta:
        model = OutlineSection
        fields = [
            "id",
            "section_title",
            "section_type",
            "word_count",
            "order",
            "parent_section",
            "is_top_level",
            "subsections",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_subsections(self, obj):
        """Get nested subsections"""
        subsections = obj.subsections.all()
        return OutlineSectionSerializer(subsections, many=True).data


class OutlineSerializer(serializers.ModelSerializer):
    """Serializer for outline structure"""

    sections = OutlineSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Outline
        fields = [
            "id",
            "structure_data",
            "sections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for written sections"""

    subsections = serializers.SerializerMethodField()
    is_top_level = serializers.BooleanField(read_only=True)
    total_word_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Section
        fields = [
            "id",
            "outline_section",
            "section_title",
            "section_type",
            "content",
            "word_count",
            "order",
            "parent_section",
            "is_top_level",
            "total_word_count",
            "subsections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_subsections(self, obj):
        """Get nested subsections"""
        subsections = obj.subsections.all()
        return SectionSerializer(subsections, many=True).data


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project list views"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_sources = serializers.IntegerField(read_only=True)
    total_sections = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "topic",
            "citation_style",
            "status",
            "status_display",
            "total_sources",
            "total_sections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new projects"""

    class Meta:
        model = Project
        fields = [
            "topic",
            "citation_style",
        ]

    def create(self, validated_data):
        """Create project and set user from request context"""
        validated_data["user"] = self.context["request"].user
        project = super().create(validated_data)

        try:
            print("Running thesis writing flow")

            run_thesis_writing_flow.delay(project.id)
        except Exception as e:
            print(f"Error running thesis writing flow: {e}")
        return project


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer with nested relationships"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_sources = serializers.IntegerField(read_only=True)
    total_sections = serializers.IntegerField(read_only=True)
    sources = SourceSerializer(many=True, read_only=True)
    research = ResearchSerializer(read_only=True)
    outline = OutlineSerializer(read_only=True)
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "user",
            "topic",
            "citation_style",
            "status",
            "status_display",
            "total_sources",
            "total_sections",
            "sources",
            "research",
            "outline",
            "sections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

