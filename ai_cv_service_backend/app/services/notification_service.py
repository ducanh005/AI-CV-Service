import logging

from app.integrations.gmail_integration import send_email_via_gmail
from app.workers.tasks import send_email_notification


logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def _dispatch_email(email: str, subject: str, body: str) -> None:
        try:
            send_email_notification.delay(email, subject, body)
        except Exception:
            logger.exception("Celery dispatch failed, sending email synchronously")
            send_email_via_gmail(email, subject, body)

    @staticmethod
    def send_apply_success(email: str, job_title: str) -> None:
        subject = "Application Submitted Successfully"
        body = f"Your application for '{job_title}' has been received."
        NotificationService._dispatch_email(email, subject, body)

    @staticmethod
    def send_interview_invitation(email: str, interview_link: str) -> None:
        subject = "Interview Invitation"
        body = f"Your interview has been scheduled. Join here: {interview_link}"
        NotificationService._dispatch_email(email, subject, body)

    @staticmethod
    def send_screening_result(email: str, job_title: str, passed: bool, score: float, threshold: float) -> None:
        if passed:
            subject = f"CV Screening Result: Passed ({job_title})"
            body = (
                f"Congratulations. Your CV passed screening for '{job_title}'. "
                f"Score: {score}/100 (threshold: {threshold})."
            )
        else:
            subject = f"CV Screening Result: Not Passed ({job_title})"
            body = (
                f"Thank you for applying to '{job_title}'. "
                f"Current score: {score}/100 (threshold: {threshold})."
            )
        NotificationService._dispatch_email(email, subject, body)
