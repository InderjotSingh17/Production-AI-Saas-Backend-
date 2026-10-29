import ssl
from celery import Celery
from app.config import settings
celery_app = Celery(
    "production_ai_saas_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=None,
    redis_backend_health_check_interval=25,
    redis_socket_connect_timeout=10,
    redis_socket_timeout=30,
    redis_retry_on_timeout=True,
    broker_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
    redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_transport_options={
        "global_keyprefix": "production_ai_celery:",
        "health_check_interval": 25,
        "socket_keepalive": True,
        "retry_on_timeout": True,
    },
    result_backend_transport_options={
        "global_keyprefix": "production_ai_celery_results:"
    },
)