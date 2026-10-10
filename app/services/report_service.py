"""Statistics and rankings, always computed from the stored records."""

BANDS = (
    ("Below 40", 0, 40),
    ("40-49", 40, 50),
    ("50-59", 50, 60),
    ("60-69", 60, 70),
    ("70-79", 70, 80),
    ("80-89", 80, 90),
    ("90-100", 90, 101),
)


def _marks(students):
    return [s["marks"] for s in students if s.get("marks") is not None]


def stats_for(students):
    """Count, graded count, average, highest and lowest. Missing marks are ignored."""
    marks = _marks(students)
    return {
        "count": len(students),
        "graded": len(marks),
        "average": round(sum(marks) / len(marks), 2) if marks else None,
        "highest": max(marks) if marks else None,
        "lowest": min(marks) if marks else None,
    }


def _by_name(students):
    return sorted(students, key=lambda s: (s["full_name"].casefold(), s["student_id"]))


def _group(students, key):
    groups = {}
    for s in students:
        label = s.get(key)
        if label in (None, ""):
            continue
        groups.setdefault(str(label).casefold() if isinstance(label, str) else label, (label, []))[1].append(s)
    rows = []
    for label, members in (g for g in groups.values()):
        row = stats_for(members)
        row["name"] = label
        rows.append(row)
    return rows


class ReportService:
    def __init__(self, repository):
        self._repo = repository

    def summary(self):
        students = self._repo.all()
        overall = stats_for(students)
        highest, lowest = overall["highest"], overall["lowest"]

        by_course = sorted(_group(students, "course"), key=lambda r: (-r["count"], str(r["name"]).casefold()))
        by_department = sorted(_group(students, "department"), key=lambda r: (-r["count"], str(r["name"]).casefold()))
        by_semester = sorted(_group(students, "semester"), key=lambda r: r["name"])

        marks = _marks(students)
        bands = [
            {"label": label, "count": sum(1 for m in marks if low <= m < high)}
            for label, low, high in BANDS
        ]

        return {
            **overall,
            "total": overall["count"],
            "ungraded": overall["count"] - overall["graded"],
            "toppers": _by_name([s for s in students if highest is not None and s.get("marks") == highest]),
            "lowest_students": _by_name([s for s in students if lowest is not None and s.get("marks") == lowest]),
            "by_course": by_course,
            "by_department": by_department,
            "by_semester": by_semester,
            "bands": bands,
        }

    def chart_data(self, summary):
        return {
            "course": {"labels": [r["name"] for r in summary["by_course"]],
                       "values": [r["count"] for r in summary["by_course"]]},
            "department": {"labels": [r["name"] for r in summary["by_department"]],
                           "values": [r["count"] for r in summary["by_department"]]},
            "semester": {"labels": [f"Semester {r['name']}" for r in summary["by_semester"]],
                         "values": [r["count"] for r in summary["by_semester"]]},
            "bands": {"labels": [b["label"] for b in summary["bands"]],
                      "values": [b["count"] for b in summary["bands"]]},
        }

    def rankings(self, *, course="", department="", semester=""):
        """Rank students by marks (ties share a rank: 1, 1, 3).

        Students without marks are listed after the ranked ones with rank None.
        """
        students = self._repo.all()
        if course:
            students = [s for s in students if s.get("course", "").casefold() == course.casefold()]
        if department:
            students = [s for s in students if s.get("department", "").casefold() == department.casefold()]
        if semester and str(semester).isdigit():
            students = [s for s in students if s.get("semester") == int(semester)]

        ranked = sorted(
            (s for s in students if s.get("marks") is not None),
            key=lambda s: (-s["marks"], s["full_name"].casefold(), s["student_id"]),
        )
        rows = []
        previous_marks, previous_rank = None, 0
        for position, student in enumerate(ranked, start=1):
            if student["marks"] != previous_marks:
                previous_rank = position
                previous_marks = student["marks"]
            rows.append({"rank": previous_rank, "student": student})
        rows.extend(
            {"rank": None, "student": s}
            for s in _by_name([s for s in students if s.get("marks") is None])
        )
        return {"rows": rows, "stats": stats_for(students)}
