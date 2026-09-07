from app.config import get_settings
from app.services.notifications.base import EmailProvider, NotificationResult, SmsProvider
from app.services.notifications.mock import MockEmailProvider, MockSmsProvider

settings = get_settings()


def get_email_provider() -> EmailProvider:
    provider = settings.email_provider
    if provider == "mock":
        return MockEmailProvider()
    if provider == "resend":
        from app.services.notifications.resend_email import ResendEmailProvider
        return ResendEmailProvider()
    if provider == "zeptomail":
        from app.services.notifications.zeptomail_email import ZeptoMailEmailProvider
        return ZeptoMailEmailProvider()
    raise ValueError(f"Unknown EMAIL_PROVIDER '{provider}'. Use mock, resend, or zeptomail.")


def get_sms_provider() -> SmsProvider:
    provider = settings.sms_provider
    if provider == "mock":
        return MockSmsProvider()
    if provider == "termii":
        from app.services.notifications.termii_sms import TermiiSmsProvider
        return TermiiSmsProvider()
    raise ValueError(f"Unknown SMS_PROVIDER '{provider}'. Use mock or termii.")


__all__ = ["EmailProvider", "SmsProvider", "NotificationResult", "get_email_provider", "get_sms_provider"]
