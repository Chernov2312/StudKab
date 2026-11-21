import asyncio

from celery import Celery
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as DatabaseTimeout

from app.core.config import get_settings
from app.core.domain import utcnow
from app.db.database import make_database
from app.services.notification_service import create_exam_reminders

app = Celery("puls", broker=get_settings().celery_broker_url)
app.conf.update(
    timezone="UTC",
    accept_content=["json"],
    task_ignore_result=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "exam-reminders": {
            "task": "puls.exam_reminders",
            "schedule": 60.0,
            "options": {"expires": 60},
        }
    },
)


async def run_exam_reminders() -> int:
    database = make_database(get_settings().database_url)
    try:
        async with database() as db:
            return await create_exam_reminders(db, utcnow())
    finally:
        await database.kw["bind"].dispose()


@app.task(
    name="puls.exam_reminders",
    acks_late=True,
    autoretry_for=(OperationalError, InterfaceError, DatabaseTimeout, OSError),
    retry_backoff=True,
    retry_backoff_max=15,
    retry_kwargs={"max_retries": 3},
)
def exam_reminders() -> int:
    return asyncio.run(run_exam_reminders())
