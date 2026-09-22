"""Shared paths and ingestion metadata helpers."""
from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
QUARANTINE_DIR = DATA_DIR / "quarantine"


def ensure_dirs() -> None:
    for d in (RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, QUARANTINE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def new_batch_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def ingestion_metadata(source: str, batch_id: str) -> dict:
    return {
        "source": source,
        "batch_id": batch_id,
        "ingestion_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
