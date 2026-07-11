"""Application factory.

create_app() builds and returns the Flask app. The factory pattern (vs a
module-level `app = Flask(...)`) matters for three reasons:
1. Tests can create a fresh app with test config.
2. Gunicorn imports it cleanly: `gunicorn "app:create_app()"`.
3. No import-time side effects — nothing touches the DB until a request.
"""
import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from . import db as database
from .config import Config

# CSRF protection for every POST form in the app (Phase 2+ forms get it
# automatically). Any POST without a valid token is rejected with 400.
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure the directory for the SQLite file exists (instance/ locally,
    # /data on a mounted volume in prod).
    db_dir = os.path.dirname(app.config["DATABASE_PATH"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    csrf.init_app(app)
    database.init_app(app)

    from .routes.public import bp as public_bp
    app.register_blueprint(public_bp)

    # ---- template helpers -------------------------------------------------
    @app.template_filter("usd")
    def usd(cents):
        """Prices are stored as integer cents; formatting is a view concern."""
        return f"${cents / 100:,.2f}"

    @app.context_processor
    def inject_site_settings():
        """Every template sees `site` (academy name, tagline) — white-label."""
        try:
            return {"site": database.get_settings()}
        except Exception:
            # DB not initialized yet (first boot) — render with defaults.
            return {"site": {}}

    # ---- error pages & health check ---------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.get("/healthz")
    def healthz():
        """Uptime monitors and the hosting platform hit this."""
        return {"status": "ok"}

    return app
