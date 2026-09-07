import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ChatMessage(Base):
    """One message in the thread for a paid tenancy (thread key = rent_payment_id)."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rent_payment_id = Column(String, ForeignKey("rent_payments.id"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rent_payment = relationship("RentPayment")
    sender = relationship("User")
