"""Data-access layer. Raw sqlite3, parameterized queries ONLY.

Design rule for the whole project: every SQL statement lives in this module
or receives its connection from get_db(). Routes never build SQL strings.
This isolation is also the escape hatch: if the academy outgrows SQLite,
we swap this file for a Postgres version and the routes don't change.
"""
import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash


# ---------------------------------------------------------------- connection

def get_db():
    """One connection per request, cached on Flask's `g` object.

    row_factory=sqlite3.Row lets templates do row["name"] instead of row[0].
    PRAGMA foreign_keys is per-connection in SQLite, so it is set here.
    """
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_settings():
    """White-label settings as a dict — injected into every template."""
    rows = get_db().execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


# -------------------------------------------------------------------- schema

def init_db():
    db = get_db()
    # WAL mode: readers don't block writers. Persistent (stored in the file),
    # so setting it once at init is enough. This is what makes SQLite viable
    # for a small production app.
    db.execute("PRAGMA journal_mode = WAL")
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    db.commit()


# ---------------------------------------------------------------------- seed

SEED_SETTINGS = {
    "academy_name": "Sunrise Tennis Academy",
    "tagline": "Junior programs, camps & high-performance training",
    "contact_email": "info@sunrise-tennis.example",
}

# Demo accounts so a recruiter can evaluate the app in under a minute.
# Passwords are documented in the README on purpose — these are demo creds.
DEMO_PARENT = ("parent@demo.test", "Demo1234!", "parent", 1)
DEMO_ADMIN = ("admin@demo.test", "Admin1234!", "admin", 0)


def seed_db():
    """Idempotent: safe to call on every boot — inserts only if empty."""
    db = get_db()
    if db.execute("SELECT 1 FROM programs LIMIT 1").fetchone():
        return False

    for key, value in SEED_SETTINGS.items():
        db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    def program(name, desc, min_age=None, max_age=None,
                utr_min=None, utr_max=None, sort=0):
        cur = db.execute(
            """INSERT INTO programs
               (name, description, min_age, max_age, utr_min, utr_max, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, desc, min_age, max_age, utr_min, utr_max, sort),
        )
        return cur.lastrowid

    def option(pid, label, days, period, member_cents, nonmember_cents,
               capacity=12):
        db.execute(
            """INSERT INTO program_options
               (program_id, label, days_per_week, billing_period,
                price_member_cents, price_nonmember_cents, capacity)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pid, label, days, period, member_cents, nonmember_cents, capacity),
        )

    p = program("10 & Under Tennis",
                "Fundamentals and fun for our youngest players. "
                "Red/orange/green ball progression.", 4, 10, sort=1)
    option(p, "1 day / week", 1, "session", 8900, 10900)
    option(p, "2 days / week", 2, "session", 13900, 17900)
    option(p, "3 days / week", 3, "session", 18900, 23900)

    p = program("Tournament Training (Level 6-7)",
                "For competitive juniors building a match game. UTR below 3.",
                None, None, None, 3.0, sort=2)
    option(p, "1 day / week", 1, "session", 18900, 20900)
    option(p, "2 days / week", 2, "session", 28900, 32900)
    option(p, "3 days / week", 3, "session", 37900, 43900)
    option(p, "4 days / week", 4, "session", 44900, 52900)

    p = program("High Performance (Level 1-5)",
                "Advanced training for ranked players. UTR 3 and above.",
                None, None, 3.0, None, sort=3)
    option(p, "1 day / week", 1, "session", 20900, 22900)
    option(p, "2 days / week", 2, "session", 30900, 35900)
    option(p, "3 days / week", 3, "session", 40900, 46900)
    option(p, "4 days / week", 4, "session", 48900, 54900)

    p = program("Saturday Tennis Camp",
                "Weekend camp for ages 5-15. Join for the full session "
                "or week by week.", 5, 15, sort=4)
    option(p, "Full session", None, "session", 17900, 21900, capacity=24)
    option(p, "Single week", None, "week", 5900, 6900, capacity=24)

    p = program("Challenger Competition Camp",
                "Saturday match-play camp with supervised competition.",
                None, None, None, None, sort=5)
    option(p, "Single week", None, "week", 5900, 6900, capacity=16)

    # ASSUMPTION (stated in PROJECT.md): summer camp priced per week,
    # $249 member / $299 non-member. Admin can edit in Phase 4.
    p = program("Summer Camp",
                "Full-day summer camp: tennis, fitness and games.",
                5, 16, sort=6)
    option(p, "Single week (full day)", None, "week", 24900, 29900,
           capacity=32)

    for email, password, role, is_member in (DEMO_PARENT, DEMO_ADMIN):
        db.execute(
            """INSERT INTO users
               (email, password_hash, role, is_member, email_verified)
               VALUES (?, ?, ?, ?, 1)""",
            (email, generate_password_hash(password), role, is_member),
        )

    parent_id = db.execute(
        "SELECT id FROM users WHERE email = ?", (DEMO_PARENT[0],)
    ).fetchone()["id"]
    db.execute(
        "INSERT INTO children (parent_id, name, birth_year, utr) "
        "VALUES (?, ?, ?, ?)",
        (parent_id, "Alex", 2014, 2.1),
    )

    db.commit()
    return True


# ----------------------------------------------------------------------- CLI

@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Database initialized.")


@click.command("seed-db")
def seed_db_command():
    click.echo("Seeded." if seed_db() else "Already seeded — skipped.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
