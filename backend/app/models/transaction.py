import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    rent_payment = "rent_payment"
    additional_listing_fee = "additional_listing_fee"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class Transaction(Base):
    """Payment record for anything charged through the platform (rent payments, listing fees)."""
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    amount_ngn = Column(Integer, nullable=False)
    provider = Column(String, nullable=False)          # e.g. "paystack" or "mock"
    provider_reference = Column(String, nullable=True)
    raw_response = Column(JSON, nullable=True)

    related_listing_id = Column(String, ForeignKey("listings.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")
