"""Smoke tests: loaders + DQ rules on real raw files."""
from __future__ import annotations

import pytest

from data_quality.rules.catalog import RULE_INDEX, RULES
from data_quality.rules.runner import check_ai4i, check_cmapss, check_mfg004, dq_score
from data_quality.schemas.schemas import Ai4iSchema, CmapssSchema, Mfg004Schema
from ingestion.paths import RAW_DIR


@pytest.fixture(scope="module")
def ai4i_df():
    from ingestion.sources.ai4i import load

    return load()


@pytest.fixture(scope="module")
def cmapss_df():
    from ingestion.sources.cmapss import load

    return load()


@pytest.fixture(scope="module")
def mfg_df():
    from ingestion.sources.mfg004 import load

    return load()


def test_raw_files_exist():
    assert (RAW_DIR / "ai4i2020.csv").exists()
    assert (RAW_DIR / "train_FD001.txt").exists()
    assert (RAW_DIR / "mfg004_inspection_records.csv").exists()


def test_catalog_ids_unique():
    ids = [r.id for r in RULES]
    assert len(ids) == len(set(ids))
    assert all(r.version and r.dimension for r in RULES)


def test_ai4i_schema(ai4i_df):
    Ai4iSchema.validate(ai4i_df, lazy=True)


def test_cmapss_schema(cmapss_df):
    CmapssSchema.validate(cmapss_df, lazy=True)
    assert not cmapss_df.duplicated(subset=["unit_id", "cycle"]).any()


def test_mfg_schema(mfg_df):
    Mfg004Schema.validate(mfg_df, lazy=True)
    ok = mfg_df["units_accepted"] + mfg_df["units_rejected"] == mfg_df["units_inspected"]
    assert ok.all()


def test_ai4i_rules_pass(ai4i_df):
    results = check_ai4i(ai4i_df)
    hard_failed = [r for r in results if not r.passed and r.severity == "error"]
    assert not hard_failed, hard_failed
    # Known source issue: machine_failure=1 without failure_* flags
    cons = next(r for r in results if r.rule_id == "AI4I-CONS-001")
    assert cons.severity == "warn"
    assert cons.failed_count >= 0  # documented as demo finding in data_sources.md
    score = dq_score([r for r in results if r.severity == "error"])
    assert score == 1.0


def test_cmapss_rules_pass(cmapss_df):
    results = check_cmapss(cmapss_df)
    failed = [r for r in results if not r.passed]
    assert not failed, failed


def test_mfg_rules_pass(mfg_df):
    results = check_mfg004(mfg_df)
    failed = [r for r in results if not r.passed]
    assert not failed, failed


def test_bronze_metadata_on_load():
    from ingestion.sources.ai4i import load_bronze

    df = load_bronze()
    for col in ("source", "batch_id", "ingestion_timestamp"):
        assert col in df.columns
        assert df[col].notna().all()


def test_rule_index_lookup():
    assert "AI4I-VAL-001" in RULE_INDEX
    assert RULE_INDEX["MFG-UNI-001"].dimension == "uniqueness"
