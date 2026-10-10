import pytest

from app.services.report_service import ReportService, stats_for


def test_summary_values_are_calculated_from_data(populated):
    summary = populated.reports.summary()
    assert summary["total"] == 6
    assert summary["graded"] == 5 and summary["ungraded"] == 1
    assert summary["average"] == pytest.approx(77.1)   # (90+80+70+90+55.5) / 5
    assert summary["highest"] == 90
    assert summary["lowest"] == 55.5
    assert [s["student_id"] for s in summary["toppers"]] == ["A101", "A104"]
    assert [s["student_id"] for s in summary["lowest_students"]] == ["A110"]


def test_counts_by_course_department_and_semester(populated):
    summary = populated.reports.summary()
    by_course = {r["name"]: r["count"] for r in summary["by_course"]}
    assert by_course == {"MCA": 2, "BCA": 2, "MBA": 2}
    by_department = {r["name"]: r["count"] for r in summary["by_department"]}
    assert by_department == {"Computer Applications": 4, "Management Studies": 2}
    assert [(r["name"], r["count"]) for r in summary["by_semester"]] == [(1, 2), (2, 2), (3, 2)]


def test_group_averages_ignore_missing_marks(populated):
    summary = populated.reports.summary()
    mba = next(r for r in summary["by_course"] if r["name"] == "MBA")
    assert mba["count"] == 2 and mba["graded"] == 1
    assert mba["average"] == 90 and mba["highest"] == 90
    bca = next(r for r in summary["by_course"] if r["name"] == "BCA")
    assert bca["average"] == pytest.approx(62.75)


def test_marks_bands_cover_all_graded_students(populated):
    bands = {b["label"]: b["count"] for b in populated.reports.summary()["bands"]}
    assert sum(bands.values()) == 5
    assert bands["50-59"] == 1 and bands["70-79"] == 1 and bands["80-89"] == 1 and bands["90-100"] == 2


def test_rankings_share_rank_for_ties_and_list_unranked_last(populated):
    rows = populated.reports.rankings()["rows"]
    summary = [(r["rank"], r["student"]["student_id"]) for r in rows]
    assert summary == [(1, "A101"), (1, "A104"), (3, "A102"), (4, "A103"), (5, "A110"), (None, "A105")]


def test_rankings_filtered_by_course_and_semester(populated):
    result = populated.reports.rankings(course="BCA")
    assert [r["student"]["student_id"] for r in result["rows"]] == ["A103", "A110"]
    assert result["stats"]["average"] == pytest.approx(62.75)

    result = populated.reports.rankings(semester="1")
    assert [(r["rank"], r["student"]["student_id"]) for r in result["rows"]] == [(1, "A101"), (2, "A102")]

    result = populated.reports.rankings(course="MBA", semester="2")
    assert [r["rank"] for r in result["rows"]] == [1, None]


def test_empty_dataset_reports_do_not_fail(services):
    summary = services.reports.summary()
    assert summary["total"] == 0
    assert summary["average"] is None and summary["highest"] is None and summary["lowest"] is None
    assert summary["toppers"] == [] and summary["by_course"] == []
    assert sum(b["count"] for b in summary["bands"]) == 0
    assert services.reports.rankings()["rows"] == []


def test_dataset_without_any_marks(services):
    from tests.helpers import student_payload
    services.students.create(student_payload(marks=""))
    summary = services.reports.summary()
    assert summary["total"] == 1 and summary["graded"] == 0
    assert summary["average"] is None and summary["toppers"] == []


def test_stats_for_helper():
    assert stats_for([]) == {"count": 0, "graded": 0, "average": None, "highest": None, "lowest": None}
    result = stats_for([{"marks": 50}, {"marks": None}, {"marks": 75}])
    assert result["average"] == 62.5 and result["highest"] == 75 and result["lowest"] == 50


def test_chart_data_matches_summary(populated):
    summary = populated.reports.summary()
    chart = populated.reports.chart_data(summary)
    assert dict(zip(chart["course"]["labels"], chart["course"]["values"])) == {"MCA": 2, "BCA": 2, "MBA": 2}
    assert chart["semester"]["labels"] == ["Semester 1", "Semester 2", "Semester 3"]
    assert len(chart["bands"]["values"]) == 7


def test_dashboard_shows_actual_numbers(auth_client, populated):
    body = auth_client.get("/").get_data(as_text=True)
    assert "Total students" in body and ">6<" in body
    assert "77.1" in body
    assert "Alice Kumar" in body
    assert 'id="chart-data"' in body and '"MBA"' in body


def test_dashboard_empty_state(auth_client):
    response = auth_client.get("/")
    assert response.status_code == 200
    assert b"No student records yet" in response.data
    assert b"chart-data" not in response.data


def test_reports_page_and_filters(auth_client, populated):
    body = auth_client.get("/reports/").get_data(as_text=True)
    assert "Toppers" in body and "Alice Kumar" in body and "Dan Roy" in body
    assert "Eve Paul" in body  # unranked students are still listed

    filtered = auth_client.get("/reports/?course=BCA&semester=3").get_data(as_text=True)
    assert "Carol Das" in filtered and "Frank Lee" in filtered
    assert "Rankings and filtered list" in filtered
    assert "2 students in this list" in filtered


def test_reports_page_with_no_matches_and_empty_data(auth_client, populated):
    body = auth_client.get("/reports/?course=Nothing").get_data(as_text=True)
    assert "No students match these filters" in body


def test_reports_page_empty_state(auth_client):
    response = auth_client.get("/reports/")
    assert response.status_code == 200
    assert b"nothing to report yet" in response.data


def test_report_service_reads_live_data(services):
    from tests.helpers import student_payload
    reports = ReportService(services.repository)
    assert reports.summary()["total"] == 0
    services.students.create(student_payload(marks="60"))
    assert reports.summary()["total"] == 1 and reports.summary()["average"] == 60
