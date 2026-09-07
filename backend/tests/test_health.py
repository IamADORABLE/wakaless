import uuid

from fastapi.testclient import TestClient

from app.core.security import create_action_token
from app.main import app
from app.routers import availability as availability_router
from app.routers import landlords as landlords_router
from app.routers import listings as listings_router
from app.services.notifications import messages as notifications_messages

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_browse_listings_empty_ok():
    resp = client.get("/listings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_signup_and_login():
    signup = client.post("/auth/signup", json={
        "full_name": "Test Renter", "phone": "+2348011112222", "email": "renter@example.com",
        "password": "supersecret1", "role": "renter",
    })
    assert signup.status_code == 200, signup.text
    token = signup.json()["access_token"]
    assert token

    login = client.post("/auth/login", json={"identifier": "+2348011112222", "password": "supersecret1"})
    assert login.status_code == 200

    login_by_email = client.post("/auth/login", json={"identifier": "renter@example.com", "password": "supersecret1"})
    assert login_by_email.status_code == 200


def test_landlord_verification_flow_no_automated_check():
    signup = client.post("/auth/signup", json={
        "full_name": "Test Landlord", "phone": "+2348022223333", "email": "landlord@example.com",
        "password": "supersecret1", "role": "landlord",
    })
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/landlords/me/verify",
        json={"ownership_proof_url": "https://example.com/proof.jpg"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    # No automated identity check — every submission goes to "pending" for
    # an admin to manually review the uploaded proof of ownership.
    assert resp.json()["status"] == "pending"


def test_submitting_verification_emails_the_admin_inbox(monkeypatch):
    monkeypatch.setattr(notifications_messages.settings, "admin_email", "admin-inbox@example.com")

    signup = client.post("/auth/signup", json={
        "full_name": "Notify Admin Landlord", "phone": "+2348088889999", "email": "notifyadmin@example.com",
        "password": "supersecret1", "role": "landlord",
    })
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    sent = {}
    original = notifications_messages.notify_admin_verification_pending

    def spy(landlord):
        sent["called"] = True
        return original(landlord)

    monkeypatch.setattr(landlords_router, "notify_admin_verification_pending", spy)

    resp = client.post(
        "/landlords/me/verify",
        json={"ownership_proof_url": "https://example.com/proof.jpg"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert sent.get("called") is True


def test_creating_a_listing_emails_the_admin_inbox(monkeypatch):
    monkeypatch.setattr(notifications_messages.settings, "admin_email", "admin-inbox@example.com")

    landlord_headers = _signup("+2348011110002", "notifynewlisting@example.com", "landlord", "Notify New Listing Landlord")
    _verify_landlord(landlord_headers, "Notify New Listing Landlord")

    sent = {}
    original = notifications_messages.notify_admin_new_listing

    def spy(listing):
        sent["called"] = True
        return original(listing)

    monkeypatch.setattr(listings_router, "notify_admin_new_listing", spy)

    resp = client.post("/listings", json={
        "title": "Notify Admin Flat", "photos": ["https://example.com/p.jpg"],
        "rent_amount_ngn": 300000, "rent_duration_months": 12, "agreement_fee_ngn": 20000,
        "area": "Surulere", "address": "1 Adeniran Ogunsanya St", "ownership_doc_url": "https://example.com/doc.jpg",
    }, headers=landlord_headers)
    assert resp.status_code == 200, resp.text
    assert sent.get("called") is True


def test_requesting_availability_emails_the_admin_inbox(monkeypatch):
    monkeypatch.setattr(notifications_messages.settings, "admin_email", "admin-inbox@example.com")

    landlord_headers = _signup("+2348011110003", "notifyavaillandlord@example.com", "landlord", "Notify Avail Landlord")
    _verify_landlord(landlord_headers, "Notify Avail Landlord")

    listing_resp = client.post("/listings", json={
        "title": "Notify Availability Flat", "photos": ["https://example.com/p.jpg"],
        "rent_amount_ngn": 300000, "rent_duration_months": 12, "agreement_fee_ngn": 20000,
        "area": "Yaba", "address": "2 Herbert Macaulay Way", "ownership_doc_url": "https://example.com/doc.jpg",
    }, headers=landlord_headers)
    listing_id = listing_resp.json()["id"]

    admin_headers = _signup("+2348011110004", "notifyavailadmin@example.com", "admin", "Notify Avail Admin")
    client.post(f"/admin/listings/{listing_id}/review", json={"approve": True}, headers=admin_headers)

    renter_headers = _signup("+2348011110005", "notifyavailrenter@example.com", "renter", "Notify Avail Renter")

    sent = {}
    original = notifications_messages.notify_admin_availability_request

    def spy(listing, renter):
        sent["called"] = True
        return original(listing, renter)

    monkeypatch.setattr(availability_router, "notify_admin_availability_request", spy)

    resp = client.post("/availability/request", json={"listing_id": listing_id}, headers=renter_headers)
    assert resp.status_code == 200, resp.text
    assert sent.get("called") is True


def test_admin_notification_is_skipped_without_admin_email(monkeypatch):
    monkeypatch.setattr(notifications_messages.settings, "admin_email", "")
    landlord = type("L", (), {"id": "x", "full_name": "No Admin Email", "phone": "+1", "email": "a@b.com"})()
    assert notifications_messages.notify_admin_verification_pending(landlord) is False


def test_bank_details_round_trip_with_bank_code():
    landlord_headers = _signup("+2348011110006", "bankdetails@example.com", "landlord", "Bank Details Landlord")

    update = client.put("/landlords/me/bank-details", json={
        "bank_name": "Guaranty Trust Bank", "bank_code": "058",
        "bank_account_number": "0123456789", "bank_account_name": "Bank Details Landlord",
    }, headers=landlord_headers)
    assert update.status_code == 200, update.text
    assert update.json()["bank_code"] == "058"

    fetched = client.get("/landlords/me/bank-details", headers=landlord_headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["bank_code"] == "058"


def test_list_banks_and_resolve_account(monkeypatch):
    landlord_headers = _signup("+2348011110007", "listbanks@example.com", "landlord", "List Banks Landlord")

    monkeypatch.setattr(
        landlords_router, "list_nigerian_banks",
        lambda: [{"name": "Guaranty Trust Bank", "code": "058"}, {"name": "Access Bank", "code": "044"}],
    )
    banks_resp = client.get("/landlords/banks", headers=landlord_headers)
    assert banks_resp.status_code == 200, banks_resp.text
    assert {"name": "Access Bank", "code": "044"} in banks_resp.json()

    monkeypatch.setattr(
        landlords_router, "resolve_account",
        lambda account_number, bank_code: "Ade Ade Resolved",
    )
    resolve_resp = client.get(
        "/landlords/resolve-account",
        params={"account_number": "0123456789", "bank_code": "058"},
        headers=landlord_headers,
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["account_name"] == "Ade Ade Resolved"


def test_bank_lookup_fails_gracefully_without_paystack_key(monkeypatch):
    landlord_headers = _signup("+2348011110008", "nopaystackkey@example.com", "landlord", "No Key Landlord")

    def boom():
        raise RuntimeError("PAYSTACK_SECRET_KEY is not set, so bank lookup/verification is unavailable.")

    monkeypatch.setattr(landlords_router, "list_nigerian_banks", boom)
    resp = client.get("/landlords/banks", headers=landlord_headers)
    assert resp.status_code == 503


def test_admin_can_approve_pending_verification():
    landlord_signup = client.post("/auth/signup", json={
        "full_name": "Pending Landlord", "phone": "+2348033334444", "email": "pending@example.com",
        "password": "supersecret1", "role": "landlord",
    })
    landlord_headers = {"Authorization": f"Bearer {landlord_signup.json()['access_token']}"}
    client.post(
        "/landlords/me/verify",
        json={"ownership_proof_url": "https://example.com/proof2.jpg"},
        headers=landlord_headers,
    )

    admin_signup = client.post("/auth/signup", json={
        "full_name": "Test Admin", "phone": "+2348044445555", "email": "admin@example.com",
        "password": "supersecret1", "role": "admin",
    })
    admin_headers = {"Authorization": f"Bearer {admin_signup.json()['access_token']}"}

    queue = client.get("/admin/verification-queue", headers=admin_headers)
    assert queue.status_code == 200, queue.text
    entry = next(v for v in queue.json() if v["full_name"] == "Pending Landlord")
    assert entry["ownership_proof_url"] == "https://example.com/proof2.jpg"

    review = client.post(
        f"/admin/verifications/{entry['id']}/review",
        json={"approve": True},
        headers=admin_headers,
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "verified"


def test_admin_can_list_users():
    _signup("+2348099990001", "listusers-renter@example.com", "renter", "List Users Renter")
    admin_headers = _signup("+2348099990002", "listusers-admin@example.com", "admin", "List Users Admin")

    resp = client.get("/admin/users", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    entry = next(u for u in resp.json() if u["full_name"] == "List Users Renter")
    assert entry["email_verified"] is False

    filtered = client.get("/admin/users", params={"role": "renter"}, headers=admin_headers)
    assert filtered.status_code == 200, filtered.text
    assert all(u["role"] == "renter" for u in filtered.json())


def _signup(phone, email, role, name="Test User"):
    resp = client.post("/auth/signup", json={
        "full_name": name, "phone": phone, "email": email, "password": "supersecret1", "role": role,
    })
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _verify_landlord(headers, full_name):
    resp = client.post("/landlords/me/verify", json={"ownership_proof_url": "https://example.com/proof.jpg"}, headers=headers)
    assert resp.status_code == 200, resp.text
    unique = uuid.uuid4().hex[:8]
    admin_headers = _signup(f"+234809{unique[:7]}", f"admin-verifier-{unique}@example.com", "admin", "Verifier Admin")
    queue = client.get("/admin/verification-queue", headers=admin_headers).json()
    entry = next(v for v in queue if v["full_name"] == full_name)
    client.post(f"/admin/verifications/{entry['id']}/review", json={"approve": True}, headers=admin_headers)


def test_full_rent_payment_flow():
    landlord_headers = _signup("+2348055551111", "landlord2@example.com", "landlord", "Rent Landlord")
    _verify_landlord(landlord_headers, "Rent Landlord")

    listing_resp = client.post("/listings", json={
        "title": "Cosy 2 bed flat", "photos": ["https://example.com/p.jpg"],
        "rent_amount_ngn": 400000, "rent_duration_months": 12, "agreement_fee_ngn": 50000,
        "area": "Yaba", "address": "12 Herbert Macaulay Way", "ownership_doc_url": "https://example.com/doc.jpg",
    }, headers=landlord_headers)
    assert listing_resp.status_code == 200, listing_resp.text
    listing_id = listing_resp.json()["id"]

    admin_headers = _signup("+2348090000002", "admin-listing@example.com", "admin", "Listing Admin")
    review = client.post(f"/admin/listings/{listing_id}/review", json={"approve": True}, headers=admin_headers)
    assert review.status_code == 200, review.text

    renter_headers = _signup("+2348066662222", "renter2@example.com", "renter", "Rent Renter")

    # Can't pay before availability is confirmed.
    blocked = client.post("/rent-payments/initiate", json={"listing_id": listing_id}, headers=renter_headers)
    assert blocked.status_code == 400

    avail = client.post("/availability/request", json={"listing_id": listing_id}, headers=renter_headers)
    assert avail.status_code == 200, avail.text
    assert avail.json()["status"] == "pending"

    mine = client.get("/availability/mine", headers=renter_headers).json()
    mine_entry = next(r for r in mine if r["listing_id"] == listing_id)
    assert mine_entry["status"] == "pending"
    assert mine_entry["listing_status"] == "live"
    assert mine_entry["consumed_at"] is None

    queue = client.get("/admin/availability-queue", headers=admin_headers).json()
    request_id = next(r["id"] for r in queue if r["listing_id"] == listing_id)
    confirm = client.post(f"/admin/availability-requests/{request_id}/review", json={"approve": True}, headers=admin_headers)
    assert confirm.status_code == 200, confirm.text

    mine = client.get("/availability/mine", headers=renter_headers).json()
    mine_entry = next(r for r in mine if r["listing_id"] == listing_id)
    assert mine_entry["status"] == "confirmed"
    assert mine_entry["listing_status"] == "live"

    initiate = client.post("/rent-payments/initiate", json={"listing_id": listing_id}, headers=renter_headers)
    assert initiate.status_code == 200, initiate.text
    # First payment: rent + agreement fee + commission (rent < 500,000 -> 20,000 fee), all charged to the renter.
    init_data = initiate.json()
    assert init_data["rent_amount_ngn"] == 400000
    assert init_data["agreement_fee_ngn"] == 50000
    assert init_data["commission_ngn"] == 20000
    assert init_data["total_amount_ngn"] == 470000
    reference = initiate.json()["reference"]

    verify = client.post("/rent-payments/verify", json={"reference": reference}, headers=renter_headers)
    assert verify.status_code == 200, verify.text
    rp = verify.json()
    assert rp["landlord_phone"] == "+2348055551111"
    rent_payment_id = rp["id"]

    # Paying consumes the availability confirmation and takes the listing off
    # the renter's "still deciding" list (it now shows up under My rentals instead).
    mine = client.get("/availability/mine", headers=renter_headers).json()
    mine_entry = next(r for r in mine if r["listing_id"] == listing_id)
    assert mine_entry["consumed_at"] is not None

    # Idempotency: a repeated verify call with the same reference (e.g. the
    # redirect callback firing twice) must return the same row, not create
    # a second tenancy.
    verify_again = client.post("/rent-payments/verify", json={"reference": reference}, headers=renter_headers)
    assert verify_again.status_code == 200, verify_again.text
    assert verify_again.json()["id"] == rent_payment_id
    assert len(client.get("/rent-payments/mine", headers=renter_headers).json()) == 1

    # Chat between renter and landlord.
    send = client.post(f"/chat/{rent_payment_id}/messages", json={"body": "Hi, when can I move in?"}, headers=renter_headers)
    assert send.status_code == 200, send.text
    messages = client.get(f"/chat/{rent_payment_id}/messages", headers=landlord_headers).json()
    assert any(m["body"] == "Hi, when can I move in?" for m in messages)

    # Receipt: itemized rent + agreement fee + commission, totalling what was charged.
    receipt = client.get(f"/rent-payments/{rent_payment_id}/receipt", headers=renter_headers)
    assert receipt.status_code == 200, receipt.text
    receipt_data = receipt.json()
    assert receipt_data["rent_amount_ngn"] == 400000
    assert receipt_data["agreement_fee_ngn"] == 50000
    assert receipt_data["commission_ngn"] == 20000
    assert receipt_data["total_paid_ngn"] == 470000

    # Payout: landlord gets rent + agreement fee in full; platform keeps its fee.
    payouts = client.get("/admin/payouts-queue", headers=admin_headers).json()
    entry = next(p for p in payouts if p["rent_payment_id"] == rent_payment_id)
    assert entry["agreement_fee_ngn"] == 50000
    assert entry["commission_ngn"] == 20000
    assert entry["landlord_payout_ngn"] == 450000
    assert entry["is_renewal"] is False
    assert entry["inspection_confirmed_at"] is None

    # The payout is held until the renter confirms they inspected the house.
    blocked_payout = client.post(f"/admin/payouts/{rent_payment_id}/mark-paid", json={"payout_reference": "manual-1"}, headers=admin_headers)
    assert blocked_payout.status_code == 400, blocked_payout.text

    inspections = client.get("/admin/inspections", headers=admin_headers).json()
    inspection_entry = next(i for i in inspections if i["id"] == rent_payment_id)
    assert inspection_entry["inspection_confirmed_at"] is None

    confirm = client.post(f"/rent-payments/{rent_payment_id}/confirm-inspection", headers=renter_headers)
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["inspection_confirmed_at"] is not None

    # Can't confirm twice.
    confirm_again = client.post(f"/rent-payments/{rent_payment_id}/confirm-inspection", headers=renter_headers)
    assert confirm_again.status_code == 400

    inspections = client.get("/admin/inspections", headers=admin_headers).json()
    inspection_entry = next(i for i in inspections if i["id"] == rent_payment_id)
    assert inspection_entry["inspection_confirmed_at"] is not None

    mark_paid = client.post(f"/admin/payouts/{rent_payment_id}/mark-paid", json={"payout_reference": "manual-1"}, headers=admin_headers)
    assert mark_paid.status_code == 200, mark_paid.text

    # Renewal charges rent only (no agreement fee, no commission this time),
    # including the same double-call idempotency guarantee.
    renew_initiate = client.post(f"/rent-payments/{rent_payment_id}/renew/initiate", headers=renter_headers)
    assert renew_initiate.status_code == 200, renew_initiate.text
    renew_init_data = renew_initiate.json()
    assert renew_init_data["rent_amount_ngn"] == 400000
    assert renew_init_data["agreement_fee_ngn"] == 0
    assert renew_init_data["commission_ngn"] == 0
    assert renew_init_data["total_amount_ngn"] == 400000
    renew_reference = renew_initiate.json()["reference"]

    renew_verify = client.post(f"/rent-payments/{rent_payment_id}/renew/verify", json={"reference": renew_reference}, headers=renter_headers)
    assert renew_verify.status_code == 200, renew_verify.text
    new_rent_payment_id = renew_verify.json()["id"]
    assert new_rent_payment_id != rent_payment_id

    renew_verify_again = client.post(f"/rent-payments/{rent_payment_id}/renew/verify", json={"reference": renew_reference}, headers=renter_headers)
    assert renew_verify_again.status_code == 200, renew_verify_again.text
    assert renew_verify_again.json()["id"] == new_rent_payment_id
    assert len(client.get("/rent-payments/mine", headers=renter_headers).json()) == 2

    # Renewal payout: landlord gets the full rent, platform takes nothing.
    renew_receipt = client.get(f"/rent-payments/{new_rent_payment_id}/receipt", headers=renter_headers).json()
    assert renew_receipt["agreement_fee_ngn"] == 0
    assert renew_receipt["commission_ngn"] == 0
    assert renew_receipt["total_paid_ngn"] == 400000
    renew_payouts = client.get("/admin/payouts-queue", headers=admin_headers).json()
    renew_entry = next(p for p in renew_payouts if p["rent_payment_id"] == new_rent_payment_id)
    assert renew_entry["landlord_payout_ngn"] == 400000
    assert renew_entry["is_renewal"] is True

    # Renewals skip the inspection gate entirely: the renter already lives there.
    renew_mark_paid = client.post(f"/admin/payouts/{new_rent_payment_id}/mark-paid", json={"payout_reference": "manual-2"}, headers=admin_headers)
    assert renew_mark_paid.status_code == 200, renew_mark_paid.text

    renew_inspections = client.get("/admin/inspections", headers=admin_headers).json()
    assert all(i["id"] != new_rent_payment_id for i in renew_inspections)


def test_signup_starts_unverified_and_verify_email_confirms_it():
    signup = client.post("/auth/signup", json={
        "full_name": "Verify Me", "phone": "+2348077778888", "email": "verifyme@example.com",
        "password": "supersecret1", "role": "renter",
    })
    assert signup.status_code == 200, signup.text
    user = signup.json()["user"]
    assert user["email_verified"] is False

    token = create_action_token(subject=user["id"], purpose="verify_email", expires_minutes=60)
    verify = client.post("/auth/verify-email", json={"token": token})
    assert verify.status_code == 200, verify.text

    login = client.post("/auth/login", json={"identifier": "verifyme@example.com", "password": "supersecret1"})
    assert login.json()["user"]["email_verified"] is True

    # A token minted for a different purpose (e.g. password reset) must not verify an email.
    wrong_purpose_token = create_action_token(subject=user["id"], purpose="reset_password", expires_minutes=60)
    rejected = client.post("/auth/verify-email", json={"token": wrong_purpose_token})
    assert rejected.status_code == 400


def test_resend_verification_is_silent_about_account_existence():
    signup = client.post("/auth/signup", json={
        "full_name": "Resend Me", "phone": "+2348055556666", "email": "resendme@example.com",
        "password": "supersecret1", "role": "renter",
    })
    assert signup.status_code == 200

    known = client.post("/auth/resend-verification", json={"email": "resendme@example.com"})
    unknown = client.post("/auth/resend-verification", json={"email": "doesnotexist@example.com"})
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json() == unknown.json()


def test_forgot_password_and_reset_password_flow():
    signup = client.post("/auth/signup", json={
        "full_name": "Forgetful Renter", "phone": "+2348066667777", "email": "forgetful@example.com",
        "password": "originalpass1", "role": "renter",
    })
    user_id = signup.json()["user"]["id"]

    forgot = client.post("/auth/forgot-password", json={"email": "forgetful@example.com"})
    assert forgot.status_code == 200

    # Same response for an unknown email, so this can't be used to enumerate accounts.
    forgot_unknown = client.post("/auth/forgot-password", json={"email": "notreal@example.com"})
    assert forgot_unknown.json() == forgot.json()

    reset_token = create_action_token(subject=user_id, purpose="reset_password", expires_minutes=30)
    reset = client.post("/auth/reset-password", json={"token": reset_token, "new_password": "brandnewpass1"})
    assert reset.status_code == 200, reset.text

    old_password_login = client.post("/auth/login", json={"identifier": "forgetful@example.com", "password": "originalpass1"})
    assert old_password_login.status_code == 401

    new_password_login = client.post("/auth/login", json={"identifier": "forgetful@example.com", "password": "brandnewpass1"})
    assert new_password_login.status_code == 200

    # A token minted for a different purpose (e.g. email verification) must not reset a password.
    wrong_purpose_token = create_action_token(subject=user_id, purpose="verify_email", expires_minutes=30)
    rejected = client.post("/auth/reset-password", json={"token": wrong_purpose_token, "new_password": "anotherpass1"})
    assert rejected.status_code == 400
