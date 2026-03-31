import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email_via_gmail(to_email: str, subject: str, body: str) -> None:
    sender_email = (settings.GMAIL_SENDER_EMAIL or "").strip()
    app_password = (settings.GMAIL_APP_PASSWORD or "").strip()

    if not sender_email or not app_password:
        logger.warning("Gmail credentials not configured, skipping email send")
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(sender_email, app_password)
            smtp.sendmail(sender_email, [to_email], message.as_string())
    except smtplib.SMTPException:
        logger.exception("Failed to send email via Gmail SMTP")
        raise
