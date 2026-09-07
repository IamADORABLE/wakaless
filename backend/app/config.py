"""
Central app configuration.

Everything here is overridable via environment variables (see .env.example),
so the brief's "open decision" on unlock fee amount is config, not code.
Change the .env and restart; no rebuild needed.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./wakaless.db"

    # Auth
    secret_key: str = "dev-only-insecure-secret-change-me"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    # Business rules (defaults per the brief's "pick sensible defaults" instruction)
    additional_listing_fee_ngn: int = 5000
    listing_expiry_days: int = 30

    # Rent duration options a landlord can choose when creating a listing (months).
    rent_duration_options_months: str = "6,12,24"

    def rent_duration_options(self) -> list[int]:
        return [int(x) for x in self.rent_duration_options_months.split(",") if x.strip()]

    # Commission kept from each rent payment before the rest goes to the
    # landlord (manual bank transfer, admin-confirmed, see PayoutStatus).
    commission_low_ngn: int = 20000
    commission_high_ngn: int = 50000
    commission_threshold_ngn: int = 500000  # rent >= this uses the high commission

    # Renewal reminders, emailed to the renter this many days before their
    # tenancy's end_date, asking if they're renewing.
    reminder_lead_days_1: int = 30
    reminder_lead_days_2: int = 14
    reminder_check_interval_hours: int = 24

    # Payments: mock | paystack
    payment_provider: str = "mock"
    paystack_secret_key: str = ""
    paystack_public_key: str = ""

    # Email: mock | resend | zeptomail
    email_provider: str = "mock"
    resend_api_key: str = ""
    notifications_from_email: str = "noreply@wakaless.local"
    notifications_from_name: str = "Wakaless"
    zeptomail_smtp_host: str = "smtp.zeptomail.com"
    zeptomail_smtp_port: int = 587
    zeptomail_smtp_user: str = ""
    zeptomail_smtp_password: str = ""

    # Email verification / password reset token lifetimes.
    email_verification_expire_minutes: int = 60 * 24  # 24h
    password_reset_expire_minutes: int = 30

    # SMS: mock | termii
    sms_provider: str = "mock"
    termii_api_key: str = ""
    termii_sender_id: str = "Wakaless"

    # Storage: local | cloudinary
    storage_provider: str = "local"
    cloudinary_url: str = ""

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Admin inbox: notified when a landlord submits a verification for review.
    admin_email: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
