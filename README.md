# Wakaless

**No agent. No wahala.**

Landlords list their own rental properties directly; renters skip the agent middleman and the
inflated commission fees that come with it. This is the MVP scaffold built from the project brief —
a working React frontend and FastAPI backend covering the v1 flows: browse listings, unlock a
listing's contact info, landlord proof-of-ownership verification, listing creation with admin review, and the
listing lifecycle (rented / expired).

## What's here

```
wakaless/
├── backend/     FastAPI + SQLAlchemy + Alembic + Postgres (SQLite fallback for local dev)
└── frontend/    React (Vite) + React Router
```

Everything runs locally out of the box with a **mock** payment provider — no Paystack account needed
to try the app end to end. Flip a `.env` value to switch to the real provider once you have credentials.
Landlord verification has no external provider at all — it's a manual admin review of an uploaded
proof-of-ownership document (see "Landlord verification" below).

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # defaults are fine for local dev
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.
On first run it auto-creates a local SQLite database (`wakaless.db`) so there's nothing else to set up.

To try the admin review queue, create an admin user:

```bash
python create_admin.py +2348000000000 "Admin Name" a-strong-password
```
Then log in as that phone number/password from the frontend (or via `/docs`) — an admin currently has
no dedicated signup form since it's an internal role.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env             # points at http://localhost:8000 by default
npm run dev
```

Open `http://localhost:5173`. Sign up as a landlord, submit proof of ownership, approve it from the
admin verification queue, create a listing, approve that from the admin review queue, and unlock it
as a renter.

### Running tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## The open decision from the brief

Config, not code — change `.env` and restart, no rebuild needed:

- **Unlock fee** — defaults to ₦1,500 (`UNLOCK_FEE_NGN` in `.env`), valid for 72 hours
  (`UNLOCK_VALID_HOURS`). Change either without touching code.

Payments work the same way: `PAYMENT_PROVIDER=mock` (default, every payment "succeeds" instantly so you
can test the unlock flow) or `PAYMENT_PROVIDER=paystack` with `PAYSTACK_SECRET_KEY` set.

## Landlord verification

There's no automated identity-verification provider. A landlord uploads a photo of a document proving
they own or manage the property (utility bill, C of O, tenancy agreement, etc.); an admin reviews it
from the verification queue and approves or rejects it. The "Verified landlord" badge is only ever set
from a real `verified` status; it has no default-true path.

## What's implemented vs. stubbed

**Implemented:** signup/login (renter, landlord, admin roles), landlord one-time proof-of-ownership
verification with admin manual review, listing creation with photo + ownership-doc upload, admin manual
review queue (approve/reject), public browse + listing detail (no address/contact until unlocked),
renter unlock flow with swappable payment provider, listing lifecycle (mark rented / confirm still
available after expiry).

**Stubbed/deferred, per the brief's v1 scope:** in-app rent/agreement-fee payment processing, native
mobile apps, featured/boosted listings, automated duplicate-listing detection beyond the lat/lng fields
already on `Listing` (geo-proximity flagging can be built on top of those), in-app chat, SMS/phone-OTP
verification (the `User.phone_verified` field exists but nothing sets it yet — wire in Termii/Africa's
Talking here), file storage defaults to local disk (`backend/uploads/`) with a Cloudinary path ready to
flip on via `STORAGE_PROVIDER=cloudinary`.

## Deploying

Matches the brief's suggested hosting:

- **Frontend** → Vercel or Netlify. Build command `npm run build`, output directory `dist`, set
  `VITE_API_BASE_URL` to your deployed backend URL.
- **Backend + DB** → Railway or Render. Provision a Postgres instance, set `DATABASE_URL` to it, run
  `alembic upgrade head` once, then start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Set `FRONTEND_ORIGIN` on the backend to your deployed frontend's URL (CORS).

## Logo assets

The provided icon files live in `frontend/public/` (favicon) and `frontend/src/assets/` (in-app use).
Drop in the horizontal lockup and monochrome icon the same way once you have them — they weren't in the
shared folder yet at the time this was built.
