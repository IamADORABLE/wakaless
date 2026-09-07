from app.config import get_settings

settings = get_settings()


def compute_commission_ngn(rent_amount_ngn: int) -> int:
    """The platform's commission on a rent payment; the rest is paid to the
    landlord manually by an admin (see RentPayment.payout_status)."""
    if rent_amount_ngn < settings.commission_threshold_ngn:
        return settings.commission_low_ngn
    return settings.commission_high_ngn
