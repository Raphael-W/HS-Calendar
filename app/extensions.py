from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter

from flask_limiter.util import get_remote_address
from flask import request

import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

from .config import BaseConfig

# Real environment variables win over .env, so deployments and CI can supply the
# key without a file on disk.
load_dotenv(BaseConfig.ENV_PATH)

encryption_key = os.environ["ENCRYPTION_KEY"].encode()
fernet = Fernet(encryption_key)


def _get_client_ip():
    return request.headers.get("CF-Connecting-IP") or get_remote_address()


db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(_get_client_ip, default_limits=[])
