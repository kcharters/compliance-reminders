"""Entry point – start the compliance reminder scheduler."""

import logging
from scheduler import build_scheduler

logger = logging.getLogger(__name__)


def main() -> None:
    scheduler = build_scheduler()
    logger.info("Compliance reminder scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
