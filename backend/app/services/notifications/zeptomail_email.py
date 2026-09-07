import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from app.config import get_settings
from app.services.notifications.base import EmailProvider, NotificationResult

settings = get_settings()


class ZeptoMailEmailProvider(EmailProvider):
    """Sends real email via ZeptoMail's SMTP relay (STARTTLS)."""

    def __init__(self) -> None:
        if not settings.zeptomail_smtp_user or not settings.zeptomail_smtp_password:
            raise RuntimeError(
                "ZEPTOMAIL_SMTP_USER / ZEPTOMAIL_SMTP_PASSWORD are not set. "
                "Set EMAIL_PROVIDER=mock for local dev, or add your ZeptoMail SMTP credentials."
            )

    def send(self, to_email: str, subject: str, body: str) -> NotificationResult:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((settings.notifications_from_name, settings.notifications_from_email))
        msg["To"] = to_email

        with smtplib.SMTP(settings.zeptomail_smtp_host, settings.zeptomail_smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(settings.zeptomail_smtp_user, settings.zeptomail_smtp_password)
            smtp.sendmail(settings.notifications_from_email, [to_email], msg.as_string())

        return NotificationResult(success=True, provider_reference=None, raw={})
