from flask import Blueprint, render_template, request

from app.services import get_services
from app.utils.pagination import paginate, parse_page

bp = Blueprint("reports", __name__, url_prefix="/reports")

RANKING_PAGE_SIZE = 25


@bp.get("/")
def index():
    services = get_services()
    filters = {
        "course": request.args.get("course", "").strip(),
        "department": request.args.get("department", "").strip(),
        "semester": request.args.get("semester", "").strip(),
    }
    ranking = services.reports.rankings(**filters)
    page = paginate(ranking["rows"], parse_page(request.args.get("page")), RANKING_PAGE_SIZE)
    query_args = {k: v for k, v in filters.items() if v}

    return render_template(
        "reports/index.html",
        summary=services.reports.summary(),
        filters=filters,
        ranking_stats=ranking["stats"],
        page=page,
        query_args=query_args,
        has_filters=bool(query_args),
        options=services.students.filter_options(),
    )
