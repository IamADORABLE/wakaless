import logging

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_action_token,
    decode_action_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
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

VERIFY_EMAIL_PURPOSE = "verify_email"
RESET_PASSWORD_PURPOSE = "reset_password"


def _send_verification_email_best_effort(user: User) -> None:
    """Best-effort: a failed send must never break signup/resend responses."""
    try:
        token = create_action_token(
            subject=user.id, purpose=VERIFY_EMAIL_PURPOSE,
            expires_minutes=settings.email_verification_expire_minutes,
        )
        send_verification_email(user, token)
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

    _send_verification_email_best_effort(user)

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
    try:
        user_id = decode_action_token(payload.token, purpose=VERIFY_EMAIL_PURPOSE)
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired")

    user.email_verified = True
    db.commit()
    return {"detail": "Email verified"}


@router.post("/resend-verification")
def resend_verification(payload: ResendVerification, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if user and not user.email_verified:
        _send_verification_email_best_effort(user)
    # Same response either way, so this can't be used to probe which emails have signed up.
    return {"detail": "If that email has an unverified account, we've sent a new verification link"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()
    if user:
        try:
            token = create_action_token(
                subject=user.id, purpose=RESET_PASSWORD_PURPOSE,
                expires_minutes=settings.password_reset_expire_minutes,
            )
            send_password_reset_email(user, token)
        except Exception:
            logger.exception("Failed to send password reset email to user %s", user.id)
    # Same response either way, so this can't be used to probe which emails have signed up.
    return {"detail": "If that email has an account, we've sent a password reset link"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_action_token(payload.token, purpose=RESET_PASSWORD_PURPOSE)
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password reset"}
