import logging
from datetime import datetime

from app.config import get_settings
from app.services.notifications import get_email_provider, get_sms_provider

settings = get_settings()
logger = logging.getLogger("wakaless.notifications")


def notify_landlord_availability_check(listing, renter) -> tuple[datetime | None, datetime | None]:
    """Email + SMS the landlord asking them to confirm the listing is still
    available. Returns (email_sent_at, sms_sent_at); None for whichever
    channel failed, so the caller can store what actually went out."""
    landlord = listing.landlord
    subject = f"Is '{listing.title}' still available?"
    body = (
        f"Hi {landlord.full_name}, a renter wants to pay for your listing "
        f"'{listing.title}' ({listing.area}). Please reply to confirm it's "
        f"still available. An admin will follow up with you shortly."
    )
    email_sent_at = None
    email_result = get_email_provider().send(landlord.email, subject, body)
    if email_result.success:
        email_sent_at = datetime.utcnow()

    sms_sent_at = None
    sms_message = f"Wakaless: a renter wants to pay for '{listing.title}'. Is it still available? An admin will contact you."
    sms_result = get_sms_provider().send(landlord.phone, sms_message)
    if sms_result.success:
        sms_sent_at = datetime.utcnow()

    return email_sent_at, sms_sent_at


def notify_renter_renewal_reminder(rent_payment, lead_time_label: str) -> bool:
    """Email the renter asking if they're renewing before their tenancy ends."""
    renter = rent_payment.renter
    listing = rent_payment.listing
    subject = f"Your rent for '{listing.title}' ends in {lead_time_label}. Renewing?"
    body = (
        f"Hi {renter.full_name}, your tenancy at '{listing.title}' ({listing.area}) "
        f"ends on {rent_payment.end_date.strftime('%d %b %Y')} ({lead_time_label} from now). "
        f"Let us know if you're renewing so we can hold the listing for you. "
        f"Otherwise it'll be made available to other renters after that date."
    )
    result = get_email_provider().send(renter.email, subject, body)
    return result.success


def send_verification_email(user, code: str) -> bool:
    """Email a new signup a code to confirm they own this email address."""
    subject = "Your Wakaless verification code"
    body = (
        f"Hi {user.full_name}, welcome to Wakaless. Your verification code is:\n\n"
        f"{code}\n\n"
        f"Enter it in the app to confirm your email. It expires in {settings.email_verification_code_expire_minutes} minutes.\n\n"
        "If you didn't create this account, you can ignore this email.\n\nWakaless"
    )
    result = get_email_provider().send(user.email, subject, body)
    return result.success


def send_password_reset_email(user, code: str) -> bool:
    """Email a renter/landlord/admin a code to set a new password."""
    subject = "Your Wakaless password reset code"
    body = (
        f"Hi {user.full_name}, we got a request to reset your Wakaless password. Your code is:\n\n"
        f"{code}\n\n"
        f"Enter it in the app to choose a new password. It expires in {settings.password_reset_code_expire_minutes} minutes.\n\n"
        "If you didn't request this, you can ignore this email.\n\nWakaless"
    )
    result = get_email_provider().send(user.email, subject, body)
    return result.success


def notify_admin_verification_pending(landlord) -> bool:
    """Email the admin inbox when a landlord submits their photo for
    review. Best-effort: a failure here must never break the landlord's
    submit response, the request still shows up in the admin queue either way."""
    if not settings.admin_email:
        return False
    try:
        queue_url = f"{settings.frontend_origin}/admin/verification-queue"
        subject = f"Landlord verification pending: {landlord.full_name}"
        body = (
            f"{landlord.full_name} ({landlord.phone}, {landlord.email}) just submitted "
            f"their photo for review.\n\n"
            f"Review it here: {queue_url}\n\nWakaless"
        )
        result = get_email_provider().send(settings.admin_email, subject, body)
        return result.success
    except Exception:
        logger.exception("Failed to email admin about pending verification for landlord %s", landlord.id)
        return False


def notify_admin_availability_request(listing, renter) -> bool:
    """Email the admin inbox when a renter asks to confirm a listing's
    availability, so the admin knows to follow up with the landlord.
    Best-effort: a failure here must never break the renter's request."""
    if not settings.admin_email:
        return False
    try:
        queue_url = f"{settings.frontend_origin}/admin/availability-queue"
        subject = f"Availability request: {listing.title}"
        body = (
            f"{renter.full_name} ({renter.phone}, {renter.email}) wants to confirm that "
            f"'{listing.title}' ({listing.area}) is still available.\n\n"
            f"Landlord: {listing.landlord.full_name} ({listing.landlord.phone})\n\n"
            f"Review it here: {queue_url}\n\nWakaless"
        )
        result = get_email_provider().send(settings.admin_email, subject, body)
        return result.success
    except Exception:
        logger.exception("Failed to email admin about availability request for listing %s", listing.id)
        return False


def notify_admin_new_listing(listing) -> bool:
    """Email the admin inbox when a landlord submits a listing for review.
    Best-effort: a failure here must never break the landlord's submit response."""
    if not settings.admin_email:
        return False
    try:
        queue_url = f"{settings.frontend_origin}/admin/review-queue"
        subject = f"New listing pending review: {listing.title}"
        body = (
            f"{listing.landlord.full_name} ({listing.landlord.phone}, {listing.landlord.email}) "
            f"just submitted a new listing for review.\n\n"
            f"'{listing.title}' ({listing.area}), NGN {listing.rent_amount_ngn:,}/"
            f"{listing.rent_duration_months} months.\n\n"
            f"Review it here: {queue_url}\n\nWakaless"
        )
        result = get_email_provider().send(settings.admin_email, subject, body)
        return result.success
    except Exception:
        logger.exception("Failed to email admin about new listing %s", listing.id)
        return False


def notify_renter_receipt(rent_payment) -> bool:
    """Email the renter their receipt right after a successful payment.
    Best-effort: a failure here must never break the payment response, the
    renter can still view/print the receipt in the app either way."""
    try:
        renter = rent_payment.renter
        listing = rent_payment.listing
        receipt_url = f"{settings.frontend_origin}/renter/payments/{rent_payment.id}/receipt"

        lines = [f"Rent ({rent_payment.rent_duration_months} months): NGN {rent_payment.rent_amount_ngn:,}"]
        if rent_payment.agreement_fee_ngn > 0:
            lines.append(f"Agreement fee: NGN {rent_payment.agreement_fee_ngn:,}")
        if rent_payment.commission_ngn > 0:
            lines.append(f"Commission: NGN {rent_payment.commission_ngn:,}")
        lines.append(f"Total paid: NGN {rent_payment.total_paid_ngn:,}")

        subject = f"Your receipt for '{listing.title}'"
        body = (
            f"Hi {renter.full_name}, thanks for your payment. Here's your receipt for "
            f"'{listing.title}' ({listing.address}).\n\n"
            + "\n".join(lines)
            + f"\n\nTenancy: {rent_payment.start_date.strftime('%d %b %Y')} to {rent_payment.end_date.strftime('%d %b %Y')}"
            + f"\nPayment reference: {rent_payment.payment_reference}"
            + f"\n\nLandlord: {listing.landlord.full_name} ({listing.landlord.phone})"
            + f"\n\nView or print your receipt anytime: {receipt_url}"
            + "\n\nWakaless"
        )
        result = get_email_provider().send(renter.email, subject, body)
        return result.success
    except Exception:
        logger.exception("Failed to email receipt for rent_payment %s", rent_payment.id)
        return False
