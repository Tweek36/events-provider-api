from celery import Celery
from celery.schedules import crontab
import requests
from app.settings import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
)

celery_app.conf.beat_schedule = {
    "daily-sync-task": {
        "task": "app.celery_app.daily_sync",
        "schedule": crontab(hour=3, minute=0),  # Каждый день в 03:00
    },
}


@celery_app.task
def daily_sync():
    try:
        response = requests.get(f"http://{settings.HOSTNAME}/api/sync/trigger")
        print(f"Sync status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Sync failed: {e}")
        raise e
