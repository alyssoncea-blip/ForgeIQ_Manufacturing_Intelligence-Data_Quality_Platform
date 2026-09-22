"""Phase 5: Anomaly detection tests."""
from __future__ import annotations

import numpy as np
import pytest

from anomaly_detection.iforest import run, score_ai4i, score_cmapss
from ingestion.paths import SILVER_DIR
from ingestion.pipelines import silver


@pytest.fixture(scope="module")
def anomalies():
    if not (SILVER_DIR / "fact_sensor_reading_ai4i.parquet").exists():
        silver.run()
    return run()


def test_two_anomaly_tables(anomalies):
    assert set(anomalies) == {"fact_anomaly_ai4i", "fact_anomaly_cmapss"}


def test_row_counts(anomalies):
    assert len(anomalies["fact_anomaly_ai4i"]) == 10000
    assert len(anomalies["fact_anomaly_cmapss"]) == 20631


def test_score_columns(anomalies):
    for df in anomalies.values():
        assert {"anomaly_score", "is_anomaly", "model", "model_version"} <= set(df.columns)
        assert df["is_anomaly"].isin([0, 1]).all()
        assert df["anomaly_score"].notna().all()
        assert df["model"].str.startswith("iforest_").all()


def test_anomaly_rate_near_contamination(anomalies):
    for name, df in anomalies.items():
        rate = df["is_anomaly"].mean()
        assert 0.01 < rate < 0.10, f"{name} rate={rate}"


def test_anomaly_score_lower_for_anomalies(anomalies):
    for name, df in anomalies.items():
        a = df.loc[df["is_anomaly"] == 1, "anomaly_score"]
        n = df.loc[df["is_anomaly"] == 0, "anomaly_score"]
        assert a.median() < n.median(), name


def test_ai4i_scores_write():
    df = score_ai4i()
    assert len(df) == 10000
    assert "machine_id" in df.columns


def test_cmapss_scores_write():
    df = score_cmapss()
    assert len(df) == 20631
    assert "rul" in df.columns


def test_files_written(anomalies):
    for name in anomalies:
        path = SILVER_DIR / f"{name}.parquet"
        assert path.exists() and path.stat().st_size > 0


def test_deterministic_seed():
    """Same data → same anomaly flags (seeded model)."""
    a1 = score_ai4i()
    a2 = score_ai4i()
    assert (a1["is_anomaly"].to_numpy() == a2["is_anomaly"].to_numpy()).all()
    np.testing.assert_array_equal(
        a1["anomaly_score"].to_numpy(), a2["anomaly_score"].to_numpy()
    )
