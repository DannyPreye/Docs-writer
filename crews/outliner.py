from crewai import Crew, Agent, Task, LLM
from dotenv import load_dotenv
import os
load_dotenv()

from pydantic import BaseModel, Field
class Structure(BaseModel):
    """Structure of the outline"""
    title: str
    type: str
    word_count: int
    order: int
    parent_section: str = Field(default="", description="Parent section name, empty string for top-level sections")

class SectionWithSubsections(BaseModel):
    """Section with its subsections"""
    section: Structure
    subsections: list[Structure]

class OutlineResult(BaseModel):
    """Result of the outline task"""
    structure: list[SectionWithSubsections]


llm= LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)


outline_agent = Agent(
        role='Academic Structure Specialist',
        goal='Create well-structured, logical thesis outline for {topic}',
        backstory="""You are a PhD-level academic advisor with expertise in thesis structure and organization.
        You understand different citation styles, academic conventions, and how to create compelling arguments.
        You excel at creating comprehensive outlines that follow academic standards and logical flow.
        You ensure proper methodology integration and research question alignment.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )



outline_task = Task(
        description="""Create a comprehensive thesis outline for: {topic}

        Topic: {topic}
        Citation Style: {citation_style}


        Research Summary: {research_summary}

        using the research summary, create a comprehensive thesis outline that follows the academic standards and logical flow.

        Your responsibilities:
        1. Analyze the research topic and available sources from the research task
        2. Create a comprehensive thesis outline
        3. Structure the outline logically with proper academic flow
        4. Include all standard thesis sections (Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References)
        5. Break down each section into subsections
        6. Estimate word count for each section
        7. Provide rationale for the structure

        Requirements:
        - Follow academic thesis structure conventions
        - Ensure logical flow and argument progression
        - Include methodology section appropriate for the research type
        - Plan for proper citation integration
        - For top-level sections (main sections), set parent_section to empty string ""
        - For subsections, set parent_section to the name of their parent section
        """,
        agent=outline_agent,
        expected_output="Comprehensive thesis outline with structure, rationale, and methodology in JSON format",
        output_json=OutlineResult

    )


outline_crew = Crew(
    agents=[outline_agent],
    tasks=[outline_task],
    verbose=True
)
