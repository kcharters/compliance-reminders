"""
Compliance reminder definitions.

Reminders are persisted in reminders/reminders.json so they can be managed
from the GUI without touching code. Use load_reminders() / save_reminders()
for all read/write access.

Each reminder dict contains:
  - id          : unique slug
  - name        : human-readable label
  - recipients  : list of email addresses
  - schedule    : dict with "hour" and "minute" keys
  - days_before : list of lead times (days before deadline) to fire the reminder
  - deadline    : ISO date string of the compliance deadline
  - template    : template file name inside templates/
"""

import json
from pathlib import Path

_REMINDERS_FILE = Path(__file__).parent / "reminders.json"

_DEFAULT_REMINDERS: list[dict] = [
    {
        "id": "gdpr_annual_review",
        "name": "GDPR Annual Review",
        "recipients": ["dpo@example.com", "legal@example.com"],
        "schedule": {"hour": 8, "minute": 0},
        "days_before": [30, 14, 7, 1],
        "deadline": "2026-05-31",
        "template": "gdpr_review.html",
    },
    {
        "id": "iso27001_audit",
        "name": "ISO 27001 Internal Audit",
        "recipients": ["infosec@example.com"],
        "schedule": {"hour": 9, "minute": 0},
        "days_before": [60, 30, 7],
        "deadline": "2026-06-15",
        "template": "iso_audit.html",
    },
    {
        "id": "policy_renewal",
        "name": "Acceptable Use Policy Renewal",
        "recipients": ["hr@example.com", "it@example.com"],
        "schedule": {"hour": 8, "minute": 30},
        "days_before": [14, 7, 3, 1],
        "deadline": "2026-07-01",
        "template": "policy_renewal.html",
    },
]


def load_reminders() -> list[dict]:
    """Load reminders from JSON file, falling back to built-in defaults."""
    if _REMINDERS_FILE.exists():
        return json.loads(_REMINDERS_FILE.read_text(encoding="utf-8"))
    return [dict(r) for r in _DEFAULT_REMINDERS]


def save_reminders(reminders: list[dict]) -> None:
    """Persist reminders to JSON file."""
    _REMINDERS_FILE.write_text(json.dumps(reminders, indent=2), encoding="utf-8")


# Backward-compatible module-level constant used by scheduler.py at startup.
REMINDERS = load_reminders()
