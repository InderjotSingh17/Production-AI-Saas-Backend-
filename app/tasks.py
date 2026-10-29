from celery import shared_task
@shared_task(
    bind=True,
    name="app.tasks.process_background_job",
    max_retries=3,
    acks_late=True,
)
def process_background_job(self, job_name: str) -> dict:
    try:
        return {
            "job_name": job_name,
            "status": "completed",
        }
    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=2 ** self.request.retries,
        )