import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.database import SessionLocal
from app.models.listing import Listing, ListingStatus
from app.models.rent_payment import RentPayment, RentPaymentStatus
from app.services.notifications.messages import notify_renter_renewal_reminder

settings = get_settings()
logger = logging.getLogger("wakaless.scheduler")

_scheduler: BackgroundScheduler | None = None


def run_reminder_and_expiry_check() -> None:
    """Idempotent by construction (guarded by *_sent_at / status columns), so
    it's always safe to re-run after a crash/restart or via the manual
    POST /admin/run-reminders escape hatch."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        due_1m = (
            db.query(RentPayment)
            .filter(
                RentPayment.status == RentPaymentStatus.active,
                RentPayment.reminder_1m_sent_at.is_(None),
                RentPayment.end_date <= now + timedelta(days=settings.reminder_lead_days_1),
                RentPayment.end_date > now,
            )
            .all()
        )
        for rp in due_1m:
            if notify_renter_renewal_reminder(rp, "1 month"):
                rp.reminder_1m_sent_at = now

        due_2w = (
            db.query(RentPayment)
            .filter(
                RentPayment.status == RentPaymentStatus.active,
                RentPayment.reminder_2w_sent_at.is_(None),
                RentPayment.end_date <= now + timedelta(days=settings.reminder_lead_days_2),
                RentPayment.end_date > now,
            )
            .all()
        )
        for rp in due_2w:
            if notify_renter_renewal_reminder(rp, "2 weeks"):
                rp.reminder_2w_sent_at = now

        ended = (
            db.query(RentPayment)
            .filter(RentPayment.status == RentPaymentStatus.active, RentPayment.end_date <= now)
            .all()
        )
        for rp in ended:
            rp.status = RentPaymentStatus.ended
            listing = db.query(Listing).filter(Listing.id == rp.listing_id).first()
            if listing and listing.status == ListingStatus.rented:
                listing.status = ListingStatus.live
                listing.expires_at = now + timedelta(days=settings.listing_expiry_days)

        db.commit()
    except Exception:
        logger.exception("run_reminder_and_expiry_check failed")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    # Job bodies compare against datetime.utcnow() (naive UTC) throughout —
    # pin the scheduler to UTC too, or its default local-timezone clock would
    # misread those naive datetimes and misfire immediately.
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_reminder_and_expiry_check,
        "interval",
        hours=settings.reminder_check_interval_hours,
        next_run_time=datetime.utcnow() + timedelta(seconds=10),
    )
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
