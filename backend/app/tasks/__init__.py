"""
漫AI - 任务初始化
"""
from app.tasks.video_generation import celery_app, generate_video_task

__all__ = ["celery_app", "generate_video_task"]
