import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    renter = "renter"
    landlord = "landlord"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(Enum(UserRole), nullable=False, default=UserRole.renter)
    full_name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    phone_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Landlord payout details — for reference only, no automated transfer.
    # An admin manually bank-transfers the landlord's share and marks the
    # rent payment "paid out" (see RentPayment.payout_status).
    bank_name = Column(String, nullable=True)
    bank_account_number = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=True)

    verification = relationship(
        "LandlordVerification", back_populates="user", uselist=False,
        cascade="all, delete-orphan",
    )
    listings = relationship("Listing", back_populates="landlord", cascade="all, delete-orphan")
    rent_payments = relationship("RentPayment", back_populates="renter", cascade="all, delete-orphan")
