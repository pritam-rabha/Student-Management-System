"""Administrator login and logout."""
from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.services import get_services

bp = Blueprint("auth", __name__)

MAX_FIELD_LENGTH = 256


def _safe_next(target):
    """Only allow redirects to local paths; reject absolute and protocol-relative URLs."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return url_for("dashboard.index")
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return url_for("dashboard.index")
    return target


def _render_login(error, status, next_url, username=""):
    return render_template("login.html", error=error, next_url=next_url, username=username), status


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_user"):
        return redirect(url_for("dashboard.index"))

    services = get_services()
    next_url = request.values.get("next", "")

    if request.method == "GET":
        return render_template("login.html", error=None, next_url=next_url, username="")

    client = request.remote_addr or "unknown"
    username = request.form.get("username", "").strip()[:MAX_FIELD_LENGTH]
    password = request.form.get("password", "")[:MAX_FIELD_LENGTH]

    wait = services.throttle.seconds_blocked(client)
    if wait:
        minutes = max(1, (wait + 59) // 60)
        return _render_login(
            f"Too many failed sign-in attempts. Try again in about {minutes} minute(s).",
            429, next_url, username,
        )

    if not services.auth.configured:
        current_app.logger.error("Login attempted but no administrator account is configured.")
        return _render_login(
            "Sign-in is not available because the administrator account has not been set up.",
            503, next_url,
        )

    if not username or not password:
        return _render_login("Enter both your username and password.", 400, next_url, username)

    if not services.auth.verify(username, password):
        services.throttle.record_failure(client)
        current_app.logger.warning("Failed login attempt for username %r", username[:64])
        return _render_login("Invalid username or password.", 401, next_url, username)

    services.throttle.reset(client)
    session.clear()  # new session on privilege change prevents fixation
    session["admin_user"] = services.auth.username
    session.permanent = True
    flash("Signed in successfully.", "success")
    return redirect(_safe_next(next_url))


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
