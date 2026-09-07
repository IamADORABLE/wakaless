from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import require_role
from app.database import get_db
from app.models.availability import AvailabilityRequest, AvailabilityStatus
from app.models.listing import Listing, ListingStatus
from app.models.rent_payment import RentPayment, RentPaymentStatus
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User, UserRole
from app.schemas.rent_payment import (
    ReceiptOut,
    RentPaymentInitiate,
    RentPaymentInitiateOut,
    RentPaymentOut,
    RentPaymentVerify,
)
from app.services.notifications.messages import notify_renter_receipt
from app.services.payments import get_payment_provider
from app.services.payouts import compute_commission_ngn

router = APIRouter(prefix="/rent-payments", tags=["rent-payments"])
settings = get_settings()


def _callback_url(**params) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{settings.frontend_origin}/payments/callback?{query}"


def _out(rp: RentPayment) -> RentPaymentOut:
    listing = rp.listing
    return RentPaymentOut(
        id=rp.id, listing_id=listing.id, address=listing.address, lat=listing.lat, lng=listing.lng,
        landlord_phone=listing.landlord.phone, landlord_name=listing.landlord.full_name,
        listing_title=listing.title, rent_amount_ngn=rp.rent_amount_ngn,
        rent_duration_months=rp.rent_duration_months, start_date=rp.start_date, end_date=rp.end_date,
        status=rp.status, is_renewal=rp.is_renewal, inspection_confirmed_at=rp.inspection_confirmed_at,
    )


@router.post("/initiate", response_model=RentPaymentInitiateOut)
def initiate_rent_payment(
    payload: RentPaymentInitiate,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id, Listing.status == ListingStatus.live).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or no longer available")

    # Already an active tenancy on this listing? Don't charge again.
    # The frontend should fetch it from GET /rent-payments/mine instead.
    existing = (
        db.query(RentPayment)
        .filter(RentPayment.renter_id == user.id, RentPayment.listing_id == listing.id, RentPayment.status == RentPaymentStatus.active)
        .first()
    )
    if existing:
        return RentPaymentInitiateOut(
            provider="none", authorization_url=None, reference="already-active",
            rent_amount_ngn=0, agreement_fee_ngn=0, commission_ngn=0, total_amount_ngn=0,
            rent_duration_months=existing.rent_duration_months,
        )

    availability = (
        db.query(AvailabilityRequest)
        .filter(
            AvailabilityRequest.listing_id == listing.id,
            AvailabilityRequest.renter_id == user.id,
            AvailabilityRequest.status == AvailabilityStatus.confirmed,
            AvailabilityRequest.consumed_at.is_(None),
        )
        .order_by(AvailabilityRequest.requested_at.desc())
        .first()
    )
    if not availability:
        raise HTTPException(
            status_code=400,
            detail="Availability must be confirmed before payment. See POST /availability/request",
        )

    # First payment on a listing: rent + agreement fee + commission, all
    # charged to the renter together. Renewals (see below) charge rent only.
    commission_ngn = compute_commission_ngn(listing.rent_amount_ngn)
    total_amount_ngn = listing.rent_amount_ngn + listing.agreement_fee_ngn + commission_ngn

    provider = get_payment_provider()
    initiated = provider.initiate(
        amount_ngn=total_amount_ngn,
        email=user.email,
        metadata={"listing_id": listing.id, "renter_id": user.id, "purpose": "rent_payment"},
        callback_url=_callback_url(kind="payment", listing_id=listing.id),
    )

    txn = Transaction(
        user_id=user.id, type=TransactionType.rent_payment, status=TransactionStatus.pending,
        amount_ngn=total_amount_ngn, provider=settings.payment_provider,
        provider_reference=initiated.reference, related_listing_id=listing.id,
    )
    db.add(txn)
    db.commit()

    return RentPaymentInitiateOut(
        provider=settings.payment_provider, authorization_url=initiated.authorization_url,
        reference=initiated.reference, rent_amount_ngn=listing.rent_amount_ngn,
        agreement_fee_ngn=listing.agreement_fee_ngn, commission_ngn=commission_ngn,
        total_amount_ngn=total_amount_ngn, rent_duration_months=listing.rent_duration_months,
    )


