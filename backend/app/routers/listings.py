from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user, require_role
from app.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User, UserRole
from app.models.verification import VerificationStatus
from app.schemas.listing import (
    AdditionalListingFeeInitiateOut,
    AdditionalListingFeeVerify,
    ListingCardOut,
    ListingCreate,
    ListingDetailOut,
    ListingStatusUpdate,
)
from app.services.notifications.messages import notify_admin_new_listing
from app.services.payments import get_payment_provider
from app.services.payouts import compute_commission_ngn
from app.services.storage import save_upload

router = APIRouter(prefix="/listings", tags=["listings"])
settings = get_settings()


def _callback_url(**params) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{settings.frontend_origin}/payments/callback?{query}"


def _unused_paid_fee(db: Session, user_id: str) -> Transaction | None:
    """An already-paid additional-listing-fee transaction not yet spent on a
    listing (related_listing_id doubles as the "consumed" marker: it's set
    the moment a listing is created off the back of this fee)."""
    return (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.additional_listing_fee,
            Transaction.status == TransactionStatus.success,
            Transaction.related_listing_id.is_(None),
        )
        .order_by(Transaction.completed_at.asc())
        .first()
    )


def _verified_badge(listing: Listing) -> bool:
    v = listing.landlord.verification
    return bool(v and v.status == VerificationStatus.verified)


def _card_out(listing: Listing) -> ListingCardOut:
    return ListingCardOut(
        id=listing.id, title=listing.title, photos=listing.photos, area=listing.area,
        rent_amount_ngn=listing.rent_amount_ngn, rent_duration_months=listing.rent_duration_months,
        agreement_fee_ngn=listing.agreement_fee_ngn,
        status=listing.status, verified_landlord=_verified_badge(listing),
    )


def _detail_out(listing: Listing) -> ListingDetailOut:
    return ListingDetailOut(
        **_card_out(listing).model_dump(),
        description=listing.description, created_at=listing.created_at,
        video_url=listing.video_url,
        commission_ngn=compute_commission_ngn(listing.rent_amount_ngn),
    )


