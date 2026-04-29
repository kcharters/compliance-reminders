"""APScheduler job that checks each reminder and fires emails when needed."""

import logging
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from reminders.definitions import REMINDERS
from reminders.email_sender import send_email
from reminders.renderer import render
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _check_and_send(reminder: dict) -> None:
    """Check if today matches a days_before threshold and send if so."""
    deadline = date.fromisoformat(reminder["deadline"])
    today = date.today()
    days_remaining = (deadline - today).days

    if days_remaining < 0:
        logger.info("[%s] Deadline has passed – skipping.", reminder["id"])
        return

    if days_remaining not in reminder["days_before"]:
        logger.debug("[%s] No reminder threshold matched (days_remaining=%d).", reminder["id"], days_remaining)
        return

    logger.info("[%s] Sending reminder – %d days to deadline.", reminder["id"], days_remaining)

    html = render(
        reminder["template"],
        {
            "reminder_name": reminder["name"],
            "days_remaining": days_remaining,
            "deadline": deadline.strftime("%d %B %Y"),
        },
    )

    subject = f"⚠️ Reminder: {reminder['name']} – {days_remaining} day{'s' if days_remaining != 1 else ''} remaining"
    send_email(reminder["recipients"], subject, html)


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=config.TIMEZONE)

    for reminder in REMINDERS:
        schedule = reminder["schedule"]
        trigger = CronTrigger(
            hour=schedule.get("hour", "*"),
            minute=schedule.get("minute", 0),
            timezone=config.TIMEZONE,
        )
        scheduler.add_job(
            _check_and_send,
            trigger=trigger,
            kwargs={"reminder": reminder},
            id=reminder["id"],
            name=reminder["name"],
            replace_existing=True,
        )
        logger.info("Scheduled '%s' at %s", reminder["name"], schedule)

    return scheduler
