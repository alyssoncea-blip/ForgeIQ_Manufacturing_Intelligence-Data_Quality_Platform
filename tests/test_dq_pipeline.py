"""Phase 3: DQ pipeline tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_quality.pipeline import run_dq
from ingestion.paths import BRONZE_DIR, QUARANTINE_DIR
from ingestion.pipelines import bronze


@pytest.fixture(scope="module")
def report():
    if not (BRONZE_DIR / "ai4i_2020.parquet").exists():
        bronze.run()
    return run_dq()


def test_report_structure(report):
    assert "overall_dq_score" in report
    assert 0.0 <= report["overall_dq_score"] <= 1.0
    assert set(report["tables"]) == {"ai4i_2020", "cmapss_fd001", "mfg004_quality"}
    assert report["rules_total"] > 0


def test_error_rules_all_pass(report):
    for table, info in report["tables"].items():
        for rule in info["rules"]:
            if rule["severity"] == "error":
                assert rule["passed"], f"{table} {rule['rule_id']} failed: {rule}"


def test_dq_score_perfect_on_error_rules(report):
    assert report["overall_dq_score"] == 1.0


def test_report_file_written(report):
    path = Path(report["report_path"])
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["batch_id"] == report["batch_id"]


def test_quarantine_dir_exists():
    assert QUARANTINE_DIR.is_dir()


def test_clean_data_no_quarantine_rows(report):
    for info in report["tables"].values():
        assert info["quarantined_rows"] == 0


def test_run_dq_idempotent():
    r1 = run_dq()
    r2 = run_dq()
    assert r1["batch_id"] != r2["batch_id"]
    assert r2["overall_dq_score"] == r1["overall_dq_score"]
