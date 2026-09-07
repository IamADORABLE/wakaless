import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_wakaless.db")

import pytest

from app.database import Base, engine
from app import models  # noqa: F401


@pytest.fixture(autouse=True, scope="session")
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield
