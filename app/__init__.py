"""Application factory for the Student Management System."""
import logging
import secrets
from types import SimpleNamespace

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.exceptions import StorageError, StudentNotFoundError
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.services.student_service import StudentService
from app.storage.json_store import JsonFileStore, JsonStudentRepository
from app.storage.seed import seed_if_missing
from app.utils.csrf import CSRFError, get_csrf_token, validate_csrf
from app.utils.formatting import format_date, format_marks, format_timestamp, marks_input
from app.utils.rate_limit import LoginThrottle

PUBLIC_ENDPOINTS = {"auth.login", "static", "health"}

ERROR_TEXT = {
    400: ("Bad request", "The request could not be processed. Check the details and try again."),
    401: ("Sign in required", "You need to sign in to view this page."),
    403: ("Access denied", "You do not have permission to perform this action."),
    404: ("Page not found", "The page or record you asked for does not exist."),
    405: ("Method not allowed", "That action is not supported for this address."),
    413: ("Request too large", "The submitted data is larger than allowed."),
    429: ("Too many requests", "Please wait a moment before trying again."),
    500: ("Something went wrong", "An unexpected error occurred. The problem has been logged. Please try again."),
    503: ("Service unavailable", "The data store is temporarily unavailable. Please try again shortly."),
}


def create_app(test_config=None):
    from config import load_config

    app = Flask(__name__)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)

    _configure_logging(app)
    _configure_secret_key(app)
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _init_services(app)
    _register_blueprints(app)
    _register_hooks(app)
    _register_error_handlers(app)
    _register_template_helpers(app)
    return app


def _configure_logging(app):
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )


def _configure_secret_key(app):
    if app.config.get("SECRET_KEY"):
        return
    if app.config["APP_ENV"] == "production":
        raise RuntimeError("SECRET_KEY must be set when APP_ENV=production.")
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.logger.warning(
        "SECRET_KEY is not set. Using a temporary key; sessions end when the app restarts."
    )


def _init_services(app):
    data_dir = app.config["DATA_DIR"]
    store = JsonFileStore(data_dir / "students.json")
    repository = JsonStudentRepository(store)

    if app.config["SEED_SAMPLE_DATA"]:
        seed_if_missing(store, app.config["SAMPLE_DATA_FILE"])

    auth = AuthService(
        app.config["ADMIN_USERNAME"],
        password_hash=app.config.get("ADMIN_PASSWORD_HASH"),
        password=app.config.get("ADMIN_PASSWORD"),
    )
    if not auth.configured:
        app.logger.warning(
            "Administrator account is not configured. Set ADMIN_USERNAME and "
            "ADMIN_PASSWORD_HASH (see README) before signing in."
        )
    elif app.config.get("ADMIN_PASSWORD") and not app.config.get("ADMIN_PASSWORD_HASH") \
            and app.config["APP_ENV"] == "production":
        app.logger.warning("ADMIN_PASSWORD is set in production; prefer ADMIN_PASSWORD_HASH.")

    app.extensions["sms"] = SimpleNamespace(
        repository=repository,
        students=StudentService(repository),
        reports=ReportService(repository),
        auth=auth,
        throttle=LoginThrottle(
            app.config["LOGIN_MAX_ATTEMPTS"], app.config["LOGIN_LOCKOUT_SECONDS"]
        ),
    )


def _register_blueprints(app):
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.students import bp as students_bp

    for blueprint in (auth_bp, dashboard_bp, students_bp, reports_bp):
        app.register_blueprint(blueprint)

    @app.get("/healthz", endpoint="health")
    def health():
        return jsonify(status="ok")


def _register_hooks(app):
    @app.before_request
    def require_login():
        # Every endpoint is private unless explicitly listed as public.
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if session.get("admin_user"):
            return None
        flash("Please sign in to continue.", "warning")
        if request.method == "GET":
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return redirect(url_for("auth.login"))

    @app.before_request
    def csrf_protect():
        validate_csrf()

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'",
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response


def _register_error_handlers(app):
    def render_error(code, message=None):
        title, default_message = ERROR_TEXT.get(code, ERROR_TEXT[500])
        return render_template(
            "errors/error.html", code=code, title=title, message=message or default_message
        ), code

    @app.errorhandler(StudentNotFoundError)
    def handle_missing_student(error):
        return render_error(404, "That student record does not exist. It may have been deleted.")

    @app.errorhandler(StorageError)
    def handle_storage_error(error):
        app.logger.error("Storage failure: %s", error)
        return render_error(503)

    @app.errorhandler(CSRFError)
    def handle_csrf(error):
        app.logger.warning("CSRF validation failed for %s %s", request.method, request.path)
        return render_error(400, CSRFError.description)

    @app.errorhandler(HTTPException)
    def handle_http(error):
        code = error.code or 500
        if code >= 500:
            app.logger.error("HTTP %s on %s", code, request.path)
        return render_error(code if code in ERROR_TEXT else 500)

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        # Full details go to the log only; the user sees a generic message.
        app.logger.exception("Unhandled error on %s %s", request.method, request.path)
        return render_error(500)


def _register_template_helpers(app):
    app.jinja_env.filters["fmt_date"] = format_date
    app.jinja_env.filters["fmt_marks"] = format_marks
    app.jinja_env.filters["fmt_timestamp"] = format_timestamp
    app.jinja_env.filters["marks_input"] = marks_input

    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": get_csrf_token,
            "current_user": session.get("admin_user"),
            "nav_section": request.blueprint,
        }
