import logging
import uuid

from app.services.notifications.base import EmailProvider, NotificationResult, SmsProvider

logger = logging.getLogger("wakaless.notifications.mock")


class MockEmailProvider(EmailProvider):
    # Captured here (class-level, so it survives across the per-call
    # instances get_email_provider() hands out) purely so tests can read
    # back what would've been emailed — e.g. a verification code — without
    # a real inbox. Never read in production code paths.
    sent: list[dict] = []

    def send(self, to_email: str, subject: str, body: str) -> NotificationResult:
        logger.info("MOCK EMAIL to=%s subject=%r body=%r", to_email, subject, body)
        MockEmailProvider.sent.append({"to": to_email, "subject": subject, "body": body})
        return NotificationResult(success=True, provider_reference=f"mock-email-{uuid.uuid4()}", raw={"mock": True})


class MockSmsProvider(SmsProvider):
    def send(self, to_phone: str, message: str) -> NotificationResult:
        logger.info("MOCK SMS to=%s message=%r", to_phone, message)
        return NotificationResult(success=True, provider_reference=f"mock-sms-{uuid.uuid4()}", raw={"mock": True})
