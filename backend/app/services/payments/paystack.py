import httpx

from app.config import get_settings
from app.services.payments.base import InitiatedPayment, PaymentProvider, VerifiedPayment

settings = get_settings()
PAYSTACK_BASE = "https://api.paystack.co"


class PaystackPaymentProvider(PaymentProvider):
    def __init__(self) -> None:
        if not settings.paystack_secret_key:
            raise RuntimeError(
                "PAYSTACK_SECRET_KEY is not set. Set PAYMENT_PROVIDER=mock for local dev, "
                "or add your Paystack secret key."
            )
        self.headers = {"Authorization": f"Bearer {settings.paystack_secret_key}"}

    def initiate(self, amount_ngn: int, email: str, metadata: dict, callback_url: str | None = None) -> InitiatedPayment:
        # Paystack expects amount in kobo (₦1 = 100 kobo).
        payload = {"email": email, "amount": amount_ngn * 100, "metadata": metadata}
        if callback_url:
            payload["callback_url"] = callback_url
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{PAYSTACK_BASE}/transaction/initialize", json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()["data"]
        return InitiatedPayment(reference=data["reference"], authorization_url=data["authorization_url"])

    def verify(self, reference: str) -> VerifiedPayment:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{PAYSTACK_BASE}/transaction/verify/{reference}", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()["data"]
        success = data.get("status") == "success"
        amount_ngn = int(data.get("amount", 0)) // 100
        return VerifiedPayment(success=success, reference=reference, amount_ngn=amount_ngn, raw=data)
