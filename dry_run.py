"""Quick smoke-test: print which reminders would fire today without sending emails."""

from datetime import date
from reminders.definitions import REMINDERS


def dry_run() -> None:
    today = date.today()
    print(f"Dry-run for {today}\n{'='*40}")
    for r in REMINDERS:
        deadline = date.fromisoformat(r["deadline"])
        days_remaining = (deadline - today).days
        would_fire = days_remaining in r["days_before"] and days_remaining >= 0
        status = "✅ WOULD FIRE" if would_fire else "  skipped"
        print(f"{status}  [{r['id']}]  days_remaining={days_remaining}")


if __name__ == "__main__":
    dry_run()
