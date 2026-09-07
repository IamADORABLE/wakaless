import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class RentPaymentStatus(str, enum.Enum):
    active = "active"
    ended = "ended"


class PayoutStatus(str, enum.Enum):
    awaiting_payout = "awaiting_payout"
    paid_out = "paid_out"


class RentPayment(Base):
    """A renter's paid tenancy on one listing. Reveals landlord contact, opens chat."""
    __tablename__ = "rent_payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    renter_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False, index=True)
    availability_request_id = Column(String, ForeignKey("availability_requests.id"), nullable=True)

    rent_amount_ngn = Column(Integer, nullable=False)
    rent_duration_months = Column(Integer, nullable=False)
    payment_reference = Column(String, nullable=True)  # Paystack reference (or mock ref)

    # First payment on a listing charges rent + agreement fee + commission,
    # all added on top and paid by the renter; the landlord gets rent +
    # agreement fee in full, the platform keeps the commission. A renewal
    # charges rent only (agreement_fee_ngn/this call's commission_ngn are 0)
    # and the landlord gets the full rent. See PayoutStatus below.
    agreement_fee_ngn = Column(Integer, nullable=False, default=0)
    total_paid_ngn = Column(Integer, nullable=False)

    paid_at = Column(DateTime, default=datetime.utcnow)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(RentPaymentStatus), default=RentPaymentStatus.active, nullable=False)

    reminder_1m_sent_at = Column(DateTime, nullable=True)
    reminder_2w_sent_at = Column(DateTime, nullable=True)

    # Frozen at payment time so a later config change never rewrites history.
    commission_ngn = Column(Integer, nullable=False)
    landlord_payout_ngn = Column(Integer, nullable=False)
    payout_status = Column(Enum(PayoutStatus), default=PayoutStatus.awaiting_payout, nullable=False)
    payout_reference = Column(String, nullable=True)
    payout_paid_at = Column(DateTime, nullable=True)

    # Renewals extend a tenancy the renter already occupies, so they skip
    # the inspection gate below entirely. A first payment holds the
    # landlord's payout until the renter ticks "the house is good" in My
    # rentals — an admin can't mark it paid out before that (see
    # POST /rent-payments/{id}/confirm-inspection and the payouts-queue gate).
    is_renewal = Column(Boolean, default=False, nullable=False)
    inspection_confirmed_at = Column(DateTime, nullable=True)

    renter = relationship("User", back_populates="rent_payments")
    listing = relationship("Listing", back_populates="rent_payments")
