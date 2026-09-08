from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.availability import AvailabilityRequest, AvailabilityStatus
from app.models.listing import Listing, ListingStatus
from app.models.chat import ChatMessage
from app.models.rent_payment import PayoutStatus, RentPayment
from app.models.user import User, UserRole
from app.models.verification import LandlordVerification, VerificationStatus
from app.schemas.availability import AvailabilityQueueItem, AvailabilityRequestOut, AvailabilityReview
from app.schemas.chat import AdminChatThreadOut, ChatMessageOut
from app.schemas.listing import ListingDetailOut, ListingReview
from app.schemas.rent_payment import AdminInspectionItem, AdminTransactionItem
from app.schemas.user import (
    AdminUserOut,
    PayoutMarkPaid,
    PayoutQueueItem,
    VerificationOut,
    VerificationQueueItem,
    VerificationReview,
)
from app.services.scheduler import run_reminder_and_expiry_check

router = APIRouter(prefix="/admin", tags=["admin"])


def _out(listing: Listing) -> ListingDetailOut:
    v = listing.landlord.verification
    return ListingDetailOut(
        id=listing.id, title=listing.title, photos=listing.photos, area=listing.area,
        rent_amount_ngn=listing.rent_amount_ngn, rent_duration_months=listing.rent_duration_months,
        agreement_fee_ngn=listing.agreement_fee_ngn,
        status=listing.status, verified_landlord=bool(v and v.status.value == "verified"),
        description=listing.description, created_at=listing.created_at,
    )


