"""Business logic for student records: validation, CRUD, search, sort."""
import re
from datetime import datetime, timezone

from app.exceptions import StudentNotFoundError, ValidationError
from app.utils.pagination import paginate
from app.utils.validators import normalize_student_id, validate_student

SORT_OPTIONS = ("name", "id", "marks")
ORDER_OPTIONS = ("asc", "desc")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _natural_key(value):
    """Sort 'MCA9' before 'MCA10'."""
    parts = re.split(r"(\d+)", value.lower())
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in parts if p]


def _sort(students, sort, order):
    reverse = order == "desc"
    if sort == "marks":
        # Records without marks always go last, whichever direction is chosen.
        graded = [s for s in students if s.get("marks") is not None]
        ungraded = [s for s in students if s.get("marks") is None]
        # Two stable passes keep ties in name order for both directions.
        graded.sort(key=lambda s: s["full_name"].casefold())
        graded.sort(key=lambda s: s["marks"], reverse=reverse)
        ungraded.sort(key=lambda s: s["full_name"].casefold())
        return graded + ungraded
    if sort == "id":
        return sorted(students, key=lambda s: _natural_key(s["student_id"]), reverse=reverse)
    return sorted(students, key=lambda s: (s["full_name"].casefold(), s["student_id"]), reverse=reverse)


class StudentService:
    def __init__(self, repository):
        self._repo = repository

    def get(self, student_id):
        record = self._repo.get(normalize_student_id(student_id))
        if record is None:
            raise StudentNotFoundError(student_id)
        return record

    def create(self, data):
        cleaned, errors = validate_student(data, require_id=True)
        if errors:
            raise ValidationError(errors)
        now = _now()
        record = {**cleaned, "created_at": now, "updated_at": now}
        self._repo.add(record)  # raises DuplicateStudentError atomically
        return record

    def update(self, student_id, data):
        existing = self.get(student_id)
        cleaned, errors = validate_student(data, require_id=False)
        if errors:
            raise ValidationError(errors)
        return self._repo.update(
            existing["student_id"], {**cleaned, "updated_at": _now()}
        )

    def delete(self, student_id):
        self._repo.delete(normalize_student_id(student_id))

    def recent(self, limit=8):
        students = self._repo.all()
        students.sort(key=lambda s: (s.get("created_at", ""), s["student_id"]), reverse=True)
        return students[:limit]

    def filter_options(self):
        students = self._repo.all()

        def distinct(key):
            seen = {}
            for s in students:
                value = s.get(key)
                if value:
                    seen.setdefault(str(value).casefold(), value)
            return sorted(seen.values(), key=str.casefold)

        return {
            "courses": distinct("course"),
            "departments": distinct("department"),
            "semesters": sorted({s["semester"] for s in students if isinstance(s.get("semester"), int)}),
        }

    def list_students(self, *, search="", department="", course="", semester="",
                      sort="name", order="asc", page=1, per_page=10):
        """Search, filter, sort and paginate. Unknown sort/order values fall back to defaults."""
        students = self._repo.all()

        query = (search or "").strip().casefold()
        if query:
            students = [
                s for s in students
                if query in s["student_id"].casefold()
                or query in s.get("full_name", "").casefold()
                or query in s.get("email", "").casefold()
                or query in s.get("course", "").casefold()
            ]
        if department:
            students = [s for s in students if s.get("department", "").casefold() == department.casefold()]
        if course:
            students = [s for s in students if s.get("course", "").casefold() == course.casefold()]
        if semester and str(semester).isdigit():
            students = [s for s in students if s.get("semester") == int(semester)]

        sort = sort if sort in SORT_OPTIONS else "name"
        order = order if order in ORDER_OPTIONS else "asc"
        return paginate(_sort(students, sort, order), page, per_page)
