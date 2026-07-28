from flask import Blueprint, render_template, request, session, redirect, url_for, abort
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

@bp.route("/children/<int:id>/edit", methods=["POST","GET"])
@login_required
def edit_children(id):
    parent_id = session.get("user_id")

    if request.method == "GET":
        db = get_db()
        child = db.execute(
            "SELECT name, birth_year, utr FROM children WHERE id = ? AND parent_id = ?", (id, parent_id,)
        ).fetchone()

        if child is None:
            abort(404)
        return render_template("edit_child.html", child=child)

    if request.method == "POST":
        name = request.form["name"]
        birth_year = request.form["birth_year"]
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
            "UPDATE children SET name = ?, birth_year = ?, utr = ? WHERE parent_id = ?",
            (name, birth_year, utr, parent_id,)
        )
        db.commit()

        return redirect(url_for("auth.children"))

@bp.route("/enroll", methods=["POST"])
@login_required
def enroll_child():
    parent_id = session.get("user_id")

    child_id = request.form["child_id"]
    option_id = request.form["option_id"]

    db = get_db()
    child = db.execute(
        "SELECT id FROM children WHERE id = ? AND parent_id = ?", (child_id, parent_id,)
    ).fetchone()

    if child is None:
        abort(404)

    option = db.execute(
        "SELECT id, price_nonmember_cents FROM program_options WHERE id = ? AND active = 1",
        (option_id,)
    ).fetchone()

    if option is None:
        abort(404)

    amount_cents = option['price_nonmember_cents']

    existing = db.execute(
        "SELECT id FROM enrollments WHERE child_id = ? AND option_id = ?", (child_id, option_id,)
    ).fetchone()
    if existing:
        return "Child is already enrolled."

    db.execute(
        "INSERT INTO enrollments (child_id, option_id, status, amount_cents) VALUES (?, ?, ?, ?)",
        (child_id, option_id, 'pending', amount_cents,)
    )
    db.commit()

    return redirect(url_for("auth.children"))

@bp.route("/enrollments", methods=["GET"])
@login_required
def enrollments():
    parent_id = session.get("user_id")

    db = get_db()

    enrolled = db.execute(
        "SELECT e.id, e.status, e.amount_cents, c.name AS child_name, p.name AS program_name, po.label AS option_label FROM enrollments e JOIN children c ON e.child_id = c.id JOIN program_options po ON e.option_id = po.id JOIN programs p ON po.program_id = p.id WHERE c.parent_id = ?", (parent_id,)
    ).fetchall()

    return render_template("enrollments.html", enrolled=enrolled)

