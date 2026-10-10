from datetime import date

import pytest

from app.utils.formatting import format_date, format_marks, marks_input
from app.utils.pagination import paginate, parse_page
from app.utils.validators import validate_student
from tests.helpers import student_payload

TODAY = date(2026, 10, 10)


def check(**overrides):
    return validate_student(student_payload(**overrides), today=TODAY)


def test_valid_payload_is_cleaned():
    cleaned, errors = check(student_id=" mca001 ", full_name="  Asha   Verma ", email=" Asha@Example.COM ")
    assert errors == {}
    assert cleaned["student_id"] == "MCA001"
    assert cleaned["full_name"] == "Asha Verma"
    assert cleaned["email"] == "asha@example.com"
    assert cleaned["semester"] == 2 and cleaned["marks"] == 81.5


@pytest.mark.parametrize("email", ["plain", "a@b", "a@@b.com", "a b@c.com", "@c.com", "a@.com", "x" * 250 + "@c.com"])
def test_bad_emails(email):
    assert "email" in check(email=email)[1]


@pytest.mark.parametrize("email", ["a@b.co", "first.last+tag@sub.example.org"])
def test_good_emails(email):
    assert "email" not in check(email=email)[1]


@pytest.mark.parametrize("phone", ["12345", "abcdefghij", "1" * 16, "98765-4321x"])
def test_bad_phones(phone):
    assert "phone" in check(phone=phone)[1]


@pytest.mark.parametrize("phone", ["9876543210", "+91 98765 43210", "(022) 2345-6789"])
def test_good_phones(phone):
    assert "phone" not in check(phone=phone)[1]


@pytest.mark.parametrize("marks,ok", [("0", True), ("100", True), ("99.99", True), ("50.5", True),
                                      ("100.01", False), ("-0.5", False), ("1,5", False), ("NaN", False),
                                      ("Infinity", False), ("12.345", False), ("abc", False)])
def test_marks_validation(marks, ok):
    cleaned, errors = check(marks=marks)
    assert ("marks" not in errors) is ok


def test_blank_marks_become_none():
    assert check(marks="")[0]["marks"] is None


@pytest.mark.parametrize("semester,ok", [("1", True), ("10", True), ("0", False), ("11", False),
                                         ("1.5", False), ("", False), ("x", False)])
def test_semester_validation(semester, ok):
    assert ("semester" not in check(semester=semester)[1]) is ok


@pytest.mark.parametrize("value,ok", [("A1", True), ("mca-2026_01", True), ("A", False), ("-A1", False),
                                      ("A" * 21, False), ("A 1", False), ("../x", False), ("", False)])
def test_student_id_validation(value, ok):
    assert ("student_id" not in check(student_id=value)[1]) is ok


def test_date_validation():
    assert "admission_date" in check(admission_date="2026-10-11")[1]
    assert "admission_date" not in check(admission_date="2026-10-10")[1]
    assert "admission_date" in check(admission_date="10/10/2025")[1]
    assert "admission_date" in check(admission_date="20251010")[1]
    assert "admission_date" in check(admission_date="2025-02-30")[1]
    assert "admission_date" in check(admission_date="")[1]
    assert "date_of_birth" in check(date_of_birth="2027-01-01")[1]
    assert "date_of_birth" in check(date_of_birth="1800-01-01")[1]
    assert check(date_of_birth="")[0]["date_of_birth"] == ""


def test_text_length_and_control_characters():
    assert "full_name" in check(full_name="A")[1]
    assert "full_name" in check(full_name="A" * 101)[1]
    assert "full_name" in check(full_name="Bad\x00Name")[1]
    assert "course" in check(course="")[1]
    assert "department" in check(department="D" * 81)[1]
    assert "address" in check(address="x" * 301)[1]
    assert "address" in check(address="bad\x07address")[1]
    assert check(address="line one\r\nline two")[0]["address"] == "line one\nline two"


def test_missing_keys_are_treated_as_blank():
    cleaned, errors = validate_student({}, today=TODAY)
    assert {"student_id", "full_name", "email", "phone", "course", "department",
            "semester", "admission_date"} <= set(errors)
    assert "marks" not in errors and "address" not in errors


def test_require_id_false_skips_id():
    data = student_payload()
    data.pop("student_id")
    cleaned, errors = validate_student(data, require_id=False, today=TODAY)
    assert errors == {} and "student_id" not in cleaned


def test_paginate_edges():
    assert paginate([], 1, 10)["pages"] == 1
    assert paginate([], 1, 10)["first"] == 0
    page = paginate(list(range(25)), 3, 10)
    assert page["items"] == [20, 21, 22, 23, 24] and page["last"] == 25
    assert paginate(list(range(25)), -4, 10)["page"] == 1


def test_parse_page():
    assert parse_page("3") == 3
    assert parse_page("0") == 1 and parse_page("-2") == 1
    assert parse_page("abc") == 1 and parse_page(None) == 1


def test_formatting_helpers():
    assert format_date("2025-07-05") == "05 Jul 2025"
    assert format_date("") == "-" and format_date("garbage") == "garbage"
    assert format_marks(None) == "Not recorded"
    assert format_marks(80.0) == "80" and format_marks(78.5) == "78.5" and format_marks(0) == "0"
    assert marks_input(None) == "" and marks_input(55.25) == "55.25"
