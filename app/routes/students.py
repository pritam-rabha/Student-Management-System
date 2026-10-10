"""Student CRUD, search, filtering and sorting."""
from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.exceptions import DuplicateStudentError, ValidationError
from app.services import get_services
from app.utils.pagination import parse_page
from app.utils.validators import MAX_SEMESTER, MIN_SEMESTER, STUDENT_FIELDS

bp = Blueprint("students", __name__, url_prefix="/students")

PER_PAGE_CHOICES = (10, 25, 50)


def _form_values():
    return {name: request.form.get(name, "") for name in STUDENT_FIELDS}


def _form_context(**extra):
    services = get_services()
    return {
        "options": services.students.filter_options(),
        "semester_range": range(MIN_SEMESTER, MAX_SEMESTER + 1),
        "today": date.today().isoformat(),
        **extra,
    }


@bp.get("/")
def list_students():
    services = get_services()
    args = request.args
    try:
        per_page = int(args.get("per_page", current_app.config["PER_PAGE"]))
    except ValueError:
        per_page = current_app.config["PER_PAGE"]
    if per_page not in PER_PAGE_CHOICES:
        per_page = current_app.config["PER_PAGE"]

    filters = {
        "search": args.get("q", "").strip()[:100],
        "department": args.get("department", "").strip(),
        "course": args.get("course", "").strip(),
        "semester": args.get("semester", "").strip(),
    }
    sort = args.get("sort", "name")
    order = args.get("order", "asc")

    result = services.students.list_students(
        **filters, sort=sort, order=order,
        page=parse_page(args.get("page")), per_page=per_page,
    )
    # Echo normalised sort values so the UI reflects what was applied.
    sort = sort if sort in ("name", "id", "marks") else "name"
    order = order if order in ("asc", "desc") else "asc"

    query_args = {
        k: v for k, v in {
            "q": filters["search"], "department": filters["department"],
            "course": filters["course"], "semester": filters["semester"],
            "sort": sort, "order": order, "per_page": per_page,
        }.items() if v not in ("", None)
    }
    return render_template(
        "students/list.html",
        result=result,
        filters=filters,
        sort=sort,
        order=order,
        per_page=per_page,
        per_page_choices=PER_PAGE_CHOICES,
        query_args=query_args,
        has_filters=any(filters.values()),
        options=services.students.filter_options(),
    )


@bp.route("/new", methods=["GET", "POST"])
def create():
    services = get_services()
    if request.method == "GET":
        form = {name: "" for name in STUDENT_FIELDS}
        form["admission_date"] = date.today().isoformat()
        return render_template("students/form.html", mode="create", form=form, errors={}, **_form_context())

    form = _form_values()
    try:
        student = services.students.create(form)
    except ValidationError as exc:
        return render_template("students/form.html", mode="create", form=form,
                               errors=exc.errors, **_form_context()), 400
    except DuplicateStudentError:
        errors = {"student_id": "A student with this ID already exists. Choose a different ID."}
        return render_template("students/form.html", mode="create", form=form,
                               errors=errors, **_form_context()), 409

    flash(f"Student {student['full_name']} was added.", "success")
    return redirect(url_for("students.detail", student_id=student["student_id"]))


@bp.get("/<student_id>")
def detail(student_id):
    student = get_services().students.get(student_id)
    return render_template("students/detail.html", student=student)


@bp.route("/<student_id>/edit", methods=["GET", "POST"])
def edit(student_id):
    services = get_services()
    student = services.students.get(student_id)

    if request.method == "GET":
        form = {k: ("" if v is None else v) for k, v in student.items()}
        return render_template("students/form.html", mode="edit", student=student,
                               form=form, errors={}, **_form_context())

    form = _form_values()
    form["student_id"] = student["student_id"]
    try:
        updated = services.students.update(student["student_id"], form)
    except ValidationError as exc:
        return render_template("students/form.html", mode="edit", student=student,
                               form=form, errors=exc.errors, **_form_context()), 400

    flash(f"Changes to {updated['full_name']} were saved.", "success")
    return redirect(url_for("students.detail", student_id=updated["student_id"]))


@bp.post("/<student_id>/delete")
def delete(student_id):
    services = get_services()
    student = services.students.get(student_id)
    services.students.delete(student["student_id"])
    flash(f"Student {student['full_name']} ({student['student_id']}) was deleted.", "success")
    return redirect(url_for("students.list_students"))
