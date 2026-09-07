from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserRole


class ChatMessageCreate(BaseModel):
    body: str


class ChatMessageOut(BaseModel):
    id: str
    sender_id: str
    sender_role: UserRole
    body: str
    created_at: datetime


class ChatThreadOut(BaseModel):
    rent_payment_id: str
    listing_id: str
    listing_title: str
    other_party_name: str
    last_message_at: datetime | None
    last_message_preview: str | None


class AdminChatThreadOut(BaseModel):
    """Every chat thread on the platform, for admin oversight."""
    rent_payment_id: str
    listing_id: str
    listing_title: str
    renter_name: str
    landlord_name: str
    message_count: int
    last_message_at: datetime | None
    last_message_preview: str | None
