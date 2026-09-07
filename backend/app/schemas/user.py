from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole
from app.models.verification import VerificationStatus


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8)
    role: UserRole = UserRole.renter

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not v.startswith("+") and not v.startswith("0"):
            raise ValueError("Phone must start with + (intl) or 0 (local)")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Email is required")
        return v


class UserLogin(BaseModel):
    identifier: str = Field(description="Phone number or email")
    password: str


class UserOut(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str
    role: UserRole
    phone_verified: bool
    email_verified: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class EmailVerifyRequest(BaseModel):
    token: str


class ResendVerification(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class VerificationSubmit(BaseModel):
    ownership_proof_url: str = Field(description="URL of the uploaded proof-of-ownership document/photo")


class VerificationOut(BaseModel):
    status: VerificationStatus
    failure_reason: str | None = None
    verified_at: datetime | None = None

    model_config = {"from_attributes": True}


class VerificationQueueItem(BaseModel):
    id: str
    user_id: str
    full_name: str
    phone: str
    email: str
    ownership_proof_url: str | None
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


class VerificationReview(BaseModel):
    approve: bool
    rejection_reason: str | None = None


class AdminUserOut(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str
    role: UserRole
    phone_verified: bool
    email_verified: bool
    created_at: datetime
    verification_status: VerificationStatus | None = None
    listings_count: int = 0

    model_config = {"from_attributes": True}


class BankDetailsUpdate(BaseModel):
    bank_name: str = Field(min_length=2, max_length=140)
    bank_account_number: str = Field(min_length=6, max_length=20)
    bank_account_name: str = Field(min_length=2, max_length=140)


class BankDetailsOut(BaseModel):
    bank_name: str | None
    bank_account_number: str | None
    bank_account_name: str | None

    model_config = {"from_attributes": True}


class PayoutQueueItem(BaseModel):
    rent_payment_id: str
    listing_title: str
    landlord_name: str
    bank_name: str | None
    bank_account_number: str | None
    bank_account_name: str | None
    rent_amount_ngn: int
    agreement_fee_ngn: int
    commission_ngn: int
    landlord_payout_ngn: int
    paid_at: datetime


class PayoutMarkPaid(BaseModel):
    payout_reference: str | None = None
