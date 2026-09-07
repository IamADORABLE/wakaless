"""
One-off script: create (or promote) an admin user for the review queue.

Usage:
    python create_admin.py +2348000000000 "Admin Name" admin@example.com a-strong-password
"""
import sys

from app.core.security import hash_password
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)

    phone, name, email, password = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            user.role = UserRole.admin
            print(f"Promoted existing user {phone} to admin.")
        else:
            user = User(full_name=name, phone=phone, email=email, role=UserRole.admin, hashed_password=hash_password(password))
            db.add(user)
            print(f"Created new admin user {phone}.")
        db.commit()
    finally:
        db.close()
