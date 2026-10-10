import json

from tests.helpers import post, student_payload


def test_create_student_and_view_details(auth_client, services):
    response = post(auth_client, "/students/new", student_payload())
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/students/MCA001")

    stored = services.repository.get("MCA001")
    assert stored["full_name"] == "Asha Verma"
    assert stored["semester"] == 2
    assert stored["marks"] == 81.5
    assert stored["created_at"] and stored["updated_at"]

    page = auth_client.get("/students/MCA001")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Asha Verma" in body and "asha.verma@example.com" in body and "81.5" in body


def test_student_id_is_normalised_to_upper_case(auth_client, services):
    post(auth_client, "/students/new", student_payload(student_id="mca777"))
    assert services.repository.get("MCA777") is not None
    assert auth_client.get("/students/mca777").status_code == 200


def test_optional_fields_may_be_blank(auth_client, services):
    response = post(auth_client, "/students/new",
                    student_payload(date_of_birth="", address="", marks=""))
    assert response.status_code == 302
    stored = services.repository.get("MCA001")
    assert stored["marks"] is None and stored["date_of_birth"] == "" and stored["address"] == ""
    page = auth_client.get("/students/MCA001").get_data(as_text=True)
    assert "Not recorded" in page


def test_duplicate_student_id_is_rejected(auth_client, services):
    post(auth_client, "/students/new", student_payload())
    response = post(auth_client, "/students/new",
                    student_payload(full_name="Someone Else", email="else@example.com"))
    assert response.status_code == 409
    assert b"already exists" in response.data
    assert len(services.repository.all()) == 1
    assert services.repository.get("MCA001")["full_name"] == "Asha Verma"


def test_duplicate_id_check_ignores_case(auth_client, services):
    post(auth_client, "/students/new", student_payload(student_id="abc12"))
    response = post(auth_client, "/students/new", student_payload(student_id="ABC12"))
    assert response.status_code == 409


def test_invalid_marks_are_rejected(auth_client, services):
    for bad in ("101", "-1", "abc", "nan", "inf", "80.123", "1e500"):
        response = post(auth_client, "/students/new", student_payload(marks=bad))
        assert response.status_code == 400, bad
        assert b"Marks" in response.data
    assert services.repository.all() == []


def test_marks_boundaries_are_accepted(auth_client, services):
    assert post(auth_client, "/students/new", student_payload(student_id="Z0", marks="0")).status_code == 302
    assert post(auth_client, "/students/new", student_payload(student_id="Z100", marks="100")).status_code == 302
    assert services.repository.get("Z0")["marks"] == 0
    assert services.repository.get("Z100")["marks"] == 100


def test_invalid_fields_show_errors_and_keep_input(auth_client):
    response = post(auth_client, "/students/new", student_payload(
        email="not-an-email", semester="0", phone="abc", full_name="", student_id="!!",
        admission_date="2999-01-01"))
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    for message in ("valid email", "Semester must be between", "7 to 15 digits",
                    "Full name is required", "Use 2 to 20 letters", "cannot be in the future"):
        assert message in body
    assert 'value="not-an-email"' in body


def test_dob_must_precede_admission(auth_client):
    response = post(auth_client, "/students/new",
                    student_payload(date_of_birth="2025-08-01", admission_date="2025-07-15"))
    assert response.status_code == 400
    assert b"before the admission date" in response.data


def test_semester_must_be_whole_number(auth_client):
    for bad in ("1.5", "eleven", "11", "-2"):
        response = post(auth_client, "/students/new", student_payload(semester=bad))
        assert response.status_code == 400, bad


def test_script_input_is_escaped(auth_client):
    post(auth_client, "/students/new", student_payload(full_name="<script>alert(1)</script>"))
    page = auth_client.get("/students/MCA001").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_edit_student(auth_client, services):
    post(auth_client, "/students/new", student_payload())
    form = auth_client.get("/students/MCA001/edit")
    assert form.status_code == 200 and b"Asha Verma" in form.data

    payload = student_payload(full_name="Asha V. Verma", marks="92", semester="3")
    payload.pop("student_id")
    response = post(auth_client, "/students/MCA001/edit", payload)
    assert response.status_code == 302
    stored = services.repository.get("MCA001")
    assert stored["full_name"] == "Asha V. Verma"
    assert stored["marks"] == 92 and stored["semester"] == 3
    assert stored["created_at"] <= stored["updated_at"]


def test_edit_cannot_change_student_id(auth_client, services):
    post(auth_client, "/students/new", student_payload())
    post(auth_client, "/students/MCA001/edit", student_payload(student_id="HACKED1"))
    assert services.repository.get("HACKED1") is None
    assert services.repository.get("MCA001") is not None


def test_edit_with_invalid_data_keeps_original(auth_client, services):
    post(auth_client, "/students/new", student_payload())
    response = post(auth_client, "/students/MCA001/edit", student_payload(marks="500"))
    assert response.status_code == 400
    assert services.repository.get("MCA001")["marks"] == 81.5


def test_delete_student(auth_client, services):
    post(auth_client, "/students/new", student_payload())
    response = post(auth_client, "/students/MCA001/delete")
    assert response.status_code == 302
    assert services.repository.get("MCA001") is None
    assert auth_client.get("/students/MCA001").status_code == 404


def test_delete_requires_post(auth_client):
    post(auth_client, "/students/new", student_payload())
    assert auth_client.get("/students/MCA001/delete").status_code == 405


def test_missing_student_returns_404(auth_client):
    assert auth_client.get("/students/NOPE1").status_code == 404
    assert auth_client.get("/students/NOPE1/edit").status_code == 404
    assert post(auth_client, "/students/NOPE1/edit", student_payload()).status_code == 404
    assert post(auth_client, "/students/NOPE1/delete").status_code == 404


def test_path_traversal_in_student_id_is_harmless(auth_client):
    assert auth_client.get("/students/..%2F..%2Fetc%2Fpasswd").status_code == 404
    assert auth_client.get("/students/%00").status_code == 404


def test_form_without_csrf_token_is_rejected(auth_client, services):
    response = auth_client.post("/students/new", data=student_payload())
    assert response.status_code == 400
    assert services.repository.all() == []


def test_form_with_wrong_csrf_token_is_rejected(auth_client, services):
    response = auth_client.post("/students/new", data={**student_payload(), "csrf_token": "forged"})
    assert response.status_code == 400
    assert services.repository.all() == []


def test_oversized_request_is_rejected(auth_client):
    response = auth_client.post("/students/new", data={"address": "x" * 200_000})
    assert response.status_code == 413


def test_data_persists_across_application_restart(app, tmp_path):
    from app import create_app
    from tests.helpers import login

    client = app.test_client()
    login(client)
    post(client, "/students/new", student_payload())

    restarted = create_app({**app.config, "SEED_SAMPLE_DATA": True})
    assert restarted.extensions["sms"].repository.get("MCA001")["full_name"] == "Asha Verma"
    # demo data must not overwrite or be mixed into the existing file
    assert len(restarted.extensions["sms"].repository.all()) == 1


def test_data_file_is_valid_json_with_documented_shape(auth_client, app):
    post(auth_client, "/students/new", student_payload())
    path = app.config["DATA_DIR"] / "students.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["students"][0]["student_id"] == "MCA001"
