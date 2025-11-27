from crewai import Crew, Agent, Task, LLM, TaskOutput
from dotenv import load_dotenv
from .tools.main import (
    BrightDataWebUnlockerTool,
    EnhancedPDFReaderTool,
    PDFMetadataReaderTool,
)
from crews.tools.project_model_tools import (
    ProjectStatusUpdateTool,
    ResearchSaveTool,
)
from crewai_tools import ScrapeWebsiteTool, SerperDevTool, WebsiteSearchTool
from pydantic import BaseModel, Field
import os

load_dotenv()

class ResearchOutput(BaseModel):
    sources: list[dict] = Field(description="List of sources found in the research")
    research_summary: str = Field(
        description="Overall research summary and main themes"
    )
    research_gaps: str = Field(description="Identified research gaps")
    recommendations: str = Field(description="Recommended research directions")
    total_sources_found: int = Field(description="Total number of sources found")
    pdf_sources_count: int = Field(description="Number of PDF sources found")
    web_sources_count: int = Field(description="Number of web sources found")



llm = LLM(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))


def _build_research_tools():
    tools = []
    for tool in [
        SerperDevTool(),
        BrightDataWebUnlockerTool(),
        # WebsiteSearchTool(),
        EnhancedPDFReaderTool(),
        PDFMetadataReaderTool(),
    ]:
        if tool is not None:
            tools.append(tool)
    tools.append(ResearchSaveTool())
    tools.append(ProjectStatusUpdateTool())
    return tools


def validate_total_research_output(result: TaskOutput):
    "Validate that the total number of source is not less that 10 sources"
    try:
        total_sources = result.json()["total_sources_found"]

        print(f"Total sources found: {total_sources}")
        if total_sources < 10:
            return False
        return True
    except Exception as e:
        print(f"Error validating total research output: {e}")
        return False


def _build_research_crew() -> Crew:
    tools = _build_research_tools()
    research_agent = Agent(
        role="Research Specialist",
        goal="Conduct comprehensive academic research and identify relevant sources",
        backstory="""You are an expert academic researcher with deep knowledge across multiple disciplines.
        You excel at finding high-quality academic sources, analyzing their relevance, and extracting key insights.
        You have access to internet search, web scraping, and can visit academic databases and websites.

        You MUST actively use the available tools:
        - Use SerperDevTool to search the internet for academic sources
        - Use WebsiteSearchTool to find relevant websites
        - Use BrightDataWebUnlockerTool to scrape content from websites
        - Use EnhancedPDFReaderTool to read PDF documents when you find PDF links
        - Use PDFMetadataReaderTool to extract metadata from PDFs
        - When you finish compiling sources and summaries, call `project_research_save_tool`
          with JSON payload containing `project_id`, `research` object, and `sources`
          to persist data in the Django project.
        - Use `project_status_update_tool` whenever you need to explicitly move the
          project between statuses (researching, failed, etc.).

        Do not just describe what you would do - actually USE these tools to gather information.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )

    research_task = Task(
        description="""
            Topic: {topic}
            Citation Style: {citation_style}
            project_id: {project_id}

            CRITICAL: You MUST use the available tools to conduct research. Do not just describe what you would do - actually execute tool calls.

            Your task:
            1. **USE SerperDevTool** to search the internet for academic sources related to: {topic}
            2. **USE WebsiteSearchTool** to find relevant academic websites and databases
            3. **USE BrightDataWebUnlockerTool** to scrape content from academic databases, journals, and websites
            4. **USE EnhancedPDFReaderTool** to read PDF files when you encounter PDF links
            5. **USE PDFMetadataReaderTool** to extract metadata from PDF documents
            6. Find 15-20 high-quality academic sources from various online platforms
            7. Analyze each source for relevance and quality
            8. Extract key findings and insights from scraped content and PDF documents
            9. Generate proper citations in {citation_style} format
            10. Provide a comprehensive research summary

            Persistence Requirements:
            - After assembling the final JSON output, call `project_research_save_tool`
              with a payload formatted as:
              {
                "project_id": {project_id},
                "research": { ...research_output_fields... },
                "sources": [ ...sources_list... ]
              }
            - If you need to adjust the project workflow state (e.g., mark failure),
              call `project_status_update_tool` with
              {"project_id": {project_id}, "status": "<new_status>", "note": "..."}.

            PDF Handling Guidelines:
            - **AUTOMATIC PDF PROCESSING**: When you encounter PDF links, the system will automatically extract text content
            - PDFs often contain more complete and accurate information than web scraping
            - Academic papers, research reports, and official documents are often in PDF format
            - **IMPORTANT**: If a PDF URL is not accessible, the system will note the error and continue with other sources
            - **PDF Content Extraction**: The system can now read and extract text from PDF documents automatically
            - **Source Identification**: PDF sources will be clearly marked with source_type: 'pdf'
            - **Content Quality**: PDF content is often more reliable and complete than web page content

            Focus on:
            - Peer-reviewed academic papers
            - Recent publications (last 5-10 years)
            - Authoritative sources
            - Diverse perspectives on the topic
            - High-quality web content from academic institutions
            """,
        agent=research_agent,
        expected_output="""
            Return a JSON object with this exact structure:
            {
                "sources": [
                    {
                        "title": "Source Title",
                        "source_type": "academic|book|article|website|report|other",
                        "authors": ["Author 1", "Author 2"],
                        "publication_year": 2023,
                        "url": "https://example.com",
                        "doi": "10.1000/example",
                        "abstract": "Abstract text...",
                        "key_findings": "Key findings extracted by AI...",
                        "summary": "AI-generated summary...",
                        "full_content": "Full content scraped from source...",
                        "relevance_score": 0.85,
                        "relevance_reason": "Why this source is relevant...",
                        "citation_text": "Formatted citation in project citation style"
                    }
                ],
                "research_summary": "Overall research summary and main themes...",
                "research_gaps": "Identified research gaps...",
                "recommendations": "Recommended research directions...",
                "total_sources_found": 15,
                "pdf_sources_count": 5,
                "web_sources_count": 10
            }

            IMPORTANT: Return ONLY valid JSON. No additional text or explanations outside the JSON structure.
            """,
        output_json=ResearchOutput,
        guardrail="""
            CRITICAL REQUIREMENT: The total number of sources found (total_sources_found) must be greater than 10.

            If you find fewer than 10 sources:
            1. Analyze why your search might have been too narrow or specific
            2. Refine your search query by:
               - Using broader or alternative keywords related to the topic
               - Trying different search terms and synonyms
               - Searching in different academic databases or platforms
               - Using related terms, acronyms, or variations of the topic
            3. Use the search tools again with the refined queries
            4. Expand your search to include:
               - Related subtopics
               - Different perspectives or approaches
               - Alternative terminology or jargon used in the field
            5. Continue searching until you have found at least 10 high-quality sources

            Do NOT return results with fewer than 10 sources. Keep refining and searching until you meet this requirement.
            """,
    )

    return Crew(agents=[research_agent], tasks=[research_task], verbose=True)


_research_crew: Crew | None = None


def get_research_crew() -> Crew:
    global _research_crew
    if _research_crew is None:
        _research_crew = _build_research_crew()
    return _research_crew
