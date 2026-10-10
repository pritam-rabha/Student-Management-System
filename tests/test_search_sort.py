from tests.helpers import student_payload


def ids(result):
    return [s["student_id"] for s in result["items"]]


def page_ids(client, query=""):
    html = client.get("/students/" + query).get_data(as_text=True)
    return html


def test_listing_shows_all_students(auth_client, populated):
    response = auth_client.get("/students/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for name in ("Alice Kumar", "Bob Singh", "Carol Das", "Dan Roy", "Eve Paul", "Frank Lee"):
        assert name in body
    assert "6 records" in body


def test_search_by_name_id_email_and_course(populated):
    svc = populated.students
    assert ids(svc.list_students(search="alice")) == ["A101"]
    assert ids(svc.list_students(search="a104")) == ["A104"]
    assert ids(svc.list_students(search="CAROL@EXAMPLE")) == ["A103"]
    assert ids(svc.list_students(search="mba")) == ["A104", "A105"]
    assert ids(svc.list_students(search="  alice  ")) == ["A101"]


def test_search_has_no_matches(auth_client, populated):
    response = auth_client.get("/students/?q=zzzzzz")
    assert response.status_code == 200
    assert b"No students match your search" in response.data
    assert b"Clear search and filters" in response.data


def test_filters(populated):
    svc = populated.students
    assert ids(svc.list_students(course="BCA")) == ["A103", "A110"]
    assert ids(svc.list_students(course="bca")) == ["A103", "A110"]
    assert ids(svc.list_students(department="Management Studies")) == ["A104", "A105"]
    assert ids(svc.list_students(semester="1")) == ["A101", "A102"]
    assert ids(svc.list_students(course="MCA", semester="3")) == []
    assert ids(svc.list_students(course="BCA", semester="3", search="frank")) == ["A110"]


def test_invalid_semester_filter_is_ignored(populated):
    assert populated.students.list_students(semester="abc")["total"] == 6


def test_filters_work_through_the_web_ui(auth_client, populated):
    body = auth_client.get("/students/?course=MBA&semester=2").get_data(as_text=True)
    assert "Dan Roy" in body and "Eve Paul" in body
    assert "Alice Kumar" not in body


def test_sort_by_name(populated):
    svc = populated.students
    assert ids(svc.list_students(sort="name", order="asc")) == ["A101", "A102", "A103", "A104", "A105", "A110"]
    assert ids(svc.list_students(sort="name", order="desc")) == ["A110", "A105", "A104", "A103", "A102", "A101"]


def test_sort_by_student_id_is_natural(populated):
    svc = populated.students
    assert ids(svc.list_students(sort="id", order="asc"))[-2:] == ["A105", "A110"]
    assert ids(svc.list_students(sort="id", order="desc"))[0] == "A110"


def test_sort_by_marks_puts_missing_marks_last(populated):
    svc = populated.students
    asc = ids(svc.list_students(sort="marks", order="asc"))
    desc = ids(svc.list_students(sort="marks", order="desc"))
    assert asc == ["A110", "A103", "A102", "A101", "A104", "A105"]
    assert desc == ["A101", "A104", "A102", "A103", "A110", "A105"]


def test_unknown_sort_values_fall_back_to_defaults(populated):
    result = populated.students.list_students(sort="password", order="sideways")
    assert ids(result)[0] == "A101"


def test_sort_through_the_web_ui(auth_client, populated):
    body = auth_client.get("/students/?sort=marks&order=desc").get_data(as_text=True)
    assert body.index("Alice Kumar") < body.index("Bob Singh") < body.index("Frank Lee")
    assert 'aria-sort="descending"' in body


def test_pagination(auth_client, services):
    for n in range(1, 26):
        services.students.create(student_payload(
            student_id=f"P{n:03d}", full_name=f"Student {n:03d}", email=f"s{n}@example.com"))
    page1 = services.students.list_students(per_page=10, page=1)
    page3 = services.students.list_students(per_page=10, page=3)
    assert page1["total"] == 25 and page1["pages"] == 3
    assert len(page1["items"]) == 10 and len(page3["items"]) == 5
    assert page3["has_prev"] and not page3["has_next"]

    clamped = services.students.list_students(per_page=10, page=99)
    assert clamped["page"] == 3

    body = auth_client.get("/students/?page=2").get_data(as_text=True)
    assert "Student 011" in body and "Student 001" not in body
    assert "Showing 11 to 20 of 25" in body
    assert 'aria-label="Pagination"' in body


def test_invalid_page_values_do_not_crash(auth_client, populated):
    for query in ("page=abc", "page=-5", "page=0", "per_page=abc", "per_page=100000"):
        assert auth_client.get(f"/students/?{query}").status_code == 200


def test_empty_directory_state(auth_client):
    response = auth_client.get("/students/")
    assert response.status_code == 200
    assert b"No students yet" in response.data


def test_filter_options_are_distinct_and_sorted(populated):
    options = populated.students.filter_options()
    assert options["courses"] == ["BCA", "MBA", "MCA"]
    assert options["departments"] == ["Computer Applications", "Management Studies"]
    assert options["semesters"] == [1, 2, 3]
