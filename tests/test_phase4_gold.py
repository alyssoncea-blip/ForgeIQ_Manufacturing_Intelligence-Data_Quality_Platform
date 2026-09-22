"""Phase 4: Silver entity resolution + Gold KPIs + soft contracts."""
from __future__ import annotations

import pytest

from analytics.gold import gold_tables, write_gold
from ingestion.paths import GOLD_DIR, SILVER_DIR
from ingestion.pipelines import bronze, silver


@pytest.fixture(scope="module")
def silver_tables():
    if not (SILVER_DIR / "fact_quality.parquet").exists():
        bronze.run()
    return silver.run()


@pytest.fixture(scope="module")
def gold():
    return gold_tables()


def test_silver_three_tables(silver_tables):
    assert set(silver_tables) == {
        "fact_sensor_reading_ai4i",
        "fact_sensor_reading_cmapss",
        "fact_quality",
    }
    for df in silver_tables.values():
        assert "machine_id" in df.columns
        assert "event_time" in df.columns
        assert "source" in df.columns


def test_silver_machine_id_format(silver_tables):
    for name, df in silver_tables.items():
        assert df["machine_id"].str.match(r"^M\d+$").all(), name
        assert df["machine_id"].notna().all()


def test_silver_event_time_monotonic_ai4i(silver_tables):
    df = silver_tables["fact_sensor_reading_ai4i"]
    assert df["event_time"].is_monotonic_increasing


def test_silver_cmapss_rul_non_negative(silver_tables):
    df = silver_tables["fact_sensor_reading_cmapss"]
    assert (df["rul"] >= 0).all()


def test_silver_quality_fpy_bounds(silver_tables):
    df = silver_tables["fact_quality"]
    ratio = df["units_accepted"] / df["units_inspected"]
    assert ratio.between(0, 1).all()


def test_gold_tables_present(gold):
    expected = {
        "dim_date",
        "dim_machine",
        "dim_product",
        "dim_line",
        "fact_production",
        "fact_quality",
        "fact_maintenance",
        "kpi_summary",
    }
    assert set(gold) == expected


def test_gold_fact_production_consistency(gold):
    fp = gold["fact_production"]
    assert (fp["units_accepted"] + fp["units_rejected"] == fp["units_inspected"]).all()
    assert fp["first_pass_yield"].between(0, 1).all()


def test_gold_kpi_summary_values(gold):
    kpis = {r.kpi: r for r in gold["kpi_summary"].itertuples()}
    assert 0 < kpis["first_pass_yield"].value < 1
    assert 0 < kpis["defect_rate"].value < 1
    assert kpis["active_machines_cmapss"].value == 100
    assert kpis["machine_failures_ai4i"].value == 339
    assert kpis["downtime_hours_estimated"].status == "estimated"


def test_gold_fact_maintenance_downtime_premise(gold):
    fm = gold["fact_maintenance"]
    assert (fm["downtime_hours_estimated"] == 8.0).all()
    assert fm["machine_id"].notna().all()


def test_contract_machine_id_referential(gold):
    """Soft contract: fact machine_ids exist in dim_machine."""
    dim_ids = set(gold["dim_machine"]["machine_id"])
    for fact in ("fact_quality", "fact_maintenance", "fact_production"):
        if "machine_id" in gold[fact].columns:
            missing = set(gold[fact]["machine_id"]) - dim_ids
            assert not missing, f"{fact} orphan machine_ids: {list(missing)[:5]}"


def test_contract_date_ids(gold):
    dim_dates = set(gold["dim_date"]["date_id"])
    assert set(gold["fact_production"]["date_id"]).issubset(dim_dates)
    assert set(gold["fact_quality"]["date_id"]).issubset(dim_dates)


def test_write_gold_files():
    paths = write_gold()
    assert (GOLD_DIR / "forgeiq.duckdb").exists()
    for p in paths.values():
        assert p.exists() and p.stat().st_size > 0


def test_gold_silver_row_counts_consistent(silver_tables, gold):
    assert len(gold["fact_quality"]) == len(silver_tables["fact_quality"])
    assert (
        len(gold["fact_maintenance"])
        == int(silver_tables["fact_sensor_reading_ai4i"]["machine_failure"].sum())
        + int(silver_tables["fact_sensor_reading_cmapss"]["failed"].sum())
    )
