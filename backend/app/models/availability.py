import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AvailabilityStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class AvailabilityRequest(Base):
    """
    A renter asking "is this still available?" before being allowed to pay.
    The landlord is notified by email + SMS, but an admin manually confirms
    or rejects — see POST /admin/availability-requests/{id}/review.
    """
    __tablename__ = "availability_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False, index=True)
    renter_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.pending, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_admin_id = Column(String, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    landlord_email_sent_at = Column(DateTime, nullable=True)
    landlord_sms_sent_at = Column(DateTime, nullable=True)

    # Set once a RentPayment is created off this confirmation, so it can't be reused.
    consumed_at = Column(DateTime, nullable=True)

    listing = relationship("Listing")
    renter = relationship("User", foreign_keys=[renter_id])
