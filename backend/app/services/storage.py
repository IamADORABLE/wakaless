"""
File storage for listing photos + ownership documents.

STORAGE_PROVIDER=local (default) saves into backend/uploads/ and serves it
back via a static mount — fine for local dev and demos. Set
STORAGE_PROVIDER=cloudinary with a CLOUDINARY_URL to upload to Cloudinary
in staging/production (per the brief's tech stack), no route changes needed.
"""
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

settings = get_settings()
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_upload(file: UploadFile, subfolder: str, resource_type: str = "auto") -> str:
    if settings.storage_provider == "cloudinary":
        return _save_to_cloudinary(file, subfolder, resource_type)
    return _save_locally(file, subfolder)


def _save_locally(file: UploadFile, subfolder: str) -> str:
    folder = UPLOAD_DIR / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    name = f"{uuid.uuid4()}{ext}"
    dest = folder / name
    with open(dest, "wb") as f:
        f.write(file.file.read())
    return f"/uploads/{subfolder}/{name}"


def _save_to_cloudinary(file: UploadFile, subfolder: str, resource_type: str) -> str:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(cloudinary_url=settings.cloudinary_url)
    result = cloudinary.uploader.upload(file.file, folder=f"wakaless/{subfolder}", resource_type=resource_type)
    return result["secure_url"]
