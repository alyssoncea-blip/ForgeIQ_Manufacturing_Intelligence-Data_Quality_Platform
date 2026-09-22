"""Bronze ingestion pipeline: load all sources → Parquet with metadata."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingestion.paths import BRONZE_DIR, ensure_dirs, ingestion_metadata, new_batch_id
from ingestion.sources import ai4i, cmapss, mfg004


def _write_bronze(df: pd.DataFrame, table: str, source: str) -> Path:
    ensure_dirs()
    batch_id = new_batch_id()
    meta = ingestion_metadata(source, batch_id)
    out = df.copy()
    for k, v in meta.items():
        out[k] = v
    path = BRONZE_DIR / f"{table}.parquet"
    out.to_parquet(path, index=False)
    return path


def run() -> dict[str, Path]:
    """Ingest all Phase-1 sources into Bronze Parquet. Returns table → path."""
    paths: dict[str, Path] = {}

    df_ai4i = ai4i.load()
    paths["ai4i_2020"] = _write_bronze(df_ai4i, "ai4i_2020", ai4i.SOURCE_NAME)

    df_cmapss = cmapss.load()
    paths["cmapss_fd001"] = _write_bronze(df_cmapss, "cmapss_fd001", cmapss.SOURCE_NAME)

    df_mfg = mfg004.load()
    paths["mfg004_quality"] = _write_bronze(df_mfg, "mfg004_quality", mfg004.SOURCE_NAME)

    return paths


if __name__ == "__main__":
    for name, p in run().items():
        size_kb = p.stat().st_size / 1024
        print(f"{name}: {p.name} ({size_kb:.1f} KB)")