@router.get("/review-queue", response_model=list[ListingDetailOut])
def review_queue(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """
    Manual review queue for ownership documents, per the brief's MVP scope
    ("manual review at MVP stage; automate later"). A dedicated admin UI page
    consumes this + POST /admin/listings/{id}/review.
    """
    listings = (
        db.query(Listing)
        .filter(Listing.status == ListingStatus.pending_review)
        .order_by(Listing.created_at.asc())
        .all()
    )
    return [_out(l) for l in listings]


@router.get("/listings/{listing_id}/ownership-doc")
def get_ownership_doc(listing_id: str, admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"ownership_doc_url": listing.ownership_doc_url}


@router.post("/listings/{listing_id}/review", response_model=ListingDetailOut)
def review_listing(
    listing_id: str,
    payload: ListingReview,
    admin: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.pending_review:
        raise HTTPException(status_code=400, detail="This listing is not awaiting review")

    if payload.approve:
        listing.status = ListingStatus.live
        listing.approved_at = datetime.utcnow()
        listing.rejection_reason = None
    else:
        listing.status = ListingStatus.rejected
        listing.rejection_reason = payload.rejection_reason or "Ownership document did not pass review."

    db.commit()
    db.refresh(listing)
    return _out(listing)


@router.get("/verification-queue", response_model=list[VerificationQueueItem])
def verification_queue(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """
    Manual review queue: there's no automated identity-verification
    provider, so every landlord's photo is checked here by an admin before
    the account is marked "verified".
    """
    verifications = (
        db.query(LandlordVerification)
        .filter(LandlordVerification.status == VerificationStatus.pending)
        .order_by(LandlordVerification.submitted_at.asc())
        .all()
    )
    return [
        VerificationQueueItem(
            id=v.id, user_id=v.user_id, full_name=v.user.full_name,
            phone=v.user.phone, email=v.user.email,
            photo_url=v.photo_url, submitted_at=v.submitted_at,
        )
        for v in verifications
    ]


@router.post("/verifications/{verification_id}/review", response_model=VerificationOut)
def review_verification(
    verification_id: str,
    payload: VerificationReview,
    admin: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    verification = db.query(LandlordVerification).filter(LandlordVerification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    if verification.status != VerificationStatus.pending:
        raise HTTPException(status_code=400, detail="This verification is not awaiting review")

    if payload.approve:
        verification.status = VerificationStatus.verified
        verification.verified_at = datetime.utcnow()
        verification.failure_reason = None
    else:
        verification.status = VerificationStatus.failed
        verification.failure_reason = payload.rejection_reason or "Photo did not pass review."

    db.commit()
    db.refresh(verification)
    return VerificationOut.model_validate(verification)


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    role: UserRole | None = None,
    verification_status: VerificationStatus | None = None,
    admin: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    results = [
        AdminUserOut(
            id=u.id, full_name=u.full_name, phone=u.phone, email=u.email, role=u.role,
            phone_verified=u.phone_verified, email_verified=u.email_verified, created_at=u.created_at,
            verification_status=u.verification.status if u.verification else None,
            listings_count=len(u.listings),
        )
        for u in users
    ]
    if verification_status:
        # A landlord with no verification row yet is effectively "unverified".
        # There's no separate DB row for that state (see LandlordVerification).
        results = [r for r in results if (r.verification_status or VerificationStatus.unverified) == verification_status]
    return results


@router.get("/availability-queue", response_model=list[AvailabilityQueueItem])
def availability_queue(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """
    A renter wants to pay for a listing; the landlord has been emailed/texted
    to confirm it's still available, but an admin still has to manually
    confirm before the renter is allowed to pay.
    """
    requests = (
        db.query(AvailabilityRequest)
        .filter(AvailabilityRequest.status == AvailabilityStatus.pending)
        .order_by(AvailabilityRequest.requested_at.asc())
        .all()
    )
    return [
        AvailabilityQueueItem(
            id=r.id, listing_id=r.listing_id, listing_title=r.listing.title,
            renter_name=r.renter.full_name, renter_phone=r.renter.phone, requested_at=r.requested_at,
        )
        for r in requests
    ]


@router.post("/availability-requests/{request_id}/review", response_model=AvailabilityRequestOut)
def review_availability_request(
    request_id: str,
    payload: AvailabilityReview,
    admin: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    request = db.query(AvailabilityRequest).filter(AvailabilityRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Availability request not found")
    if request.status != AvailabilityStatus.pending:
        raise HTTPException(status_code=400, detail="This request is not awaiting review")

    if payload.approve:
        request.status = AvailabilityStatus.confirmed
        request.rejection_reason = None
    else:
        request.status = AvailabilityStatus.rejected
        request.rejection_reason = payload.rejection_reason or "Landlord confirmed the property is no longer available."
        listing = db.query(Listing).filter(Listing.id == request.listing_id).first()
        if listing and listing.status == ListingStatus.live:
            listing.status = ListingStatus.rented

    request.resolved_at = datetime.utcnow()
    request.resolved_by_admin_id = admin.id
    db.commit()
    db.refresh(request)
    return AvailabilityRequestOut.model_validate(request)


@router.get("/payouts-queue", response_model=list[PayoutQueueItem])
def payouts_queue(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    rows = (
        db.query(RentPayment)
        .filter(RentPayment.payout_status == PayoutStatus.awaiting_payout)
        .order_by(RentPayment.paid_at.asc())
        .all()
    )
    return [
        PayoutQueueItem(
            rent_payment_id=rp.id, listing_title=rp.listing.title, landlord_name=rp.listing.landlord.full_name,
            bank_name=rp.listing.landlord.bank_name, bank_account_number=rp.listing.landlord.bank_account_number,
            bank_account_name=rp.listing.landlord.bank_account_name, rent_amount_ngn=rp.rent_amount_ngn,
            agreement_fee_ngn=rp.agreement_fee_ngn,
            commission_ngn=rp.commission_ngn, landlord_payout_ngn=rp.landlord_payout_ngn, paid_at=rp.paid_at,
            is_renewal=rp.is_renewal, inspection_confirmed_at=rp.inspection_confirmed_at,
        )
        for rp in rows
    ]


@router.get("/inspections", response_model=list[AdminInspectionItem])
def inspections(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """Every first-time tenancy and whether the renter has confirmed they
    inspected the house and are satisfied. Renewals don't need this."""
    rows = (
        db.query(RentPayment)
        .filter(RentPayment.is_renewal.is_(False))
        .order_by(RentPayment.paid_at.desc())
        .all()
    )
    return [
        AdminInspectionItem(
            id=rp.id, listing_title=rp.listing.title, renter_name=rp.renter.full_name,
            renter_phone=rp.renter.phone, landlord_name=rp.listing.landlord.full_name,
            paid_at=rp.paid_at, inspection_confirmed_at=rp.inspection_confirmed_at,
            payout_status=rp.payout_status.value,
        )
        for rp in rows
    ]


@router.post("/payouts/{rent_payment_id}/mark-paid")
def mark_payout_paid(
    rent_payment_id: str,
    payload: PayoutMarkPaid,
    admin: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Rent payment not found")
    if rp.payout_status == PayoutStatus.paid_out:
        raise HTTPException(status_code=400, detail="This payout was already marked paid")
    if not rp.is_renewal and not rp.inspection_confirmed_at:
        raise HTTPException(
            status_code=400,
            detail="The renter hasn't confirmed they inspected the house and are satisfied yet. Check the Inspections queue.",
        )

    rp.payout_status = PayoutStatus.paid_out
    rp.payout_reference = payload.payout_reference
    rp.payout_paid_at = datetime.utcnow()
    db.commit()
    return {"status": "paid_out"}


@router.post("/run-reminders")
def run_reminders(admin: User = Depends(require_role(UserRole.admin))):
    """Manual escape hatch for the same job the background scheduler runs daily."""
    run_reminder_and_expiry_check()
    return {"status": "ran"}


@router.get("/transactions", response_model=list[AdminTransactionItem])
def list_transactions(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """Full ledger of every rent payment on the platform, for financial oversight."""
    rows = db.query(RentPayment).order_by(RentPayment.paid_at.desc()).all()
    return [
        AdminTransactionItem(
            id=rp.id, listing_title=rp.listing.title,
            renter_name=rp.renter.full_name, renter_phone=rp.renter.phone,
            landlord_name=rp.listing.landlord.full_name, landlord_phone=rp.listing.landlord.phone,
            rent_amount_ngn=rp.rent_amount_ngn, agreement_fee_ngn=rp.agreement_fee_ngn,
            commission_ngn=rp.commission_ngn, total_paid_ngn=rp.total_paid_ngn,
            landlord_payout_ngn=rp.landlord_payout_ngn, payout_status=rp.payout_status.value,
            status=rp.status, paid_at=rp.paid_at, start_date=rp.start_date, end_date=rp.end_date,
        )
        for rp in rows
    ]


@router.get("/chat-threads", response_model=list[AdminChatThreadOut])
def list_all_chat_threads(admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """Every renter-landlord chat thread on the platform, for oversight. Read-only."""
    rows = db.query(RentPayment).order_by(RentPayment.paid_at.desc()).all()
    threads = []
    for rp in rows:
        messages = db.query(ChatMessage).filter(ChatMessage.rent_payment_id == rp.id).order_by(ChatMessage.created_at.desc()).all()
        last = messages[0] if messages else None
        threads.append(AdminChatThreadOut(
            rent_payment_id=rp.id, listing_id=rp.listing_id, listing_title=rp.listing.title,
            renter_name=rp.renter.full_name, landlord_name=rp.listing.landlord.full_name,
            message_count=len(messages),
            last_message_at=last.created_at if last else None,
            last_message_preview=last.body[:140] if last else None,
        ))
    return threads


@router.get("/chat-threads/{rent_payment_id}/messages", response_model=list[ChatMessageOut])
def get_chat_thread_messages(rent_payment_id: str, admin: User = Depends(require_role(UserRole.admin)), db: Session = Depends(get_db)):
    """Read-only view of any thread's messages, for oversight. Admins can't send here."""
    rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    messages = db.query(ChatMessage).filter(ChatMessage.rent_payment_id == rent_payment_id).order_by(ChatMessage.created_at.asc()).all()
    return [
        ChatMessageOut(id=m.id, sender_id=m.sender_id, sender_role=m.sender.role, body=m.body, created_at=m.created_at)
        for m in messages
    ]
