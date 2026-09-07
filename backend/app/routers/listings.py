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
    ListingCardOut,
    ListingCreate,
    ListingDetailOut,
    ListingStatusUpdate,
)
from app.services.notifications.messages import notify_admin_new_listing
from app.services.payouts import compute_commission_ngn
from app.services.storage import save_upload

router = APIRouter(prefix="/listings", tags=["listings"])
settings = get_settings()


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
            detail="Submit and get approved for proof-of-ownership verification before creating a listing.",
        )

    if payload.rent_duration_months not in settings.rent_duration_options():
        raise HTTPException(
            status_code=400,
            detail=f"rent_duration_months must be one of {settings.rent_duration_options()}",
        )

    existing_count = db.query(Listing).filter(Listing.landlord_id == user.id).count()
    if existing_count > 0:
        # First listing is free; 2nd+ costs a one-time fee per the brief.
        # MVP: fee is recorded and expected to be settled via the same
        # rent-payment-style flow before the listing goes live. Wire the
        # actual charge call here once the payment provider is chosen.
        pending_fee = Transaction(
            user_id=user.id,
            type=TransactionType.additional_listing_fee,
            status=TransactionStatus.pending,
            amount_ngn=settings.additional_listing_fee_ngn,
            provider=settings.payment_provider,
        )
        db.add(pending_fee)

    listing = Listing(
        landlord_id=user.id,
        title=payload.title,
        description=payload.description,
        photos=payload.photos,
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

    notify_admin_new_listing(listing)

    return _detail_out(listing)


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
