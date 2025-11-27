from crewai import Crew, Agent, Task, LLM
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os

load_dotenv()

from crews.tools.project_model_tools import (
    ProjectStatusUpdateTool,
    SectionSaveTool,
)


# Pydantic models for writing output
class Citation(BaseModel):
    """Citation information"""

    in_text: str = Field(description="In-text citation format, e.g., (Author, Year)")
    full_citation: str = Field(
        description="Full citation in the specified citation style"
    )
    source_id: str = Field(description="ID of the source being cited")
    page_number: str = Field(default="", description="Page number if applicable")


class SubsectionContent(BaseModel):
    """Content for a subsection"""

    section_title: str = Field(description="Title of the subsection")
    parent_section: str = Field(description="Name of the parent section")
    section_type: str = Field(description="Type of subsection")
    content: str = Field(description="Full comprehensive content in MDX format")
    word_count: int = Field(description="Actual word count of the content")
    # citations_used: list[Citation] = Field(default_factory=list, description="Citations used in this subsection")
    # sources_referenced: list[str] = Field(default_factory=list, description="Source IDs referenced in this subsection")


class SectionContent(BaseModel):
    """Content for a main section with its subsections"""

    section_title: str = Field(description="Title of the section")
    section_type: str = Field(description="Type of section")
    content: str = Field(
        description="Full comprehensive content in MDX format (intro if has subsections, full content if no subsections)"
    )
    word_count: int = Field(description="Actual word count of the main section content")
    # citations_used: list[Citation] = Field(default_factory=list, description="Citations used in the main section")
    # sources_referenced: list[str] = Field(default_factory=list, description="Source IDs referenced in the main section")
    subsections: list[SubsectionContent] = Field(
        default_factory=list, description="List of subsections with full content"
    )


class SingleSectionWritingResult(BaseModel):
    """Result for writing a single section with all its subsections"""

    section: SectionContent = Field(
        description="The complete section with main content and all subsections"
    )
    # total_word_count: int = Field(description="Total word count including main section and all subsections")
    # citations_used: list[Citation] = Field(description="All citations used across the section and subsections")
    # sources_referenced: list[str] = Field(description="All source IDs referenced")
    # writing_notes: str = Field(default="", description="Notes about the writing process")


llm = LLM(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))


def _build_writer_crew() -> Crew:
    writing_agent = Agent(
        role="Academic Writer",
        goal="Write high-quality, well-cited academic content for thesis sections",
        backstory="""You are an experienced academic writer with expertise in scholarly writing.
        You excel at crafting clear, persuasive arguments with proper citations and academic tone.
        You write comprehensively and in-depth, never providing summaries but always full, detailed content.

        After drafting content you MUST persist it back to the Django project:
        - Call `project_section_save_tool` with the section JSON (including project_id) to store content.
        - Call `project_status_update_tool` when transitioning between writing/complete states.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[SectionSaveTool(), ProjectStatusUpdateTool()],
    )

    writing_task = Task(
        description="""You are an academic writer. Write one thesis section at a time in-depth, using MDX.

            Inputs:
            - topic: {topic}
            - citation_style: {citation_style}
            - section: JSON object describing ONE main section and its subsections from the outline
            - research_summary: {research_summary}
            - outline: full outline JSON: {outline}
            - project_id: {project_id}

            Requirements:
            - Write COMPREHENSIVE content (no summaries) for:
              - the main section
              - every subsection in section.subsections
            - Use MDX: headings, paragraphs, lists, etc.
            - Use proper {citation_style} citations where appropriate.
            - Respect any target/estimated word counts in the provided section/subsection objects:
              - minimum = target/estimated word count
              - aim for roughly 120–150% of that minimum.
              - this should no be a barrier when writing the content, make sure to write extensively and cover all the points in the section and subsections.

            Output:
            - Return ONLY a JSON object matching SingleSectionWritingResult (no extra text).

            Persistence Requirements:
            - After generating the JSON result, call `project_section_save_tool` with:
              {
                "project_id": {project_id},
                "sections": [ ...SingleSectionWritingResult... ],
                "mark_completed": false|true (set true when the final section is done)
              }
            - If you complete the entire project, call `project_status_update_tool`
              to set the status to "completed".
            """,
        agent=writing_agent,
        expected_output="""A complete SingleSectionWritingResult object for ONE section with nested structure where:

            1. section: SectionContent - The complete section you are writing
            - Main sections WITHOUT subsections have FULL, COMPREHENSIVE content in MDX format (NOT summaries)
            - Main sections WITH subsections have COMPREHENSIVE introductory content in MDX format + subsections list populated
            - Each section's word_count must be >= target_word_count from outline (preferably 120-150% of minimum)

            2. section.subsections: list[SubsectionContent] - All subsections with FULL, COMPREHENSIVE content
            - Each SubsectionContent has parent_section field set
            - Each subsection's word_count must be >= target_word_count from outline (preferably 120-150% of minimum)
            - Each subsection contains COMPREHENSIVE, DETAILED content (NOT summaries)

            3. total_word_count: Sum of main section + all subsections
            - Must meet or exceed the sum of target_word_counts (preferably 120-150% for comprehensive writing)

            4. All content must be in valid MDX (Markdown Extended) format

            5. All content must be COMPREHENSIVE and DETAILED - never write summaries

            6. All other required fields properly populated

            The structure must be valid JSON matching the SingleSectionWritingResult Pydantic model.
            All content fields must contain comprehensive, detailed MDX formatted text - NO SUMMARIES.""",
        output_json=SingleSectionWritingResult,
        guardrail="""

            - The final output must be a valid JSON object matching the SingleSectionWritingResult structure:
              {
                "section": {
                  "section_title": "string",
                  "section_type": "string",
                  "content": "string",
                  "word_count": integer,
                  "subsections": [
                    {
                      "section_title": "string",
                      "parent_section": "string",
                      "section_type": "string",
                      "content": "string",
                      "word_count": integer
                    }
                  ]
                },
                "total_word_count": integer,
              }
            - All word counts must meet or exceed their target word counts from the outline.
            - All content must be comprehensive and detailed, not summaries.
            """,
    )

    return Crew(agents=[writing_agent], tasks=[writing_task], verbose=True)


_writer_crew: Crew | None = None


def get_writer_crew() -> Crew:
    global _writer_crew
    if _writer_crew is None:
        _writer_crew = _build_writer_crew()
    return _writer_crew
