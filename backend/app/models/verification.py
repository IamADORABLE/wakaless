import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class VerificationStatus(str, enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    failed = "failed"


class LandlordVerification(Base):
    """
    One row per landlord ACCOUNT (not per listing).

    No automated identity-verification provider: a landlord uploads a photo
    of themselves and an admin manually approves or rejects it. Proof of
    ownership is collected separately, per listing (see Listing.ownership_doc_url) —
    every listing already requires it, so it'd be redundant to also collect
    it once at the account level.
    """
    __tablename__ = "landlord_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified, nullable=False)
    failure_reason = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)

    submitted_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="verification")