@router.post("/verify", response_model=RentPaymentOut)
def verify_rent_payment(
    payload: RentPaymentVerify,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    # Idempotency: the redirect-back callback can fire more than once (React
    # dev double-invoke, browser back/forward, a retried request). If this
    # reference already produced a RentPayment, return it instead of billing
    # a second tenancy record for the same charge.
    existing = db.query(RentPayment).filter(RentPayment.payment_reference == payload.reference).first()
    if existing:
        return _out(existing)

    txn = (
        db.query(Transaction)
        .filter(Transaction.provider_reference == payload.reference, Transaction.user_id == user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status_code=404, detail="No matching payment found for this reference")

    provider = get_payment_provider()
    verified = provider.verify(payload.reference)
    if not verified.success:
        txn.status = TransactionStatus.failed
        db.commit()
        raise HTTPException(status_code=402, detail="Payment was not successful")

    txn.status = TransactionStatus.success
    txn.completed_at = datetime.utcnow()
    txn.raw_response = verified.raw

    listing = db.query(Listing).filter(Listing.id == txn.related_listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing no longer exists")

    availability = (
        db.query(AvailabilityRequest)
        .filter(
            AvailabilityRequest.listing_id == listing.id,
            AvailabilityRequest.renter_id == user.id,
            AvailabilityRequest.status == AvailabilityStatus.confirmed,
            AvailabilityRequest.consumed_at.is_(None),
        )
        .order_by(AvailabilityRequest.requested_at.desc())
        .first()
    )

    # Same breakdown as initiate (deterministic from the listing). The
    # renter paid rent + agreement fee + commission; the landlord gets
    # rent + agreement fee in full, the platform keeps the commission.
    commission_ngn = compute_commission_ngn(listing.rent_amount_ngn)
    agreement_fee_ngn = listing.agreement_fee_ngn
    total_paid_ngn = listing.rent_amount_ngn + agreement_fee_ngn + commission_ngn
    start_date = datetime.utcnow()
    end_date = start_date + relativedelta(months=listing.rent_duration_months)

    rent_payment = RentPayment(
        renter_id=user.id, listing_id=listing.id,
        availability_request_id=availability.id if availability else None,
        rent_amount_ngn=listing.rent_amount_ngn, rent_duration_months=listing.rent_duration_months,
        agreement_fee_ngn=agreement_fee_ngn, total_paid_ngn=total_paid_ngn,
        payment_reference=payload.reference, start_date=start_date, end_date=end_date,
        commission_ngn=commission_ngn,
        landlord_payout_ngn=listing.rent_amount_ngn + agreement_fee_ngn,
    )
    db.add(rent_payment)
    if availability:
        availability.consumed_at = datetime.utcnow()
    listing.status = ListingStatus.rented

    db.commit()
    db.refresh(rent_payment)
    notify_renter_receipt(rent_payment)
    return _out(rent_payment)


@router.get("/mine", response_model=list[RentPaymentOut])
def my_rent_payments(user: User = Depends(require_role(UserRole.renter)), db: Session = Depends(get_db)):
    rows = (
        db.query(RentPayment)
        .filter(RentPayment.renter_id == user.id)
        .order_by(RentPayment.paid_at.desc())
        .all()
    )
    return [_out(rp) for rp in rows]


@router.post("/{rent_payment_id}/confirm-inspection", response_model=RentPaymentOut)
def confirm_inspection(
    rent_payment_id: str,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    """The renter ticking "the house is good" after meeting the landlord and
    seeing it in person. Until this happens, the landlord's payout is held
    (see the payouts-queue gate in admin.py) — a renewal never needs this,
    since the renter already occupies the place."""
    rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id, RentPayment.renter_id == user.id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Rent payment not found")
    if rp.is_renewal:
        raise HTTPException(status_code=400, detail="Renewals don't need an inspection confirmation")
    if rp.inspection_confirmed_at:
        raise HTTPException(status_code=400, detail="Already confirmed")

    rp.inspection_confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(rp)
    return _out(rp)


@router.get("/{rent_payment_id}/receipt", response_model=ReceiptOut)
def get_receipt(rent_payment_id: str, user: User = Depends(require_role(UserRole.renter)), db: Session = Depends(get_db)):
    rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id, RentPayment.renter_id == user.id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Rent payment not found")
    listing = rp.listing
    return ReceiptOut(
        id=rp.id, renter_name=user.full_name, landlord_name=listing.landlord.full_name,
        listing_title=listing.title, address=listing.address, rent_amount_ngn=rp.rent_amount_ngn,
        agreement_fee_ngn=rp.agreement_fee_ngn, commission_ngn=rp.commission_ngn,
        total_paid_ngn=rp.total_paid_ngn, rent_duration_months=rp.rent_duration_months,
        start_date=rp.start_date, end_date=rp.end_date, payment_reference=rp.payment_reference,
        paid_at=rp.paid_at,
    )


@router.post("/{rent_payment_id}/renew/initiate", response_model=RentPaymentInitiateOut)
def initiate_renewal(
    rent_payment_id: str,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    """Pay for the next term on the same listing. Bypasses the availability
    gate since the renter already occupies it. Renewals charge rent only:
    no agreement fee (already paid at move-in) and no commission."""
    old_rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id, RentPayment.renter_id == user.id).first()
    if not old_rp:
        raise HTTPException(status_code=404, detail="Rent payment not found")
    if old_rp.status != RentPaymentStatus.active:
        raise HTTPException(status_code=400, detail="This tenancy has already ended")

    provider = get_payment_provider()
    initiated = provider.initiate(
        amount_ngn=old_rp.rent_amount_ngn,
        email=user.email,
        metadata={"listing_id": old_rp.listing_id, "renter_id": user.id, "purpose": "renew", "prior_rent_payment_id": old_rp.id},
        callback_url=_callback_url(kind="renew", rent_payment_id=old_rp.id),
    )
    txn = Transaction(
        user_id=user.id, type=TransactionType.rent_payment, status=TransactionStatus.pending,
        amount_ngn=old_rp.rent_amount_ngn, provider=settings.payment_provider,
        provider_reference=initiated.reference, related_listing_id=old_rp.listing_id,
    )
    db.add(txn)
    db.commit()

    return RentPaymentInitiateOut(
        provider=settings.payment_provider, authorization_url=initiated.authorization_url,
        reference=initiated.reference, rent_amount_ngn=old_rp.rent_amount_ngn,
        agreement_fee_ngn=0, commission_ngn=0, total_amount_ngn=old_rp.rent_amount_ngn,
        rent_duration_months=old_rp.rent_duration_months,
    )


@router.post("/{rent_payment_id}/renew/verify", response_model=RentPaymentOut)
def verify_renewal(
    rent_payment_id: str,
    payload: RentPaymentVerify,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    old_rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id, RentPayment.renter_id == user.id).first()
    if not old_rp:
        raise HTTPException(status_code=404, detail="Rent payment not found")

    # Idempotency: same reasoning as verify_rent_payment. A repeated call
    # with the same reference (e.g. the redirect callback firing twice)
    # must not extend the tenancy a second time. Check before the
    # active-status guard, since the first call already flips old_rp to
    # "ended", which would otherwise 400 a harmless duplicate call.
    existing = db.query(RentPayment).filter(RentPayment.payment_reference == payload.reference).first()
    if existing:
        return _out(existing)

    if old_rp.status != RentPaymentStatus.active:
        raise HTTPException(status_code=400, detail="This tenancy has already ended")

    txn = (
        db.query(Transaction)
        .filter(Transaction.provider_reference == payload.reference, Transaction.user_id == user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status_code=404, detail="No matching payment found for this reference")

    provider = get_payment_provider()
    verified = provider.verify(payload.reference)
    if not verified.success:
        txn.status = TransactionStatus.failed
        db.commit()
        raise HTTPException(status_code=402, detail="Payment was not successful")

    txn.status = TransactionStatus.success
    txn.completed_at = datetime.utcnow()
    txn.raw_response = verified.raw

    new_start = old_rp.end_date
    new_end = new_start + relativedelta(months=old_rp.rent_duration_months)

    old_rp.status = RentPaymentStatus.ended
    new_rp = RentPayment(
        renter_id=user.id, listing_id=old_rp.listing_id,
        rent_amount_ngn=old_rp.rent_amount_ngn, rent_duration_months=old_rp.rent_duration_months,
        agreement_fee_ngn=0, total_paid_ngn=old_rp.rent_amount_ngn,
        payment_reference=payload.reference, start_date=new_start, end_date=new_end,
        commission_ngn=0, landlord_payout_ngn=old_rp.rent_amount_ngn, is_renewal=True,
    )
    db.add(new_rp)
    db.commit()
    db.refresh(new_rp)
    notify_renter_receipt(new_rp)
    return _out(new_rp)
