from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatMessage
from app.models.rent_payment import RentPayment
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageOut, ChatThreadOut

router = APIRouter(prefix="/chat", tags=["chat"])


def _load_rent_payment_for_member(rent_payment_id: str, user: User, db: Session) -> RentPayment:
    rp = db.query(RentPayment).filter(RentPayment.id == rent_payment_id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    if user.id != rp.renter_id and user.id != rp.listing.landlord_id:
        raise HTTPException(status_code=403, detail="Not a party to this chat")
    return rp


@router.get("/threads", response_model=list[ChatThreadOut])
def list_threads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(RentPayment)
        .filter(RentPayment.renter_id == user.id)
        .all()
    )
    landlord_rows = [rp for rp in db.query(RentPayment).all() if rp.listing.landlord_id == user.id]
    all_rows = {rp.id: rp for rp in [*rows, *landlord_rows]}.values()

    threads = []
    for rp in all_rows:
        is_renter = rp.renter_id == user.id
        other_party_name = rp.listing.landlord.full_name if is_renter else rp.renter.full_name
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.rent_payment_id == rp.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        threads.append(ChatThreadOut(
            rent_payment_id=rp.id, listing_id=rp.listing_id, listing_title=rp.listing.title,
            other_party_name=other_party_name,
            last_message_at=last_message.created_at if last_message else None,
            last_message_preview=last_message.body[:140] if last_message else None,
        ))
    threads.sort(key=lambda t: t.last_message_at or datetime.min, reverse=True)
    return threads


@router.get("/{rent_payment_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    rent_payment_id: str,
    since: datetime | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rp = _load_rent_payment_for_member(rent_payment_id, user, db)
    q = db.query(ChatMessage).filter(ChatMessage.rent_payment_id == rp.id)
    if since:
        q = q.filter(ChatMessage.created_at > since)
    messages = q.order_by(ChatMessage.created_at.asc()).all()
    return [
        ChatMessageOut(id=m.id, sender_id=m.sender_id, sender_role=m.sender.role, body=m.body, created_at=m.created_at)
        for m in messages
    ]


@router.post("/{rent_payment_id}/messages", response_model=ChatMessageOut)
def send_message(
    rent_payment_id: str,
    payload: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rp = _load_rent_payment_for_member(rent_payment_id, user, db)
    if not payload.body.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    message = ChatMessage(rent_payment_id=rp.id, sender_id=user.id, body=payload.body.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return ChatMessageOut(id=message.id, sender_id=message.sender_id, sender_role=user.role, body=message.body, created_at=message.created_at)
