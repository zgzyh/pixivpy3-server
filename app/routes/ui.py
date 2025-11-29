from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from app.config import config

ui_bp = Blueprint("ui", __name__, url_prefix="/ui")

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("ui.login"))
        return f(*args, **kwargs)
    return decorated

@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        token = request.form.get("token", "")
        if token == config.auth_token:
            session["authenticated"] = True
            return redirect(url_for("ui.dashboard"))
        error = "Invalid token"
    return render_template("login.html", error=error)

@ui_bp.route("/logout")
def logout():
    session.pop("authenticated", None)
    return redirect(url_for("ui.login"))

@ui_bp.route("/")
@require_login
def dashboard():
    from app.pool import pool
    return render_template("dashboard.html", accounts=pool.status(), total=len(pool.accounts), config=config)
