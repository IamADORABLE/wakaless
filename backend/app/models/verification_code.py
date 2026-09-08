import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class VerificationPurpose(str, enum.Enum):
    verify_email = "verify_email"
    reset_password = "reset_password"


class VerificationCode(Base):
    """A one-time 6-digit code emailed to a user, for email verification or
    password reset. Stored hashed (like a password) so a DB read alone
    doesn't hand out working codes. Scoped by `purpose` so a code meant for
    one action can't be replayed for the other."""
    __tablename__ = "verification_codes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(Enum(VerificationPurpose), nullable=False)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
