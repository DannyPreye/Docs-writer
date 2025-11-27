import asyncio
from celery import shared_task
from .models import Project

from crews.main import ProjectInfo, run_flow


@shared_task
def run_thesis_writing_flow(project_id):
    project = Project.objects.get(id=project_id)
    project_info = ProjectInfo(
        topic=project.topic,
        citation_style=project.citation_style,
        project_id=project.id,
    )
    result = asyncio.run(run_flow(project_info))
    return result
