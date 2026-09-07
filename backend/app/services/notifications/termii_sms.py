import httpx

from app.config import get_settings
from app.services.notifications.base import NotificationResult, SmsProvider

settings = get_settings()
TERMII_BASE_URL = "https://api.ng.termii.com/api"

# Thin, defensive wrapper: reconfirm the exact request/response shape against
# Termii's current docs before going live (https://developers.termii.com/messaging).
# Note: Nigerian SMS sender IDs typically need pre-registration/approval with
# Termii before real messages will deliver — start that process before flipping
# SMS_PROVIDER=termii.


class TermiiSmsProvider(SmsProvider):
    def __init__(self) -> None:
        if not settings.termii_api_key:
            raise RuntimeError(
                "TERMII_API_KEY is not set. Set SMS_PROVIDER=mock for local dev, "
                "or add your Termii API key."
            )

    def send(self, to_phone: str, message: str) -> NotificationResult:
        payload = {
            "api_key": settings.termii_api_key,
            "to": to_phone,
            "from": settings.termii_sender_id,
            "sms": message,
            "type": "plain",
            "channel": "generic",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{TERMII_BASE_URL}/sms/send", json=payload)
            resp.raise_for_status()
            data = resp.json()
        success = str(data.get("code")) == "ok" or data.get("message_id") is not None
        return NotificationResult(success=success, provider_reference=data.get("message_id"), raw=data)
