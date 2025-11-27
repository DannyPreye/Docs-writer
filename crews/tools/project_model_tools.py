import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from asgiref.sync import async_to_sync, sync_to_async
from crewai.tools import BaseTool
from django.db import transaction
from django.utils import timezone

from projects.models import Outline, OutlineSection, Project, Research, Section, Source

ProjectPayload = Union[str, Dict[str, Any]]


class BaseProjectTool(BaseTool):
    """Base tool with helpers for parsing payloads and fetching projects."""

    async def _arun(self, payload: ProjectPayload = None, **kwargs) -> str:
        raw_payload: Optional[ProjectPayload]
        raw_payload = payload if payload is not None else kwargs or None
        if raw_payload is None:
            raise ValueError("Payload is required.")
        parsed_payload = self._parse_payload(raw_payload)
        return await self._execute_async(parsed_payload)

    def _run(self, payload: ProjectPayload = None, **kwargs) -> str:
        raw_payload: Optional[ProjectPayload]
        raw_payload = payload if payload is not None else kwargs or None
        if raw_payload is None:
            raise ValueError("Payload is required.")
        parsed_payload = self._parse_payload(raw_payload)
        return self._execute(parsed_payload)

    def _execute(self, payload: Dict[str, Any]) -> str:
        raise NotImplementedError

    async def _execute_async(self, payload: Dict[str, Any]) -> str:
        return await sync_to_async(self._execute, thread_sensitive=True)(payload)

    def _parse_payload(self, payload: ProjectPayload) -> Dict[str, Any]:
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON payload: {exc}") from exc
        if isinstance(payload, dict):
            return payload
        raise ValueError("Payload must be a JSON string or dictionary.")

    def _get_project(self, payload: Dict[str, Any]) -> Project:
        project_id = payload.get("project_id")
        if not project_id:
            raise ValueError("`project_id` is required.")
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist as exc:
            raise ValueError(f"Project with id {project_id} not found.") from exc

    def _validate_status(self, status: Optional[str]) -> Optional[str]:
        if status is None:
            return None
        valid_statuses = {choice[0] for choice in Project.STATUS_CHOICES}
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Valid options: {', '.join(valid_statuses)}"
            )
        return status

    @staticmethod
    def _in_async_context() -> bool:
        try:
            loop = asyncio.get_running_loop()
            return loop.is_running()
        except RuntimeError:
            return False


class ProjectLookupTool(BaseProjectTool):
    """Tool to fetch project details for validation or context."""

    name: str = "project_lookup_tool"
    description: str = (
        "Use this tool to validate that a project exists and fetch its basic information. "
        "Input must include `project_id`. Returns project metadata such as topic, citation_style, "
        "status, and timestamps."
    )

    def _execute(self, payload: Dict[str, Any]) -> str:
        project = self._get_project(payload)
        return json.dumps(
            {
                "project_id": project.id,
                "topic": project.topic,
                "citation_style": project.citation_style,
                "status": project.status,
                "total_sources": project.total_sources,
                "total_sections": project.total_sections,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }
        )


class ProjectStatusUpdateTool(BaseProjectTool):
    """Tool to update project status explicitly."""

    name: str = "project_status_update_tool"
    description: str = (
        "Update the status of a project. Provide `project_id` and `status` "
        "(draft|researching|outlined|writing|completed|failed). Optionally include "
        "`note` for context."
    )

    def _execute(self, payload: Dict[str, Any]) -> str:
        project = self._get_project(payload)
        status = self._validate_status(payload.get("status"))
        if not status:
            raise ValueError("`status` is required.")
        project.status = status
        project.updated_at = timezone.now()
        project.save(update_fields=["status", "updated_at"])
        note = payload.get("note")
        result = f"Project {project.id} status updated to {status}."
        if note:
            result += f" Note: {note}"
        return result


class ResearchSaveTool(BaseProjectTool):
    """Tool to persist research summaries and sources."""

    name: str = "project_research_save_tool"
    description: str = (
        "Persist research output for a project. Provide `project_id`, `research` object "
        "(research_summary, research_gaps, recommendations, total_sources_found, "
        "pdf_sources_count, web_sources_count) and `sources` list. "
        "Automatically updates project status to `researching` unless overridden via `status`."
    )

    default_status: str = "researching"

    @transaction.atomic
    def _execute(self, payload: Dict[str, Any]) -> str:
        print("payload_________\n\n\n", payload)
        project = self._get_project(payload)
        research_data = payload.get("research") or {}
        sources_data = payload.get("sources") or []
        clear_existing = payload.get("clear_existing_sources", True)

        if not research_data.get("research_summary"):
            raise ValueError("`research.research_summary` is required.")

        Research.objects.update_or_create(
            project=project,
            defaults={
                "research_summary": research_data.get("research_summary", ""),
                "research_gaps": research_data.get("research_gaps", ""),
                "recommendations": research_data.get("recommendations", ""),
                "total_sources_found": research_data.get("total_sources_found", 0),
                "pdf_sources_count": research_data.get("pdf_sources_count", 0),
                "web_sources_count": research_data.get("web_sources_count", 0),
            },
        )

        if clear_existing:
            project.sources.all().delete()

        new_sources: List[Source] = []
        for source in sources_data:
            new_sources.append(
                Source(
                    project=project,
                    title=source.get("title", "Untitled Source"),
                    source_type=source.get("source_type", "other"),
                    authors=source.get("authors") or [],
                    publication_year=source.get("publication_year"),
                    url=source.get("url"),
                    doi=source.get("doi"),
                    abstract=source.get("abstract"),
                    key_findings=source.get("key_findings"),
                    summary=source.get("summary"),
                    full_content=source.get("full_content"),
                    relevance_score=source.get("relevance_score"),
                    relevance_reason=source.get("relevance_reason"),
                    citation_text=source.get("citation_text"),
                )
            )

        if new_sources:
            Source.objects.bulk_create(new_sources)

        status = self._validate_status(payload.get("status")) or self.default_status
        project.status = status
        project.updated_at = timezone.now()
        project.save(update_fields=["status", "updated_at"])

        return (
            f"Research data saved for project {project.id}. "
            f"{len(new_sources)} sources stored. Status set to {status}."
        )


