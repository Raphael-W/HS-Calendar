import os
from flask import Flask, jsonify, make_response, render_template
from werkzeug.exceptions import HTTPException
from .extensions import db, migrate, limiter

def create_app():
    app = Flask(__name__)

    app.config.from_object("app.config.BaseConfig")

    os.makedirs(app.config["INSTANCE_PATH"], exist_ok=True)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    from . import models

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Statuses the sign-in form has to tell apart to word its own message:
    # 400 missing details, 401 wrong password, 429 rate limited.
    FORM_ERRORS = {400, 401, 429}

    def _error_page(status):
        """The one generic error page: 404, or an unexplained failure."""
        html = render_template("error.html", not_found=(status == 404))
        return make_response(html, status)

    def _error_json(e):
        # Deliberately carries no "description"/"message"/"error" text — the
        # client supplies its own wording from the status code alone.
        response = make_response(jsonify(status="error"), e.code)
        if retry_after := e.get_response().headers.get("Retry-After"):
            response.headers["Retry-After"] = retry_after
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        if e.code in FORM_ERRORS:
            return _error_json(e)

        # Everything else is a page, and never says which error occurred.
        return _error_page(404 if e.code == 404 else 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled exception")
        return _error_page(500)

    return app
