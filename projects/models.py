from django.db import models
from accounts.models import User


class Project(models.Model):
    """Main project model for thesis writing projects"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("researching", "Researching"),
        ("outlined", "Outlined"),
        ("writing", "Writing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
        help_text="User who owns this project"
    )
    topic = models.CharField(
        max_length=500,
        help_text="Research topic or thesis title"
    )
    citation_style = models.CharField(
        max_length=50,
        default="APA",
        help_text="Citation style (APA, MLA, Chicago, etc.)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Current status of the project"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.topic} - {self.get_status_display()}"

    @property
    def total_sources(self):
        """Get total number of sources for this project"""
        return self.sources.count()

    @property
    def total_sections(self):
        """Get total number of written sections"""
        return self.sections.count()


class Source(models.Model):
    """Research source model for storing academic sources"""

    SOURCE_TYPE_CHOICES = [
        ("academic", "Academic Paper"),
        ("book", "Book"),
        ("article", "Article"),
        ("website", "Website"),
        ("report", "Report"),
        ("other", "Other"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sources",
        help_text="Project this source belongs to"
    )
    title = models.CharField(max_length=500, help_text="Title of the source")
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default="academic",
        help_text="Type of source"
    )
    authors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of authors"
    )
    publication_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year of publication"
    )
    url = models.URLField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="URL of the source"
    )
    doi = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="DOI identifier"
    )
    abstract = models.TextField(
        null=True,
        blank=True,
        help_text="Abstract of the source"
    )
    key_findings = models.TextField(
        null=True,
        blank=True,
        help_text="Key findings extracted from the source"
    )
    summary = models.TextField(
        null=True,
        blank=True,
        help_text="AI-generated summary of the source"
    )
    full_content = models.TextField(
        null=True,
        blank=True,
        help_text="Full content scraped from the source"
    )
    relevance_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Relevance score (0.0 to 1.0)"
    )
    relevance_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for relevance score"
    )
    citation_text = models.TextField(
        null=True,
        blank=True,
        help_text="Formatted citation in project citation style"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sources"
        verbose_name = "Source"
        verbose_name_plural = "Sources"
        ordering = ["-relevance_score", "-created_at"]
        indexes = [
            models.Index(fields=["project", "-relevance_score"]),
            models.Index(fields=["source_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_source_type_display()})"


class Research(models.Model):
    """Research results model linked to a project"""

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="research",
        help_text="Project this research belongs to"
    )
    research_summary = models.TextField(
        help_text="Overall research summary and main themes"
    )
    research_gaps = models.TextField(
        null=True,
        blank=True,
        help_text="Identified research gaps"
    )
    recommendations = models.TextField(
        null=True,
        blank=True,
        help_text="Recommended research directions"
    )
    total_sources_found = models.IntegerField(
        default=0,
        help_text="Total number of sources found"
    )
    pdf_sources_count = models.IntegerField(
        default=0,
        help_text="Number of PDF sources found"
    )
    web_sources_count = models.IntegerField(
        default=0,
        help_text="Number of web sources found"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "research"
        verbose_name = "Research"
        verbose_name_plural = "Research"

    def __str__(self):
        return f"Research for {self.project.topic}"


class Outline(models.Model):
    """Outline model for storing thesis outline structure"""

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="outline",
        help_text="Project this outline belongs to"
    )
    structure_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full outline structure data in JSON format"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "outlines"
        verbose_name = "Outline"
        verbose_name_plural = "Outlines"

    def __str__(self):
        return f"Outline for {self.project.topic}"


class OutlineSection(models.Model):
    """Outline section model for storing individual sections in the outline"""

    outline = models.ForeignKey(
        Outline,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text="Outline this section belongs to"
    )
    section_title = models.CharField(
        max_length=500,
        help_text="Title of the section"
    )
    section_type = models.CharField(
        max_length=100,
        help_text="Type of section (introduction, literature_review, etc.)"
    )
    word_count = models.IntegerField(
        default=0,
        help_text="Target word count for this section"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order of the section in the outline"
    )
    parent_section = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subsections",
        help_text="Parent section (null for top-level sections)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "outline_sections"
        verbose_name = "Outline Section"
        verbose_name_plural = "Outline Sections"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["outline", "order"]),
            models.Index(fields=["parent_section"]),
        ]

    def __str__(self):
        return f"{self.section_title} (Order: {self.order})"

    @property
    def is_top_level(self):
        """Check if this is a top-level section"""
        return self.parent_section is None


class Section(models.Model):
    """Written section model for storing completed thesis sections"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text="Project this section belongs to"
    )
    outline_section = models.ForeignKey(
        OutlineSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="written_sections",
        help_text="Reference to the outline section this was based on"
    )
    section_title = models.CharField(
        max_length=500,
        help_text="Title of the section"
    )
    section_type = models.CharField(
        max_length=100,
        help_text="Type of section"
    )
    content = models.TextField(
        help_text="Full content in MDX format"
    )
    word_count = models.IntegerField(
        default=0,
        help_text="Actual word count of the content"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order of the section"
    )
    parent_section = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subsections",
        help_text="Parent section (null for top-level sections)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sections"
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["project", "order"]),
            models.Index(fields=["parent_section"]),
            models.Index(fields=["section_type"]),
        ]

    def __str__(self):
        return f"{self.section_title} ({self.word_count} words)"

    @property
    def is_top_level(self):
        """Check if this is a top-level section"""
        return self.parent_section is None

    @property
    def total_word_count(self):
        """Get total word count including subsections"""
        total = self.word_count
        for subsection in self.subsections.all():
            total += subsection.total_word_count
        return total
