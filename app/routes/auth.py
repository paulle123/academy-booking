from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from functools import wraps

bp = Blueprint("auth", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

@bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or "@" not in email:
            return "Please enter a valid email."
        if len(password) < 8:
            return "Password must be at least 8 characters."

        db = get_db()

        # check if email already exists
        existing = db.execute(
        """SELECT id FROM users WHERE email = ?""", (email,)
        ).fetchone()
        if existing:
            return "Could not create an account with that email."
        
        pw_hash = generate_password_hash(password)

        db.execute(
        """INSERT INTO users
               (email, password_hash, role, is_member, email_verified)
               VALUES (?, ?, ?, ?, ?)""",
               (email, pw_hash, 'parent', 0, 0)
        )
        db.commit()
        return 'Registered!'
    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or "@" not in email:
            return "Please enter a valid email."
        if len(password) < 8:
            return "Password must be at least 8 characters."

        db = get_db()

        user = db.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None:
            return "Invalid email or password."

        if not check_password_hash(user["password_hash"], password):
            return "Invalid email or password."
        
        session["user_id"] = user["id"]
        return "Logged in!"
        
    return render_template("login.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    return "Welcome to your dashboard!"

@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("public.index"))

@bp.route("/children", methods=["GET"])
@login_required
def children():
    parent_id = session.get("user_id")

    db = get_db()

    children = db.execute(
        "SELECT id, name, birth_year, utr  FROM children WHERE parent_id = ?", (parent_id,)
    ).fetchall()
    return render_template("children.html", children=children)

@bp.route("/add_child", methods=["POST", "GET"])
@login_required
def children_add():
    if request.method == "POST":
        name = request.form['name']
        birth_year = request.form['birth_year']
        utr_raw = request.form.get("utr", "").strip()
        utr = None

        if not name:
            return "Invalid name."
        try:
            birth_year = int(request.form["birth_year"])
        except ValueError:
            return "Birth year must be a number."
        if birth_year < 2007 or birth_year > 2023:
            return "Invalid birth year."
        if utr_raw:
            try:
                utr = float(utr_raw)
            except ValueError:
                return "UTR must be a number."

        db = get_db()
        db.execute(
            "INSERT INTO children (parent_id, name, birth_year, utr) VALUES (?, ?, ?, ?)",
            (session["user_id"], name, birth_year, utr)
        )
        db.commit()
        return redirect(url_for("auth.children"))
    return render_template("add_child.html")

@bp.route("/children/<int:id>/delete", methods=["POST"])
@login_required
def children_delete(id):
    parent_id = session.get("user_id")

    db = get_db()
    db.execute(
        "DELETE FROM children WHERE id = ? AND parent_id = ?", (id, parent_id,)
    )
    db.commit()
    return redirect(url_for("auth.children"))