"""Phase 6: dashboard smoke tests (layout + pages)."""
from __future__ import annotations

import pytest

from analytics.gold import gold_tables
from dashboard.app import PAGES, app, _latest_report


@pytest.fixture(scope="module")
def gold():
    from ingestion.pipelines import bronze, silver

    from anomaly_detection.iforest import run as anomaly_run

    if not (bronze.BRONZE_DIR / "ai4i_2020.parquet").exists():
        bronze.run()
    silver.run()
    anomaly_run()
    return gold_tables()


def test_app_title():
    assert app.title == "ForgeIQ"


def test_pages_registered():
    assert set(PAGES) == {"overview", "quality", "health", "dq"}


def test_overview_page_renders(gold):
    node = PAGES["overview"]()
    assert node is not None


def test_quality_page_renders(gold):
    node = PAGES["quality"]()
    assert node is not None


def test_health_page_renders(gold):
    node = PAGES["health"]()
    assert node is not None


def test_dq_page_renders(gold):
    report = _latest_report()
    if report is None:
        from data_quality.pipeline import run_dq

        run_dq()
    node = PAGES["dq"]()
    assert node is not None


def test_kpi_summary_has_required_keys(gold):
    kpis = set(gold["kpi_summary"]["kpi"])
    for key in ("first_pass_yield", "defect_rate", "machine_failures_ai4i"):
        assert key in kpis