@router.get("", response_model=list[ListingCardOut])
def browse_listings(
    area: str | None = Query(default=None, description="Filter by area, e.g. 'Lekki'"),
    max_rent: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    """Public, free browsing. No auth required. Only shows live listings."""
    q = db.query(Listing).filter(Listing.status == ListingStatus.live)
    if area:
        q = q.filter(Listing.area.ilike(f"%{area}%"))
    if max_rent:
        q = q.filter(Listing.rent_amount_ngn <= max_rent)

    return [_card_out(listing) for listing in q.order_by(Listing.created_at.desc()).all()]


@router.get("/rent-duration-options")
def rent_duration_options():
    return {"options": settings.rent_duration_options()}


@router.get("/{listing_id}", response_model=ListingDetailOut)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Public detail view. Price breakdown and area, but NOT exact address or contact."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _detail_out(listing)


@router.post("/photo", summary="Upload one listing photo, returns its storage URL")
def upload_photo(file: UploadFile = File(...), user: User = Depends(require_role(UserRole.landlord))):
    return {"url": save_upload(file, subfolder="listings")}


@router.post("/video", summary="Upload an optional walkthrough video, returns its storage URL")
def upload_video(file: UploadFile = File(...), user: User = Depends(require_role(UserRole.landlord))):
    return {"url": save_upload(file, subfolder="listings-video", resource_type="video")}


@router.post("/ownership-doc", summary="Upload proof of ownership (C of O / receipt / utility bill)")
def upload_ownership_doc(file: UploadFile = File(...), user: User = Depends(require_role(UserRole.landlord))):
    return {"url": save_upload(file, subfolder="ownership-docs")}


@router.post("", response_model=ListingDetailOut)
def create_listing(
    payload: ListingCreate,
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    if not user.verification or user.verification.status != VerificationStatus.verified:
        raise HTTPException(
            status_code=403,
            detail="Submit and get approved for identity verification (upload a photo of yourself) before creating a listing.",
        )

    if payload.rent_duration_months not in settings.rent_duration_options():
        raise HTTPException(
            status_code=400,
            detail=f"rent_duration_months must be one of {settings.rent_duration_options()}",
        )

    # First listing is free; 2nd+ costs a one-time fee, paid up front via
    # POST /listings/additional-fee/initiate + /verify before this call.
    existing_count = db.query(Listing).filter(Listing.landlord_id == user.id).count()
    fee_txn = None
    if existing_count > 0:
        fee_txn = _unused_paid_fee(db, user.id)
        if not fee_txn:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"An additional listing fee of NGN {settings.additional_listing_fee_ngn:,} is required "
                    "before creating another listing. Pay it via POST /listings/additional-fee/initiate."
                ),
            )

    listing = Listing(
        landlord_id=user.id,
        title=payload.title,
        description=payload.description,
        photos=payload.photos,
        video_url=payload.video_url,
        rent_amount_ngn=payload.rent_amount_ngn,
        rent_duration_months=payload.rent_duration_months,
        agreement_fee_ngn=payload.agreement_fee_ngn,
        area=payload.area,
        address=payload.address,
        lat=payload.lat,
        lng=payload.lng,
        ownership_doc_url=payload.ownership_doc_url,
        status=ListingStatus.pending_review,
        expires_at=datetime.utcnow() + timedelta(days=settings.listing_expiry_days),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    if fee_txn:
        fee_txn.related_listing_id = listing.id
        db.commit()

    notify_admin_new_listing(listing)

    return _detail_out(listing)


@router.post("/additional-fee/initiate", response_model=AdditionalListingFeeInitiateOut)
def initiate_additional_listing_fee(
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    """Pay the one-time fee for a 2nd+ listing (the 1st is free). Call this
    before POST /listings when that endpoint has already rejected you with
    402 — once verified, the fee is available for exactly one listing."""
    existing_count = db.query(Listing).filter(Listing.landlord_id == user.id).count()
    if existing_count == 0:
        raise HTTPException(status_code=400, detail="Your first listing is free, no fee is required yet.")
    if _unused_paid_fee(db, user.id):
        raise HTTPException(status_code=400, detail="You already have a paid fee ready for your next listing.")

    amount_ngn = settings.additional_listing_fee_ngn
    provider = get_payment_provider()
    initiated = provider.initiate(
        amount_ngn=amount_ngn,
        email=user.email,
        metadata={"landlord_id": user.id, "purpose": "additional_listing_fee"},
        callback_url=_callback_url(kind="additional_listing_fee"),
    )

    txn = Transaction(
        user_id=user.id, type=TransactionType.additional_listing_fee, status=TransactionStatus.pending,
        amount_ngn=amount_ngn, provider=settings.payment_provider, provider_reference=initiated.reference,
    )
    db.add(txn)
    db.commit()

    return AdditionalListingFeeInitiateOut(
        provider=settings.payment_provider, authorization_url=initiated.authorization_url,
        reference=initiated.reference, amount_ngn=amount_ngn,
    )


@router.post("/additional-fee/verify")
def verify_additional_listing_fee(
    payload: AdditionalListingFeeVerify,
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    # Idempotency: same reasoning as rent-payments verify — a redirect
    # callback can fire more than once.
    txn = (
        db.query(Transaction)
        .filter(Transaction.provider_reference == payload.reference, Transaction.user_id == user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status_code=404, detail="No matching payment found for this reference")
    if txn.status == TransactionStatus.success:
        return {"status": "success"}

    provider = get_payment_provider()
    verified = provider.verify(payload.reference)
    if not verified.success:
        txn.status = TransactionStatus.failed
        db.commit()
        raise HTTPException(status_code=402, detail="Payment was not successful")

    txn.status = TransactionStatus.success
    txn.completed_at = datetime.utcnow()
    txn.raw_response = verified.raw
    db.commit()
    return {"status": "success"}


@router.get("/mine/list", response_model=list[ListingDetailOut])
def my_listings(user: User = Depends(require_role(UserRole.landlord)), db: Session = Depends(get_db)):
    listings = db.query(Listing).filter(Listing.landlord_id == user.id).order_by(Listing.created_at.desc()).all()
    return [_detail_out(l) for l in listings]


@router.patch("/{listing_id}/status", response_model=ListingDetailOut)
def update_listing_status(
    listing_id: str,
    payload: ListingStatusUpdate,
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    """Landlord marks their own listing as rented, or re-confirms an expired one."""
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.landlord_id == user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    allowed_transitions = {
        ListingStatus.rented: {ListingStatus.live, ListingStatus.expired},
        ListingStatus.live: {ListingStatus.expired},  # confirming still-available
    }
    if payload.status not in allowed_transitions or listing.status not in allowed_transitions[payload.status]:
        raise HTTPException(status_code=400, detail=f"Cannot move listing from {listing.status} to {payload.status}")

    listing.status = payload.status
    if payload.status == ListingStatus.live:
        listing.expires_at = datetime.utcnow() + timedelta(days=settings.listing_expiry_days)
    db.commit()
    db.refresh(listing)

    return _detail_out(listing)
