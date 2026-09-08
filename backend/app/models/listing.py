import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ListingStatus(str, enum.Enum):
    pending_review = "pending_review"   # awaiting admin review of ownership doc
    live = "live"                       # approved, visible in search
    rejected = "rejected"                # admin rejected the ownership doc
    rented = "rented"                    # landlord marked it taken
    expired = "expired"                  # auto-expired, awaiting landlord confirmation


class Listing(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    landlord_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photos = Column(JSON, default=list)  # list of storage URLs
    video_url = Column(String, nullable=True)  # optional walkthrough video

    # Money fields kept separate per the brief ("agreement fee entered separately from rent")
    rent_amount_ngn = Column(Integer, nullable=False)  # total rent for rent_duration_months, not necessarily annual
    rent_duration_months = Column(Integer, nullable=False)
    agreement_fee_ngn = Column(Integer, nullable=False, default=0)

    # Location
    area = Column(String, nullable=False)          # coarse, shown pre-payment e.g. "Lekki Phase 1"
    address = Column(String, nullable=True)         # exact, revealed only after rent payment
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    ownership_doc_url = Column(String, nullable=True)  # C of O / receipt / utility bill

    status = Column(Enum(ListingStatus), default=ListingStatus.pending_review, nullable=False)
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    landlord = relationship("User", back_populates="listings")
    rent_payments = relationship("RentPayment", back_populates="listing", cascade="all, delete-orphan")

    @property
    def is_verified_landlord_badge(self) -> bool:
        # Resolved in the router (needs the landlord's verification row);
        # kept here as a documented contract: never default this to True.
        raise NotImplementedError("compute from landlord.verification.status == verified")
