from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.models.verification import LandlordVerification, VerificationStatus
from app.schemas.user import (
    BankDetailsOut,
    BankDetailsUpdate,
    BankOut,
    ResolveAccountOut,
    VerificationOut,
    VerificationSubmit,
)
from app.services.notifications.messages import notify_admin_verification_pending
from app.services.paystack_banks import list_nigerian_banks, resolve_account
from app.services.storage import save_upload

router = APIRouter(prefix="/landlords", tags=["landlords"])


@router.get("/me/verification", response_model=VerificationOut)
def my_verification(user: User = Depends(require_role(UserRole.landlord)), db: Session = Depends(get_db)):
    v = db.query(LandlordVerification).filter(LandlordVerification.user_id == user.id).first()
    if not v:
        return VerificationOut(status=VerificationStatus.unverified)
    return VerificationOut.model_validate(v)


@router.post("/me/photo", summary="Upload a photo of the landlord, for identity confirmation")
def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.landlord)),
):
    url = save_upload(file, subfolder="landlord-photos")
    return {"url": url}


@router.post("/me/verify", response_model=VerificationOut)
def submit_verification(
    payload: VerificationSubmit,
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    """
    One-time per account. No automated identity check. An admin manually
    reviews the uploaded photo before the account is marked "verified" (see
    POST /admin/verifications/{id}/review). Proof of ownership is collected
    separately, per listing, since every listing already requires it.
    """
    existing = db.query(LandlordVerification).filter(LandlordVerification.user_id == user.id).first()
    if existing and existing.status in (VerificationStatus.verified, VerificationStatus.pending):
        raise HTTPException(status_code=400, detail="A verification is already submitted or approved for this account")

    if not existing:
        existing = LandlordVerification(user_id=user.id)
        db.add(existing)

    existing.photo_url = payload.photo_url
    existing.submitted_at = datetime.utcnow()
    existing.status = VerificationStatus.pending
    existing.failure_reason = None

    db.commit()
    db.refresh(existing)

    notify_admin_verification_pending(user)

    return VerificationOut.model_validate(existing)


@router.get("/me/bank-details", response_model=BankDetailsOut)
def get_bank_details(user: User = Depends(require_role(UserRole.landlord))):
    return BankDetailsOut.model_validate(user)


@router.put("/me/bank-details", response_model=BankDetailsOut)
def update_bank_details(
    payload: BankDetailsUpdate,
    user: User = Depends(require_role(UserRole.landlord)),
    db: Session = Depends(get_db),
):
    user.bank_name = payload.bank_name
    user.bank_code = payload.bank_code
    user.bank_account_number = payload.bank_account_number
    user.bank_account_name = payload.bank_account_name
    db.commit()
    db.refresh(user)
    return BankDetailsOut.model_validate(user)


@router.get("/banks", response_model=list[BankOut])
def banks(user: User = Depends(require_role(UserRole.landlord))):
    try:
        return list_nigerian_banks()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Couldn't reach the bank list right now. Try again shortly.")


@router.get("/resolve-account", response_model=ResolveAccountOut)
def resolve_account_number(
    account_number: str,
    bank_code: str,
    user: User = Depends(require_role(UserRole.landlord)),
):
    try:
        account_name = resolve_account(account_number, bank_code)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=400, detail="Couldn't verify this account number for the selected bank.")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Couldn't reach the bank verification service right now.")
    return ResolveAccountOut(account_name=account_name)
