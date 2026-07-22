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