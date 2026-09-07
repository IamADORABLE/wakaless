from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.availability import AvailabilityRequest, AvailabilityStatus
from app.models.listing import Listing, ListingStatus
from app.models.user import User, UserRole
from app.schemas.availability import AvailabilityRequestCreate, AvailabilityRequestOut, MyAvailabilityRequestOut
from app.services.notifications.messages import notify_admin_availability_request, notify_landlord_availability_check

router = APIRouter(prefix="/availability", tags=["availability"])


@router.post("/request", response_model=AvailabilityRequestOut)
def request_availability(
    payload: AvailabilityRequestCreate,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id, Listing.status == ListingStatus.live).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or no longer available")

    existing = (
        db.query(AvailabilityRequest)
        .filter(
            AvailabilityRequest.listing_id == listing.id,
            AvailabilityRequest.renter_id == user.id,
            AvailabilityRequest.status == AvailabilityStatus.pending,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending availability request for this listing")

    already_confirmed = (
        db.query(AvailabilityRequest)
        .filter(
            AvailabilityRequest.listing_id == listing.id,
            AvailabilityRequest.renter_id == user.id,
            AvailabilityRequest.status == AvailabilityStatus.confirmed,
            AvailabilityRequest.consumed_at.is_(None),
        )
        .first()
    )
    if already_confirmed:
        raise HTTPException(status_code=400, detail="Availability is already confirmed. You can pay now")

    request = AvailabilityRequest(listing_id=listing.id, renter_id=user.id)
    db.add(request)
    db.flush()

    email_sent_at, sms_sent_at = notify_landlord_availability_check(listing, user)
    request.landlord_email_sent_at = email_sent_at
    request.landlord_sms_sent_at = sms_sent_at

    db.commit()
    db.refresh(request)

    notify_admin_availability_request(listing, user)

    return AvailabilityRequestOut.model_validate(request)


@router.get("/mine", response_model=list[MyAvailabilityRequestOut])
def my_availability_requests(user: User = Depends(require_role(UserRole.renter)), db: Session = Depends(get_db)):
    """Every listing this renter has asked about, and whether it's still
    available: their own request status (pending/confirmed/rejected) plus
    the listing's current status (still live, already rented, expired)."""
    requests = (
        db.query(AvailabilityRequest)
        .filter(AvailabilityRequest.renter_id == user.id)
        .order_by(AvailabilityRequest.requested_at.desc())
        .all()
    )
    return [
        MyAvailabilityRequestOut(
            id=r.id, listing_id=r.listing_id, listing_title=r.listing.title,
            listing_area=r.listing.area, listing_status=r.listing.status,
            status=r.status, requested_at=r.requested_at,
            rejection_reason=r.rejection_reason, consumed_at=r.consumed_at,
        )
        for r in requests
    ]


@router.get("/status/{listing_id}", response_model=AvailabilityRequestOut | None)
def get_availability_status(
    listing_id: str,
    user: User = Depends(require_role(UserRole.renter)),
    db: Session = Depends(get_db),
):
    request = (
        db.query(AvailabilityRequest)
        .filter(AvailabilityRequest.listing_id == listing_id, AvailabilityRequest.renter_id == user.id)
        .order_by(AvailabilityRequest.requested_at.desc())
        .first()
    )
    if not request:
        return None
    return AvailabilityRequestOut.model_validate(request)
