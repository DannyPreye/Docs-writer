import asyncio
from celery import shared_task
from .models import Project

from crews.main import run_flow


@shared_task
def run_thesis_writing_flow(project_id):
    project = Project.objects.get(id=project_id)
    run_flow(project)
