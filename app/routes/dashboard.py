from flask import Blueprint, render_template

from app.services import get_services

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    services = get_services()
    summary = services.reports.summary()
    return render_template(
        "dashboard.html",
        summary=summary,
        recent=services.students.recent(8),
        chart_data=services.reports.chart_data(summary),
    )
