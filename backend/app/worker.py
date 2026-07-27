"""
Celery application instance.

Configure via environment variables:
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/1

Run worker:
    celery -A app.worker worker -l info -c 2
"""

from __future__ import annotations

import os

from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "radioai",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=120,  # hard limit
    task_soft_time_limit=90,  # soft limit (raises SoftTimeLimitExceeded)
    worker_prefetch_multiplier=1,  # fair scheduling for CPU-heavy tasks
)

# Auto-discover tasks in app/tasks/
celery_app.autodiscover_tasks(["app.tasks"])
