import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_access_token,
    generate_verification_code,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationPurpose
from app.schemas.user import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    ResendVerification,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services.notifications.messages import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = logging.getLogger("wakaless.auth")


def _issue_code(db: Session, user: User, purpose: VerificationPurpose, expire_minutes: int) -> str:
    """Creates a fresh code for (user, purpose), invalidating any earlier
    unconsumed one so only the most recently sent code ever works."""
    db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == purpose,
        VerificationCode.consumed_at.is_(None),
    ).delete()

    code = generate_verification_code()
    record = VerificationCode(
        user_id=user.id, purpose=purpose, code_hash=hash_password(code),
        expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes),
    )
    db.add(record)
    db.commit()
    return code


def _check_code(db: Session, user: User, purpose: VerificationPurpose, submitted_code: str) -> bool:
    """Validates a submitted code against the latest unconsumed record for
    (user, purpose): not expired, under the attempt limit, and matching.
    Consumes it (so it can't be replayed) on success."""
    record = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == purpose,
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
        .first()
    )
    if not record:
        return False
    if record.expires_at < datetime.utcnow():
        return False
    if record.attempts >= settings.verification_code_max_attempts:
        return False

    record.attempts += 1
    if not verify_password(submitted_code, record.code_hash):
        db.commit()
        return False

    record.consumed_at = datetime.utcnow()
    db.commit()
    return True


def _send_verification_email_best_effort(db: Session, user: User) -> None:
    """Best-effort: a failed send must never break signup/resend responses."""
    try:
        code = _issue_code(db, user, VerificationPurpose.verify_email, settings.email_verification_code_expire_minutes)
        send_verification_email(user, code)
    except Exception:
        logger.exception("Failed to send verification email to user %s", user.id)


@router.post("/signup", response_model=Token)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="An account with this phone number already exists")

    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _send_verification_email_best_effort(db, user)

    token = create_access_token(subject=user.id, extra={"role": user.role.value})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    user = db.query(User).filter((User.phone == identifier) | (User.email == identifier)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect phone number/email or password")

    token = create_access_token(subject=user.id, extra={"role": user.role.value})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/verify-email")
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if not user or not _check_code(db, user, VerificationPurpose.verify_email, payload.code):
        raise HTTPException(status_code=400, detail="That code is incorrect or has expired")

    user.email_verified = True
    db.commit()
    return {"detail": "Email verified"}


@router.post("/resend-verification")
def resend_verification(payload: ResendVerification, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if user and not user.email_verified:
        _send_verification_email_best_effort(db, user)
    # Same response either way, so this can't be used to probe which emails have signed up.
    return {"detail": "If that email has an unverified account, we've sent a new verification code"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if user:
        try:
            code = _issue_code(db, user, VerificationPurpose.reset_password, settings.password_reset_code_expire_minutes)
            send_password_reset_email(user, code)
        except Exception:
            logger.exception("Failed to send password reset email to user %s", user.id)
    # Same response either way, so this can't be used to probe which emails have signed up.
    return {"detail": "If that email has an account, we've sent a password reset code"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if not user or not _check_code(db, user, VerificationPurpose.reset_password, payload.code):
        raise HTTPException(status_code=400, detail="That code is incorrect or has expired")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password reset"}
