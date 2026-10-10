import pytest

from tests.helpers import csrf_token, student_payload

PROTECTED_GET = [
    "/", "/students/", "/students/new", "/students/MCA001", "/students/MCA001/edit", "/reports/",
]
PROTECTED_POST = ["/students/new", "/students/MCA001/edit", "/students/MCA001/delete"]


@pytest.mark.parametrize("url", PROTECTED_GET)
def test_pages_redirect_anonymous_users_to_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")


@pytest.mark.parametrize("url", PROTECTED_POST)
def test_state_changing_requests_blocked_for_anonymous_users(client, services, url):
    token = csrf_token(client)
    response = client.post(url, data={**student_payload(), "csrf_token": token})
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")
    assert services.repository.all() == []


def test_health_and_login_are_public(client):
    assert client.get("/healthz").get_json() == {"status": "ok"}
    assert client.get("/login").status_code == 200


def test_static_assets_are_public(client):
    assert client.get("/static/css/app.css").status_code == 200


def test_unknown_url_returns_404_page(client):
    response = client.get("/no/such/page")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_error_pages_do_not_leak_internals(app, auth_client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret-internal-detail /srv/app/path")

    monkeypatch.setattr(app.extensions["sms"].reports, "summary", boom)
    app.testing = False
    app.config["PROPAGATE_EXCEPTIONS"] = False
    response = auth_client.get("/")
    assert response.status_code == 500
    body = response.get_data(as_text=True)
    assert "secret-internal-detail" not in body
    assert "Traceback" not in body
    assert "Something went wrong" in body


def test_security_headers_and_cache_policy(auth_client):
    response = auth_client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Cache-Control"] == "no-store"


def test_session_cookie_flags(client):
    from tests.helpers import login
    response = login(client)
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
