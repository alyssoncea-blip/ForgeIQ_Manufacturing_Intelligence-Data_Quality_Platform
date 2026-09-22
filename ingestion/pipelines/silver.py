"""Silver layer: clean, standardize, entity-resolve Bronze → canonical factory model."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from ingestion.paths import (
    BRONZE_DIR,
    SILVER_DIR,
    ensure_dirs,
    ingestion_metadata,
    new_batch_id,
)

# Premissa temporal documentada (docs/data_dictionary.md)
AI4I_T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
AI4I_DELTA = timedelta(minutes=5)
CMAPSS_T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

FAILURE_MODE_COLS = ["failure_twf", "failure_hdf", "failure_pwf", "failure_osf", "failure_rnf"]
FAILURE_MODE_NAMES = {
    "failure_twf": "tool_wear",
    "failure_hdf": "heat_dissipation",
    "failure_pwf": "power",
    "failure_osf": "overstrain",
    "failure_rnf": "random",
}


def _meta_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = df.copy()
    meta = ingestion_metadata(source, new_batch_id())
    for k, v in meta.items():
        if k not in out.columns:
            out[k] = v
    return out


def silver_ai4i(bronze: pd.DataFrame | None = None) -> pd.DataFrame:
    """Canonical sensor/failure events from AI4I.

    - machine_id: deterministic bucket M9xxx from udi (fleet proxy)
    - event_time: ordinal → documented synthetic timeline
    """
    df = bronze if bronze is not None else pd.read_parquet(BRONZE_DIR / "ai4i_2020.parquet")
    out = pd.DataFrame(
        {
            "udi": df["udi"].astype(int),
            "machine_id": df["udi"].map(lambda u: f"M9{int(u) % 50:03d}"),
            "product_id": df["product_id"],
            "product_type": df["product_type"],
            "event_time": [
                AI4I_T0 + AI4I_DELTA * (int(u) - 1) for u in df["udi"]
            ],
            "air_temperature_k": df["air_temperature_k"].astype(float),
            "process_temperature_k": df["process_temperature_k"].astype(float),
            "rotational_speed_rpm": df["rotational_speed_rpm"].astype(float),
            "torque_nm": df["torque_nm"].astype(float),
            "tool_wear_min": df["tool_wear_min"].astype(float),
            "machine_failure": df["machine_failure"].astype(int),
            "failure_modes": [
                "|".join(FAILURE_MODE_NAMES[c] for c in FAILURE_MODE_COLS if row[c] == 1)
                or None
                for _, row in df.iterrows()
            ],
        }
    )
    return _meta_columns(out, "silver_ai4i")


def silver_cmapss(bronze: pd.DataFrame | None = None) -> pd.DataFrame:
    """Canonical fleet time series from CMAPSS FD001.

    - machine_id: M + unit_id padded (M0001..M0100)
    - event_time: cycle → synthetic daily timeline per unit
    """
    df = bronze if bronze is not None else pd.read_parquet(BRONZE_DIR / "cmapss_fd001.parquet")
    sensor_prefixes = (
        "total_", "pressure_", "physical_", "corrected_", "engine_",
        "static_", "ratio_", "bypass_", "burner_", "bleed_",
        "demanded_", "hpt_", "lpt_", "setting_",
    )
    sensor_cols = [c for c in df.columns if c.startswith(sensor_prefixes)]
    out = pd.DataFrame(
        {
            "unit_id": df["unit_id"].astype(int),
            "machine_id": df["unit_id"].map(lambda u: f"M{int(u):04d}"),
            "cycle": df["cycle"].astype(int),
            "event_time": [
                CMAPSS_T0 + timedelta(days=int(c) - 1) for c in df["cycle"]
            ],
            "rul": df["rul"].astype(int),
            "failed": df["failed"].astype(int),
        }
    )
    for col in sensor_cols:
        out[col] = df[col]
    return _meta_columns(out, "silver_cmapss")


def silver_quality(bronze: pd.DataFrame | None = None) -> pd.DataFrame:
    """Canonical quality inspections from MFG-004.

    - machine_id: stable hash of work_order_id → M8xxx
    - line_id: facility_id as line proxy (documented)
    """
    df = bronze if bronze is not None else pd.read_parquet(BRONZE_DIR / "mfg004_quality.parquet")
    wo = df["work_order_id"].astype(str)
    machine_num = wo.map(lambda s: int(abs(hash(s)) % 9000) + 80000)  # placeholder stable-ish
    # Deterministic without PYTHONHASHSEED: use sum of ordinals
    machine_num = wo.map(lambda s: (sum(ord(c) for c in s) % 900) + 8000)

    out = pd.DataFrame(
        {
            "inspection_id": df["inspection_id"],
            "work_order_id": df["work_order_id"],
            "part_number": df["part_number"],
            "product_family": df["product_family"],
            "lot_number": df["lot_number"],
            "line_id": df["facility_id"].astype(str),
            "machine_id": machine_num.map(lambda n: f"M{n}"),
            "event_time": pd.to_datetime(df["inspection_date"], errors="coerce"),
            "inspection_shift": df["inspection_shift"],
            "disposition": df["disposition"],
            "units_inspected": df["units_inspected"].astype(int),
            "units_accepted": df["units_accepted"].astype(int),
            "units_rejected": df["units_rejected"].astype(int),
            "defects_found_total": df["defects_found_total"].astype(int),
            "defect_type_primary": df["defect_type_primary"],
            "defect_severity_class": df["defect_severity_class"],
            "defect_cause_category": df["defect_cause_category"],
            "cpk": df.get("cpk_process_capability_index"),
            "sigma_level": df.get("sigma_level_estimated"),
        }
    )
    return _meta_columns(out, "silver_quality")


def run() -> dict[str, pd.DataFrame]:
    ensure_dirs()
    tables = {
        "fact_sensor_reading_ai4i": silver_ai4i(),
        "fact_sensor_reading_cmapss": silver_cmapss(),
        "fact_quality": silver_quality(),
    }
    for name, df in tables.items():
        path = SILVER_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
    return tables


if __name__ == "__main__":
    for name, df in run().items():
        print(f"{name}: {len(df)} rows, {len(df.columns)} cols")
