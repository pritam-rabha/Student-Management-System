import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from tests.helpers import ADMIN_PASSWORD, ADMIN_USER, login, student_payload


@pytest.fixture
def app(tmp_path):
    """An application wired to an isolated temporary data directory."""
    application = create_app({
        "TESTING": True,
        "APP_ENV": "testing",
        "SECRET_KEY": "test-secret-key-not-for-production",
        "DATA_DIR": tmp_path / "data",
        "SEED_SAMPLE_DATA": False,
        "ADMIN_USERNAME": ADMIN_USER,
        # Low iteration count keeps the suite fast; production uses the full default.
        "ADMIN_PASSWORD_HASH": generate_password_hash(ADMIN_PASSWORD, method="pbkdf2:sha256:1000"),
        "ADMIN_PASSWORD": None,
        "SESSION_COOKIE_SECURE": False,
        "LOGIN_MAX_ATTEMPTS": 100,
    })
    return application


@pytest.fixture
def services(app):
    return app.extensions["sms"]


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    response = login(client)
    assert response.status_code == 302
    return client


# Known data set used by the search, sort and report tests.
DATASET = [
    dict(student_id="A101", full_name="Alice Kumar", email="alice@example.com", course="MCA",
         department="Computer Applications", semester="1", marks="90"),
    dict(student_id="A102", full_name="Bob Singh", email="bob@example.com", course="MCA",
         department="Computer Applications", semester="1", marks="80"),
    dict(student_id="A103", full_name="Carol Das", email="carol@example.com", course="BCA",
         department="Computer Applications", semester="3", marks="70"),
    dict(student_id="A104", full_name="Dan Roy", email="dan@example.com", course="MBA",
         department="Management Studies", semester="2", marks="90"),
    dict(student_id="A105", full_name="Eve Paul", email="eve@example.com", course="MBA",
         department="Management Studies", semester="2", marks=""),
    dict(student_id="A110", full_name="Frank Lee", email="frank@example.com", course="BCA",
         department="Computer Applications", semester="3", marks="55.5"),
]


@pytest.fixture
def populated(services):
    for row in DATASET:
        services.students.create(student_payload(**row))
    return services
