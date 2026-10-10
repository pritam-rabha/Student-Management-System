"""Server-side validation and normalisation of student input."""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

MIN_SEMESTER = 1
MAX_SEMESTER = 10
MAX_MARKS = Decimal("100")

STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,19}$")
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)
PHONE_RE = re.compile(r"^\+?[0-9\s().-]+$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

STUDENT_FIELDS = (
    "student_id",
    "full_name",
    "email",
    "phone",
    "course",
    "department",
    "semester",
    "admission_date",
    "date_of_birth",
    "marks",
    "address",
)


def normalize_student_id(value):
    return (value or "").strip().upper()


def _text(data, key):
    value = data.get(key)
    return "" if value is None else str(value)


def _single_line(data, key):
    return " ".join(_text(data, key).split())


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_student(data, *, require_id=True, today=None):
    """Validate raw form data.

    Returns (cleaned, errors). cleaned only holds fields that passed; errors
    maps field name to a user-facing message. The caller decides what to do
    when errors is not empty.
    """
    today = today or date.today()
    cleaned = {}
    errors = {}

    if require_id:
        student_id = normalize_student_id(_text(data, "student_id"))
        if not student_id:
            errors["student_id"] = "Student ID is required."
        elif not STUDENT_ID_RE.match(student_id):
            errors["student_id"] = (
                "Use 2 to 20 letters, digits, hyphens or underscores, "
                "starting with a letter or digit."
            )
        else:
            cleaned["student_id"] = student_id

    full_name = _single_line(data, "full_name")
    if not full_name:
        errors["full_name"] = "Full name is required."
    elif not 2 <= len(full_name) <= 100:
        errors["full_name"] = "Full name must be between 2 and 100 characters."
    elif CONTROL_RE.search(full_name):
        errors["full_name"] = "Full name contains invalid characters."
    else:
        cleaned["full_name"] = full_name

    email = _text(data, "email").strip().lower()
    if not email:
        errors["email"] = "Email address is required."
    elif len(email) > 254 or not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address, for example name@example.com."
    else:
        cleaned["email"] = email

    phone = _single_line(data, "phone")
    digits = re.sub(r"\D", "", phone)
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not PHONE_RE.match(phone) or not 7 <= len(digits) <= 15:
        errors["phone"] = "Enter a phone number with 7 to 15 digits."
    else:
        cleaned["phone"] = phone

    for key, label in (("course", "Course"), ("department", "Department")):
        value = _single_line(data, key)
        if not value:
            errors[key] = f"{label} is required."
        elif not 2 <= len(value) <= 80 or CONTROL_RE.search(value):
            errors[key] = f"{label} must be between 2 and 80 characters."
        else:
            cleaned[key] = value

    semester_raw = _text(data, "semester").strip()
    if not semester_raw:
        errors["semester"] = "Semester is required."
    elif not (semester_raw.isascii() and semester_raw.isdigit()):
        errors["semester"] = "Semester must be a whole number."
    elif not MIN_SEMESTER <= int(semester_raw) <= MAX_SEMESTER:
        errors["semester"] = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
    else:
        cleaned["semester"] = int(semester_raw)

    admission = None
    admission_raw = _text(data, "admission_date").strip()
    if not admission_raw:
        errors["admission_date"] = "Admission date is required."
    else:
        admission = _parse_date(admission_raw)
        if admission is None:
            errors["admission_date"] = "Enter a valid date (YYYY-MM-DD)."
        elif admission > today:
            errors["admission_date"] = "Admission date cannot be in the future."
        elif admission.year < 1950:
            errors["admission_date"] = "Admission date is too far in the past."
        else:
            cleaned["admission_date"] = admission.isoformat()

    dob_raw = _text(data, "date_of_birth").strip()
    if not dob_raw:
        cleaned["date_of_birth"] = ""
    else:
        dob = _parse_date(dob_raw)
        if dob is None:
            errors["date_of_birth"] = "Enter a valid date (YYYY-MM-DD)."
        elif dob >= today or dob.year < 1900:
            errors["date_of_birth"] = "Enter a realistic date of birth in the past."
        elif admission is not None and dob >= admission:
            errors["date_of_birth"] = "Date of birth must be before the admission date."
        else:
            cleaned["date_of_birth"] = dob.isoformat()

    marks_raw = _text(data, "marks").strip()
    if not marks_raw:
        cleaned["marks"] = None
    else:
        try:
            marks = Decimal(marks_raw)
        except InvalidOperation:
            marks = None
        if marks is None or not marks.is_finite():
            errors["marks"] = "Marks must be a number between 0 and 100."
        elif not Decimal("0") <= marks <= MAX_MARKS:
            errors["marks"] = "Marks must be between 0 and 100."
        elif marks.as_tuple().exponent < -2:
            errors["marks"] = "Marks can have at most two decimal places."
        else:
            cleaned["marks"] = float(marks)

    address = _text(data, "address").replace("\r\n", "\n").strip()
    if len(address) > 300:
        errors["address"] = "Address must be 300 characters or fewer."
    elif CONTROL_RE.search(address):
        errors["address"] = "Address contains invalid characters."
    else:
        cleaned["address"] = address

    return cleaned, errors
