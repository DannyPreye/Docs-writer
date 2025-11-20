from django.contrib import admin
from .models import Project, Source, Research, Outline, OutlineSection, Section


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin configuration for Project model"""
    list_display = ("topic", "user", "citation_style", "status", "total_sources", "total_sections", "created_at")
    list_filter = ("status", "citation_style", "created_at")
    search_fields = ("topic", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at", "total_sources", "total_sections")
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("user", "topic", "citation_style", "status")
        }),
        ("Statistics", {
            "fields": ("total_sources", "total_sections")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    """Admin configuration for Source model"""
    list_display = ("title", "project", "source_type", "relevance_score", "publication_year", "created_at")
    list_filter = ("source_type", "created_at")
    search_fields = ("title", "project__topic", "authors")
    readonly_fields = ("created_at",)
    ordering = ("-relevance_score", "-created_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("project", "title", "source_type", "authors", "publication_year")
        }),
        ("Source Details", {
            "fields": ("url", "doi", "abstract", "citation_text")
        }),
        ("Content", {
            "fields": ("key_findings", "summary", "full_content")
        }),
        ("Relevance", {
            "fields": ("relevance_score", "relevance_reason")
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    """Admin configuration for Research model"""
    list_display = ("project", "total_sources_found", "pdf_sources_count", "web_sources_count", "created_at")
    search_fields = ("project__topic", "research_summary")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Project", {
            "fields": ("project",)
        }),
        ("Research Summary", {
            "fields": ("research_summary", "research_gaps", "recommendations")
        }),
        ("Statistics", {
            "fields": ("total_sources_found", "pdf_sources_count", "web_sources_count")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(Outline)
class OutlineAdmin(admin.ModelAdmin):
    """Admin configuration for Outline model"""
    list_display = ("project", "created_at", "updated_at")
    search_fields = ("project__topic",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Project", {
            "fields": ("project",)
        }),
        ("Structure Data", {
            "fields": ("structure_data",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(OutlineSection)
class OutlineSectionAdmin(admin.ModelAdmin):
    """Admin configuration for OutlineSection model"""
    list_display = ("section_title", "outline", "section_type", "word_count", "order", "parent_section", "is_top_level")
    list_filter = ("section_type", "outline")
    search_fields = ("section_title", "outline__project__topic")
    readonly_fields = ("created_at", "is_top_level")
    ordering = ("outline", "order")

    fieldsets = (
        ("Basic Information", {
            "fields": ("outline", "section_title", "section_type", "order", "parent_section")
        }),
        ("Targets", {
            "fields": ("word_count",)
        }),
        ("Properties", {
            "fields": ("is_top_level",)
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """Admin configuration for Section model"""
    list_display = ("section_title", "project", "section_type", "word_count", "order", "parent_section", "is_top_level", "created_at")
    list_filter = ("section_type", "created_at")
    search_fields = ("section_title", "project__topic", "content")
    readonly_fields = ("created_at", "updated_at", "is_top_level", "total_word_count")
    ordering = ("project", "order")

    fieldsets = (
        ("Basic Information", {
            "fields": ("project", "outline_section", "section_title", "section_type", "order", "parent_section")
        }),
        ("Content", {
            "fields": ("content", "word_count")
        }),
        ("Properties", {
            "fields": ("is_top_level", "total_word_count")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )
