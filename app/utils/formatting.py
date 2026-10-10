"""Template filters for dates and marks."""
from datetime import datetime


def format_date(value):
    if not value:
        return "-"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except (TypeError, ValueError):
        return str(value)


def format_timestamp(value):
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M UTC")
    except (TypeError, ValueError):
        return str(value)


def format_marks(value):
    if value is None:
        return "Not recorded"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def marks_input(value):
    return "" if value is None else f"{value:.2f}".rstrip("0").rstrip(".")
