"""Session-bound CSRF protection for all state-changing requests."""
import secrets
from hmac import compare_digest

from flask import request, session
from werkzeug.exceptions import BadRequest

SESSION_KEY = "_csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFError(BadRequest):
    description = "Your session expired or the form could not be verified. Reload the page and try again."


def get_csrf_token():
    token = session.get(SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_KEY] = token
    return token


def validate_csrf():
    if request.method in SAFE_METHODS:
        return
    expected = session.get(SESSION_KEY, "")
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRFToken", "")
    if not expected or not supplied or not compare_digest(expected, supplied):
        raise CSRFError()
