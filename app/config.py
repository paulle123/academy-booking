"""All configuration comes from environment variables.

Why: the same Docker image must run in dev and prod without code changes.
Secrets (SECRET_KEY, Stripe keys) never live in the repo — only in the
host's environment (Render/Fly dashboard) or a local .env file (gitignored).
"""
import os


class Config:
    # Signs the session cookie. If this leaks, attackers can forge logins.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # SQLite file location. In Docker/prod this points at a persistent volume
    # (e.g. /data/academy.db on Fly.io) so data survives redeploys.
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "instance/academy.db")

    DEBUG = os.environ.get("FLASK_DEBUG") == "1"

    # Cookie hardening. HttpOnly: JS can't read the cookie (XSS mitigation).
    # Secure: cookie only sent over HTTPS — disabled automatically in local
    # dev (http://localhost) via FLASK_DEBUG=1.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"   # not sent on cross-site POSTs (CSRF layer 2)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_DEBUG") != "1"

    # Phase 5 (Stripe) and Phase 2 (email) — already wired so switching
    # test -> live is literally an env-var change, as designed.
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    EMAIL_PROVIDER_API_KEY = os.environ.get("EMAIL_PROVIDER_API_KEY", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@example.com")
