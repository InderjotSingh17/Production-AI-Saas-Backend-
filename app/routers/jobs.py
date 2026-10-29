
from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from redis.exceptions import RedisError
from app.dependencies import get_current_user
from app.models import User
from app.celery_app import celery_app
from app.tasks import process_background_job

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.post("")
def submit_job(
    current_user: User = Depends(get_current_user),
):
    try:
        task = process_background_job.delay(
            f"demo-user-{current_user.id}"
        )
    except (RedisError, OSError):
        raise HTTPException(
            status_code=503,
            detail="Unable to queue background job.",
        )

    return {
        "task_id": task.id,
        "status": "queued",
    }


@router.get("/{task_id}")
def get_job_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
