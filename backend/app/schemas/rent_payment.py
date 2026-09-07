from datetime import datetime

from pydantic import BaseModel

from app.models.rent_payment import RentPaymentStatus


class RentPaymentInitiate(BaseModel):
    listing_id: str


class RentPaymentInitiateOut(BaseModel):
    """What the frontend needs to open the payment provider's checkout,
    plus the cost breakdown so it can be shown before redirecting."""
    provider: str
    authorization_url: str | None = None  # Paystack-hosted checkout, when using paystack
    reference: str
    rent_amount_ngn: int
    agreement_fee_ngn: int
    commission_ngn: int
    total_amount_ngn: int
    rent_duration_months: int


class RentPaymentVerify(BaseModel):
    reference: str


class RentPaymentOut(BaseModel):
    id: str
    listing_id: str
    address: str
    lat: float | None
    lng: float | None
    landlord_phone: str
    landlord_name: str
    listing_title: str
    rent_amount_ngn: int
    rent_duration_months: int
    start_date: datetime
    end_date: datetime
    status: RentPaymentStatus


class AdminTransactionItem(BaseModel):
    """One rent payment, for the admin's full transaction ledger."""
    id: str
    listing_title: str
    renter_name: str
    renter_phone: str
    landlord_name: str
    landlord_phone: str
    rent_amount_ngn: int
    agreement_fee_ngn: int
    commission_ngn: int
    total_paid_ngn: int
    landlord_payout_ngn: int
    payout_status: str
    status: RentPaymentStatus
    paid_at: datetime
    start_date: datetime
    end_date: datetime


class ReceiptOut(BaseModel):
    id: str
    renter_name: str
    landlord_name: str
    listing_title: str
    address: str
    rent_amount_ngn: int
    agreement_fee_ngn: int
    commission_ngn: int
    total_paid_ngn: int
    rent_duration_months: int
    start_date: datetime
    end_date: datetime
    payment_reference: str | None
    paid_at: datetime
