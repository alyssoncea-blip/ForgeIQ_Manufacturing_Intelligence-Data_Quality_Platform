"""Phase 2: Bronze Parquet pipeline tests."""
from __future__ import annotations

import pandas as pd
import pytest

from ingestion.paths import BRONZE_DIR, ensure_dirs
from ingestion.pipelines import bronze


@pytest.fixture(scope="module")
def bronze_paths():
    return bronze.run()


def test_bronze_creates_three_tables(bronze_paths):
    assert set(bronze_paths) == {"ai4i_2020", "cmapss_fd001", "mfg004_quality"}
    for p in bronze_paths.values():
        assert p.exists()
        assert p.suffix == ".parquet"
        assert p.stat().st_size > 0


def test_bronze_metadata_columns(bronze_paths):
    for p in bronze_paths.values():
        df = pd.read_parquet(p)
        for col in ("source", "batch_id", "ingestion_timestamp"):
            assert col in df.columns, f"{p.name} missing {col}"
            assert df[col].notna().all()


def test_bronze_row_counts(bronze_paths):
    counts = {name: len(pd.read_parquet(p)) for name, p in bronze_paths.items()}
    assert counts["ai4i_2020"] == 10000
    assert counts["cmapss_fd001"] == 20631
    assert counts["mfg004_quality"] == 3000


def test_bronze_idempotent_overwrite(bronze_paths):
    p = bronze_paths["ai4i_2020"]
    first = p.stat().st_mtime
    bronze.run()
    assert p.stat().st_mtime >= first
    assert len(pd.read_parquet(p)) == 10000


def test_dirs_exist():
    ensure_dirs()
    assert BRONZE_DIR.is_dir()
