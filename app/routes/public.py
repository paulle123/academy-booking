"""Public routes — no login required. Phase 1 scope."""
from flask import Blueprint, render_template, session

from ..db import get_db

bp = Blueprint("public", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/programs")
def programs():
    db = get_db()
    programs = db.execute(
        "SELECT * FROM programs WHERE active = 1 ORDER BY sort_order"
    ).fetchall()
    # One extra query instead of N queries in a loop (or a JOIN we'd have to
    # untangle in the template): fetch all options, group in Python.
    options = db.execute(
        """SELECT * FROM program_options
           WHERE active = 1
           ORDER BY program_id, days_per_week, id"""
    ).fetchall()
    options_by_program = {}
    for o in options:
        options_by_program.setdefault(o["program_id"], []).append(o)

    children = None
    if session.get("user_id"):
        children = db.execute(
            "SELECT id, name FROM children WHERE parent_id = ?", (session["user_id"],)
        ).fetchall()
    return render_template(
        "programs.html", programs=programs, options=options_by_program, children=children
    )
