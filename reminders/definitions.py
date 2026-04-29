"""
Compliance reminder definitions.

Each reminder is a dict describing:
  - id          : unique slug
  - name        : human-readable label
  - recipients  : list of email addresses
  - schedule    : cron expression (minute hour day month day_of_week)
  - days_before : list of lead times (days before deadline) to fire the reminder
  - deadline    : ISO date string of the compliance deadline
  - template    : template file name inside templates/
"""

from datetime import date

REMINDERS: list[dict] = [
    {
        "id": "gdpr_annual_review",
        "name": "GDPR Annual Review",
        "recipients": ["dpo@example.com", "legal@example.com"],
        # Fire every day at 08:00 so the days_before logic can check proximity
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
