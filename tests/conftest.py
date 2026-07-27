import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Loaded before the app is imported: app.extensions builds the Fernet from
# ENCRYPTION_KEY at import time, so anything .env.test overrides has to be in
# place first. .env.test wins over .env; real env vars win over both, so CI can
# inject them as secrets.
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(".env.test", override=True)

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATELIMIT_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        # A request that aborted mid-transaction leaves the session open, and the
        # test's app context means teardown never ran to clean it up.
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="session")
def credentials():
    """A real staff account, for tests marked `live`. Skips if unconfigured."""
    username = os.getenv("HS_USERNAME")
    password = os.getenv("HS_PASSWORD")

    if not (username and password):
        pytest.skip("set HS_USERNAME and HS_PASSWORD to run live tests")

    return username, password