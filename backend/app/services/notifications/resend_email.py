import httpx

from app.config import get_settings
from app.services.notifications.base import EmailProvider, NotificationResult

settings = get_settings()
RESEND_BASE_URL = "https://api.resend.com"

# Thin, defensive wrapper: reconfirm the exact request/response shape against
# Resend's current docs before going live (https://resend.com/docs/api-reference/emails/send-email).


class ResendEmailProvider(EmailProvider):
    def __init__(self) -> None:
        if not settings.resend_api_key:
            raise RuntimeError(
                "RESEND_API_KEY is not set. Set EMAIL_PROVIDER=mock for local dev, "
                "or add your Resend API key."
            )
        self.headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    def send(self, to_email: str, subject: str, body: str) -> NotificationResult:
        payload = {
            "from": settings.notifications_from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{RESEND_BASE_URL}/emails", json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
        return NotificationResult(success=True, provider_reference=data.get("id"), raw=data)
