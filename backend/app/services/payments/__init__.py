from app.config import get_settings
from app.services.payments.base import InitiatedPayment, PaymentProvider, VerifiedPayment
from app.services.payments.mock import MockPaymentProvider

settings = get_settings()


def get_payment_provider() -> PaymentProvider:
    provider = settings.payment_provider
    if provider == "mock":
        return MockPaymentProvider()
    if provider == "paystack":
        from app.services.payments.paystack import PaystackPaymentProvider
        return PaystackPaymentProvider()
    raise ValueError(f"Unknown PAYMENT_PROVIDER '{provider}'. Use mock or paystack.")


__all__ = ["PaymentProvider", "InitiatedPayment", "VerifiedPayment", "get_payment_provider"]
