from werkzeug.security import generate_password_hash

from app import create_app
from app.utils.rate_limit import LoginThrottle
from tests.helpers import ADMIN_PASSWORD, csrf_token, login, post


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Administrator sign in" in response.data


def test_login_success_redirects_to_dashboard(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert client.get("/").status_code == 200


def test_login_wrong_password_shows_error(client):
    response = login(client, password="wrong password")
    assert response.status_code == 401
    assert b"Invalid username or password." in response.data
    assert client.get("/").status_code == 302


def test_login_wrong_username_shows_same_error(client):
    response = login(client, username="someone-else")
    assert response.status_code == 401
    assert b"Invalid username or password." in response.data


def test_login_empty_fields(client):
    response = login(client, username="", password="")
    assert response.status_code == 400
    assert b"Enter both your username and password." in response.data


def test_logout_requires_post_and_ends_session(auth_client):
    assert auth_client.get("/logout").status_code == 405
    response = post(auth_client, "/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    protected = auth_client.get("/students/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_logout_without_csrf_token_is_rejected(auth_client):
    response = auth_client.post("/logout")
    assert response.status_code == 400
    assert auth_client.get("/").status_code == 200


def test_login_post_without_csrf_token_is_rejected(client):
    response = client.post("/login", data={"username": "admin", "password": ADMIN_PASSWORD})
    assert response.status_code == 400


def test_login_redirects_to_requested_page(client):
    response = client.get("/reports/")
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith("/login?next=") and "/reports/" in location
    token = csrf_token(client)
    response = client.post("/login", data={
        "username": "admin", "password": ADMIN_PASSWORD, "csrf_token": token, "next": "/reports/",
    })
    assert response.headers["Location"].endswith("/reports/")


def test_open_redirect_is_blocked(client):
    for target in ("https://evil.example/", "//evil.example/", "/\\evil.example"):
        token = csrf_token(client)
        response = client.post("/login", data={
            "username": "admin", "password": ADMIN_PASSWORD, "csrf_token": token, "next": target,
        })
        assert response.status_code == 302
        assert "evil.example" not in response.headers["Location"]
        client.post("/logout", data={"csrf_token": csrf_token(client, "/")})


def test_authenticated_user_visiting_login_is_redirected(auth_client):
    assert auth_client.get("/login").status_code == 302


def test_failed_logins_are_throttled(app, client):
    app.extensions["sms"].throttle = LoginThrottle(max_attempts=3, window_seconds=300)
    for _ in range(3):
        assert login(client, password="nope").status_code == 401
    blocked = login(client, password=ADMIN_PASSWORD)
    assert blocked.status_code == 429
    assert b"Too many failed sign-in attempts" in blocked.data


def test_throttle_expires_with_time():
    now = [1000.0]
    throttle = LoginThrottle(max_attempts=2, window_seconds=60, clock=lambda: now[0])
    throttle.record_failure("ip")
    throttle.record_failure("ip")
    assert throttle.seconds_blocked("ip") > 0
    now[0] += 61
    assert throttle.seconds_blocked("ip") == 0


def test_unconfigured_admin_cannot_sign_in(tmp_path):
    app = create_app({
        "TESTING": True, "APP_ENV": "testing", "SECRET_KEY": "x" * 32,
        "DATA_DIR": tmp_path, "SEED_SAMPLE_DATA": False,
        "ADMIN_PASSWORD_HASH": None, "ADMIN_PASSWORD": None,
    })
    client = app.test_client()
    response = login(client, password="anything")
    assert response.status_code == 503
    assert b"has not been set up" in response.data


def test_plain_password_setting_is_hashed_in_memory(tmp_path):
    app = create_app({
        "TESTING": True, "APP_ENV": "testing", "SECRET_KEY": "x" * 32,
        "DATA_DIR": tmp_path, "SEED_SAMPLE_DATA": False,
        "ADMIN_PASSWORD_HASH": None, "ADMIN_PASSWORD": "local-trial-password",
    })
    auth = app.extensions["sms"].auth
    assert auth.configured
    assert auth._hash != "local-trial-password"
    assert auth.verify("admin", "local-trial-password")
    assert not auth.verify("admin", "other")


def test_hash_from_env_style_value_verifies(tmp_path):
    app = create_app({
        "TESTING": True, "APP_ENV": "testing", "SECRET_KEY": "x" * 32,
        "DATA_DIR": tmp_path, "SEED_SAMPLE_DATA": False,
        "ADMIN_USERNAME": "registrar",
        "ADMIN_PASSWORD_HASH": generate_password_hash("s3cret-pass-phrase"),
    })
    client = app.test_client()
    assert login(client, "registrar", "s3cret-pass-phrase").status_code == 302


def test_production_requires_secret_key(tmp_path):
    import pytest
    with pytest.raises(RuntimeError):
        create_app({"APP_ENV": "production", "SECRET_KEY": None, "DATA_DIR": tmp_path,
                    "SEED_SAMPLE_DATA": False})
