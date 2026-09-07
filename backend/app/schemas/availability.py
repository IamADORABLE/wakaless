from datetime import datetime

from pydantic import BaseModel

from app.models.availability import AvailabilityStatus
from app.models.listing import ListingStatus


class AvailabilityRequestCreate(BaseModel):
    listing_id: str


class AvailabilityRequestOut(BaseModel):
    id: str
    listing_id: str
    status: AvailabilityStatus
    requested_at: datetime
    rejection_reason: str | None = None

    model_config = {"from_attributes": True}


class MyAvailabilityRequestOut(BaseModel):
    id: str
    listing_id: str
    listing_title: str
    listing_area: str
    listing_status: ListingStatus
    status: AvailabilityStatus
    requested_at: datetime
    rejection_reason: str | None = None
    consumed_at: datetime | None = None


class AvailabilityQueueItem(BaseModel):
    id: str
    listing_id: str
    listing_title: str
    renter_name: str
    renter_phone: str
    requested_at: datetime


class AvailabilityReview(BaseModel):
    approve: bool
    rejection_reason: str | None = None
