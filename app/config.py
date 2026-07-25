# config.py
import os

class BaseConfig:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
    ROOT_PATH = os.path.dirname(APP_PATH)
    INSTANCE_PATH = os.path.join(ROOT_PATH, "instance")
    ENV_PATH = os.path.join(ROOT_PATH, ".env")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_PATH, "hs_calendar.db")

    # Emit X-RateLimit-* and Retry-After so the UI can tell users how long to wait.
    RATELIMIT_HEADERS_ENABLED = True