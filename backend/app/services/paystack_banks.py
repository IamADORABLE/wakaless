"""
Paystack's bank list + account-number resolution. Kept separate from
services/payments/paystack.py because this is used regardless of
PAYMENT_PROVIDER (there's no "mock bank list" that makes sense) — it's
purely for helping a landlord fill in their payout bank details correctly.

Both endpoints are read-only lookups (no money moves), so Paystack allows
calling them with a test secret key the same as a live one.
"""
import httpx

from app.config import get_settings

settings = get_settings()
PAYSTACK_BASE = "https://api.paystack.co"

_banks_cache: list[dict] | None = None


def _headers() -> dict:
    if not settings.paystack_secret_key:
        raise RuntimeError(
            "PAYSTACK_SECRET_KEY is not set, so bank lookup/verification is unavailable."
        )
    return {"Authorization": f"Bearer {settings.paystack_secret_key}"}


def list_nigerian_banks() -> list[dict]:
    """Every active Nigerian bank Paystack can resolve accounts for.
    Cached for the process lifetime since this basically never changes."""
    global _banks_cache
    if _banks_cache is not None:
        return _banks_cache

    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{PAYSTACK_BASE}/bank",
            params={"country": "nigeria", "currency": "NGN"},
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()["data"]

    _banks_cache = [
        {"name": b["name"], "code": b["code"]}
        for b in data
        if b.get("active") and b.get("code")
    ]
    return _banks_cache


def resolve_account(account_number: str, bank_code: str) -> str:
    """Looks up the account holder's name for a given account number + bank,
    the same way Paystack's own checkout verifies transfer recipients."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{PAYSTACK_BASE}/bank/resolve",
            params={"account_number": account_number, "bank_code": bank_code},
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()["data"]
    return data["account_name"]
