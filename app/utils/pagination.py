"""Small pagination helpers."""
import math


def parse_page(value, default=1):
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return default


def paginate(items, page, per_page):
    """Return one page of items plus the metadata templates need."""
    total = len(items)
    pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), pages)
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "total": total,
        "has_prev": page > 1,
        "has_next": page < pages,
        "first": start + 1 if total else 0,
        "last": min(start + per_page, total),
    }
