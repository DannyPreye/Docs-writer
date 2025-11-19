import asyncio
import json
from typing import Optional
from crewai.flow import Flow, start, listen
from pydantic import BaseModel, Field

from crews.writer import writer_crew

from .outliner import outline_crew
from .researcher import research_crew


class ProjectInfo(BaseModel):
    topic: Optional[str] = None
    citation_style: Optional[str] = None
    research_summary: Optional[str] = None
    outline: Optional[dict] = None


class ThesisWritingFlow(Flow[ProjectInfo]):
    @start()
    async def get_project_info(self):
        return ProjectInfo(
            topic=self.state.topic, citation_style=self.state.citation_style
        )

    @listen(get_project_info)
    def research(self):

        crew_result = research_crew.kickoff(
            inputs={
                "topic": self.state.topic,
                "citation_style": self.state.citation_style,
            }
        )
        self.state.research_summary = crew_result.raw
        return self.state.research_summary

    @listen(research)
    def outliner(self):
        crew_result = outline_crew.kickoff(
            inputs={
                "topic": self.state.topic,
                "citation_style": self.state.citation_style,
                "research_summary": self.state.research_summary,
            }
        )
        self.state.outline = crew_result.raw
        return self.state.outline

    @listen(outliner)
    def writer(self):
        # Build a list where each item contains all context needed for writing one section
        clean_outline = []

        # Outline may come back as JSON string or dict; handle both
        outline_data = self.state.outline
        if isinstance(outline_data, str):
            try:
                outline_data = json.loads(outline_data)
            except json.JSONDecodeError:
                # If parsing fails, just wrap whole outline once and return
                clean_outline.append(
                    {
                        "topic": self.state.topic,
                        "citation_style": self.state.citation_style,
                        "section": None,
                        "research_summary": self.state.research_summary,
                        "outline": self.state.outline,
                    }
                )

                print("clean_outline", clean_outline)

                return writer_crew.kickoff_for_each(inputs=clean_outline)

        # Expecting OutlineResult-like structure with a "structure" list
        sections = (
            outline_data.get("structure", []) if isinstance(outline_data, dict) else []
        )

        for section in sections:
            clean_outline.append(
                {
                    "topic": self.state.topic,
                    "citation_style": self.state.citation_style,
                    "section": section,
                    "research_summary": self.state.research_summary,
                    "outline": outline_data,
                }
            )

        print("clean_outline", clean_outline)
        # return

        # Call the writer crew once per section with full context
        return writer_crew.kickoff_for_each(inputs=clean_outline)


async def run_flow(project: ProjectInfo):
    print(f"Running flow for project: {project.topic}")
    flow = ThesisWritingFlow()
    result = await flow.kickoff_async(
        inputs={"topic": project.topic, "citation_style": project.citation_style}
    )
    print("result", result)
    return result


if __name__ == "__main__":
    project = ProjectInfo(
        topic="Prevalence of Poorly Fitting Dentures in Elderly Nigerians and Contributing Factors",
        citation_style="APA",
    )

    asyncio.run(run_flow(project))
