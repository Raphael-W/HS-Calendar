from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter

from flask_limiter.util import get_remote_address
from flask import request

from cryptography.fernet import Fernet
from dotenv import dotenv_values

from .config import BaseConfig

encryption_key = dotenv_values(BaseConfig.ENV_PATH)["ENCRYPTION_KEY"].encode()
fernet = Fernet(encryption_key)


def _get_client_ip():
    return request.headers.get("CF-Connecting-IP") or get_remote_address()


db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(_get_client_ip, default_limits=["100 per hour"])
