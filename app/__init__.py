import os
from flask import Flask
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

    return app
