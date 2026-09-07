from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.routers import admin, auth, availability, chat, landlords, listings, rent_payments
from app import models  # noqa: F401  (registers all models on Base.metadata)
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience only: with the default SQLite database this creates
    # tables on first run so there's nothing to configure locally. Postgres
    # deployments are expected to run `alembic upgrade head` instead — this
    # is a no-op there so it never fights with real migrations.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Wakaless API",
    description="No agent. No wahala. Landlords list direct, renters skip the agent middleman.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.include_router(auth.router)
app.include_router(landlords.router)
app.include_router(listings.router)
app.include_router(rent_payments.router)
app.include_router(availability.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "wakaless-api"}
