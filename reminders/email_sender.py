"""Email sending utilities."""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def send_email(recipients: list[str], subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    if not config.EMAIL_USER or not config.EMAIL_PASSWORD:
        logger.warning("EMAIL_USER / EMAIL_PASSWORD not configured – skipping send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_FROM, recipients, msg.as_string())
        logger.info("Email sent to %s | subject: %s", recipients, subject)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email: %s", exc)
        return False
