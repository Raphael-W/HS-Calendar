import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, make_response, render_template
from werkzeug.exceptions import HTTPException
from .extensions import db, migrate, limiter
from pathlib import Path

def configure_logging(app):
    if app.config.get("TESTING", False):
        return

    log_dir = Path(app.config["LOGS_PATH"])
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / "app.log"

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s): %(message)s")

    file_handler.setFormatter(formatter)

    level = logging.INFO

    file_handler.setLevel(logging.INFO)

    app.logger.setLevel(level)
    app.logger.addHandler(file_handler)


def create_app():
    app = Flask(__name__)

    app.config.from_object("app.config.BaseConfig")

    os.makedirs(app.config["INSTANCE_PATH"], exist_ok=True)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    configure_logging(app)

    from . import models

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    FORM_ERRORS = {400: "Invalid input", 401: "Invalid credentials", 429: "Too many requests"}

    def _error_page(status):
        html = render_template("error.html", not_found=(status == 404))
        return make_response(html, status)

    def _error_json(e):
        response = make_response(jsonify(status="error", message=FORM_ERRORS.get(e.code, "")), e.code)
        if retry_after := e.get_response().headers.get("Retry-After"):
            response.headers["Retry-After"] = retry_after
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        if e.code in FORM_ERRORS:
            return _error_json(e)

        return _error_page(404 if e.code == 404 else 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled exception")
        return _error_page(500)

    return app
