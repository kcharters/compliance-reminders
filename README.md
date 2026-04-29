# Compliance Reminders

Python service that sends scheduled email reminders for compliance deadlines using **APScheduler** and **Jinja2** templates.

## Features
- Cron-based scheduling per reminder (APScheduler)
- Configurable lead times (`days_before`) per deadline
- HTML email templates with Jinja2
- SMTP delivery (Gmail, Outlook, or any SMTP relay)
- Dry-run mode to preview what would fire today without sending

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt

cp .env.example .env         # fill in your SMTP credentials
python dry_run.py            # preview – no emails sent
python main.py               # start the scheduler
```

## Adding a Reminder

1. Add an entry to `reminders/definitions.py`
2. Create the matching HTML template in `templates/`

```python
{
    "id": "soc2_evidence",
    "name": "SOC 2 Evidence Collection",
    "recipients": ["audit@example.com"],
    "schedule": {"hour": 8, "minute": 0},
    "days_before": [90, 60, 30, 7],
    "deadline": "2026-09-30",
    "template": "soc2_evidence.html",
},
```

## Project Structure

```
compliance-reminders/
  main.py               # entry point
  scheduler.py          # APScheduler setup & job logic
  dry_run.py            # preview tool
  config.py             # env-based configuration
  reminders/
    definitions.py      # reminder catalogue
    email_sender.py     # SMTP send helper
    renderer.py         # Jinja2 template renderer
  templates/            # HTML email templates
  .env.example
```
