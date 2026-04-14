"""
漫AI - Celery 任务
"""
from app.tasks.video_generation import celery_app, process_generation_task, submit_generation_task

__all__ = ["celery_app", "process_generation_task", "submit_generation_task"]
