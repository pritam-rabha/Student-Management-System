import re

ADMIN_USER = "admin"
ADMIN_PASSWORD = "correct horse battery"


def csrf_token(client, path="/login"):
    """Read the CSRF token from a rendered page (follows redirects)."""
    html = client.get(path, follow_redirects=True).get_data(as_text=True)
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match, "CSRF meta tag not found"
    return match.group(1)


def login(client, username=ADMIN_USER, password=ADMIN_PASSWORD, **kwargs):
    token = csrf_token(client)
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": token},
        **kwargs,
    )


def post(client, url, data=None, **kwargs):
    payload = dict(data or {})
    payload["csrf_token"] = csrf_token(client, "/")
    return client.post(url, data=payload, **kwargs)


def student_payload(**overrides):
    data = {
        "student_id": "MCA001",
        "full_name": "Asha Verma",
        "email": "asha.verma@example.com",
        "phone": "+91 98765 43210",
        "course": "MCA",
        "department": "Computer Applications",
        "semester": "2",
        "admission_date": "2025-07-15",
        "date_of_birth": "2002-04-10",
        "marks": "81.5",
        "address": "12 Lake Road, Bhopal",
    }
    data.update(overrides)
    return data
