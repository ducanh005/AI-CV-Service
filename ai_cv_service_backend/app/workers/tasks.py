from app.integrations.gmail_integration import send_email_via_gmail
from app.workers.celery_app import celery_app


@celery_app.task(name="send_email_notification")
def send_email_notification(to_email: str, subject: str, body: str) -> None:
    send_email_via_gmail(to_email=to_email, subject=subject, body=body)


@celery_app.task(name="parse_cv_background")
def parse_cv_background(cv_id: int) -> dict[str, str]:
    # Placeholder for heavy CV parse operation.
    return {"cv_id": str(cv_id), "status": "queued_and_processed"}
