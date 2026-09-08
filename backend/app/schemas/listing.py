from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.listing import ListingStatus


class ListingCreate(BaseModel):
    title: str = Field(min_length=5, max_length=140)
    description: str | None = Field(default=None, max_length=4000)
    photos: list[str] = Field(default_factory=list, description="Storage URLs, at least 1 required")
    rent_amount_ngn: int = Field(gt=0, description="Total rent for rent_duration_months")
    rent_duration_months: int = Field(gt=0, description="e.g. 6, 12, 24. See GET /listings/rent-duration-options")
    agreement_fee_ngn: int = Field(ge=0, default=0)
    area: str = Field(min_length=2, max_length=140, description='e.g. "Lekki Phase 1"')
    address: str = Field(min_length=5, description="Exact address; only shown after payment")
    lat: float | None = None
    lng: float | None = None
    ownership_doc_url: str = Field(description="C of O / receipt / utility bill upload")
    video_url: str | None = Field(default=None, description="Optional walkthrough video upload")

    @field_validator("photos")
    @classmethod
    def photo_count(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("At least one listing photo is required")
        if len(v) > 10:
            raise ValueError("At most 10 listing photos are allowed")
        return v


class ListingCardOut(BaseModel):
    """Public, pre-payment view. No exact address or landlord contact."""
    id: str
    title: str
    photos: list[str]
    area: str
    rent_amount_ngn: int
    rent_duration_months: int
    agreement_fee_ngn: int
    status: ListingStatus
    verified_landlord: bool

    model_config = {"from_attributes": True}


class ListingDetailOut(ListingCardOut):
    description: str | None
    created_at: datetime
    video_url: str | None = None
    # The one-time commission a first payment on this listing would add.
    # Renewals don't charge it (see RentPayment.commission_ngn).
    commission_ngn: int = 0
    # Exact location + landlord contact are deliberately absent here.
    # See RentPaymentOut (schemas/rent_payment.py), returned only after a paid RentPayment.


class AdditionalListingFeeInitiateOut(BaseModel):
    """What the frontend needs to open the payment provider's checkout for
    a landlord's 2nd+ listing fee (the 1st listing is free)."""
    provider: str
    authorization_url: str | None = None
    reference: str
    amount_ngn: int


class AdditionalListingFeeVerify(BaseModel):
    reference: str


class ListingReview(BaseModel):
    approve: bool
    rejection_reason: str | None = None


class ListingStatusUpdate(BaseModel):
    status: ListingStatus
