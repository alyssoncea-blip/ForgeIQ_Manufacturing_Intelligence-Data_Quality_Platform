"""Phase 6: dashboard smoke tests (layout + pages)."""
from __future__ import annotations

import pytest

from analytics.gold import gold_tables, write_gold
from dashboard.app import PAGES, _latest_report, app
from ingestion.pipelines import bronze, silver


@pytest.fixture(scope="module")
def gold():
    from anomaly_detection.iforest import run as anomaly_run

    if not (bronze.BRONZE_DIR / "ai4i_2020.parquet").exists():
        bronze.run()
    if not (silver.SILVER_DIR / "fact_quality.parquet").exists():
        silver.run()
    anomaly_run()
    write_gold()
    result = gold_tables()
    assert result is not None, "gold_tables() must return a dict"
    return result


def test_app_title():
    assert app.title == "ForgeIQ"


def test_pages_registered():
    assert set(PAGES) == {"overview", "quality", "health", "dq"}


def test_overview_page_renders(gold):
    assert PAGES["overview"]() is not None


def test_quality_page_renders(gold):
    assert PAGES["quality"]() is not None


def test_health_page_renders(gold):
    assert PAGES["health"]() is not None


def test_dq_page_renders(gold):
    if _latest_report() is None:
        from data_quality.pipeline import run_dq

        run_dq()
    assert PAGES["dq"]() is not None


def test_kpi_summary_has_required_keys(gold):
    kpis = set(gold["kpi_summary"]["kpi"])
    for key in ("first_pass_yield", "defect_rate", "machine_failures_ai4i"):
        assert key in kpis
