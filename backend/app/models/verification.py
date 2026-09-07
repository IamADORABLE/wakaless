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
    One row per landlord ACCOUNT (not per listing) per the brief.

    No automated identity-verification provider: a landlord uploads proof of
    ownership (e.g. a utility bill, C of O, or tenancy agreement in their
    name) and an admin manually approves or rejects it.
    """
    __tablename__ = "landlord_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified, nullable=False)
    failure_reason = Column(Text, nullable=True)
    ownership_proof_url = Column(String, nullable=True)

    submitted_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="verification")
