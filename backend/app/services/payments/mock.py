import uuid

from app.services.payments.base import InitiatedPayment, PaymentProvider, VerifiedPayment


class MockPaymentProvider(PaymentProvider):
    """Used when PAYMENT_PROVIDER=mock. Every payment 'succeeds' instantly —
    good enough to exercise the rent-payment flow end-to-end without a Paystack key."""

    def initiate(self, amount_ngn: int, email: str, metadata: dict, callback_url: str | None = None) -> InitiatedPayment:
        return InitiatedPayment(reference=f"mock-{uuid.uuid4()}", authorization_url=None)

    def verify(self, reference: str) -> VerifiedPayment:
        return VerifiedPayment(success=True, reference=reference, amount_ngn=0, raw={"mock": True})