class OutlineSaveTool(BaseProjectTool):
    """Tool to persist outline structure."""

    name: str = "project_outline_save_tool"
    description: str = (
        "Persist outline structure for a project. Provide `project_id`, optional `structure_data` "
        "JSON, and `sections` list that follows the OutlineResult schema. "
        "Automatically updates project status to `outlined` unless overridden."
    )

    default_status: str = "outlined"

    @transaction.atomic
    def _execute(self, payload: Dict[str, Any]) -> str:
        project = self._get_project(payload)
        structure_data = payload.get("structure_data") or {}
        sections_data = payload.get("sections") or []

        outline, _ = Outline.objects.update_or_create(
            project=project,
            defaults={"structure_data": structure_data},
        )

        outline.sections.all().delete()

        created_sections = self._create_outline_sections(outline, sections_data)

        status = self._validate_status(payload.get("status")) or self.default_status
        project.status = status
        project.updated_at = timezone.now()
        project.save(update_fields=["status", "updated_at"])

        return (
            f"Outline saved for project {project.id}. "
            f"{created_sections} outline sections created. Status set to {status}."
        )

    def _create_outline_sections(
        self,
        outline: Outline,
        sections: List[Dict[str, Any]],
        parent: Optional[OutlineSection] = None,
    ) -> int:
        count = 0
        for index, section_entry in enumerate(sections, 1):
            section_payload = section_entry.get("section") or section_entry
            subsections_payload = section_entry.get("subsections") or []
            title = (
                section_payload.get("section_title")
                or section_payload.get("title")
                or "Untitled Section"
            )
            outline_section = OutlineSection.objects.create(
                outline=outline,
                section_title=title,
                section_type=section_payload.get("section_type")
                or section_payload.get("type")
                or "section",
                word_count=section_payload.get("word_count", 0),
                order=section_payload.get("order", index),
                parent_section=parent,
            )
            count += 1
            if subsections_payload:
                count += self._create_outline_sections(
                    outline, subsections_payload, outline_section
                )
        return count


class SectionSaveTool(BaseProjectTool):
    """Tool to persist written section content."""

    name: str = "project_section_save_tool"
    description: str = (
        "Persist written sections for a project. Provide `project_id`, `sections` list with fields "
        "(`section_title`, `section_type`, `content`, `word_count`, `order`, optional "
        "`outline_section_id`, `parent_section_id`, `subsections`). "
        "Set `clear_existing` to true to replace current sections. "
        "Automatically updates status to `writing`, or to `completed` when `mark_completed` is true."
    )

    default_status: str = "writing"

    @transaction.atomic
    def _execute(self, payload: Dict[str, Any]) -> str:
        project = self._get_project(payload)
        sections_data = payload.get("sections") or []
        if not sections_data:
            raise ValueError("`sections` list is required.")

        clear_existing = payload.get("clear_existing", False)
        if clear_existing:
            project.sections.all().delete()

        created_sections = self._create_sections(project, sections_data)

        status = payload.get("status")
        if payload.get("mark_completed"):
            status = "completed"
        status = self._validate_status(status) or self.default_status
        project.status = status
        project.updated_at = timezone.now()
        project.save(update_fields=["status", "updated_at"])

        return (
            f"{created_sections} section(s) saved for project {project.id}. "
            f"Status set to {status}."
        )

    def _create_sections(
        self,
        project: Project,
        sections: List[Dict[str, Any]],
        parent: Optional[Section] = None,
    ) -> int:
        count = 0
        for index, section_payload in enumerate(sections, 1):
            subsections_payload = section_payload.get("subsections") or []
            section = Section.objects.create(
                project=project,
                outline_section_id=section_payload.get("outline_section_id"),
                section_title=section_payload.get("section_title", "Untitled Section"),
                section_type=section_payload.get("section_type", "section"),
                content=section_payload.get("content", ""),
                word_count=section_payload.get("word_count", 0),
                order=section_payload.get("order", index),
                parent_section=parent
                or Section.objects.filter(id=section_payload.get("parent_section_id")).first(),
            )
            count += 1
            if subsections_payload:
                count += self._create_sections(project, subsections_payload, section)
        return count
from crewai.tools import BaseTool
from projects.models import Project



