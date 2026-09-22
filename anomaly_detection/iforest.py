"""Anomaly detection on Silver sensor streams (IsolationForest).

Phase 5.5 in roadmap (per approved projeto.txt). Outputs scored frames for Gold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ingestion.paths import SILVER_DIR, ensure_dirs

AI4I_FEATURES = [
    "air_temperature_k",
    "process_temperature_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]


def _sensor_features_cmapss(df: pd.DataFrame) -> list[str]:
    exclude = {"unit_id", "machine_id", "cycle", "event_time", "rul", "failed", "source",
               "batch_id", "ingestion_timestamp"}
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]


def _fit_score(
    df: pd.DataFrame, features: list[str], seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    X = df[features].to_numpy(dtype=float)
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X)
    scores = model.decision_function(X)  # lower = more anomalous
    preds = model.predict(X)  # -1 anomaly, 1 inlier
    return scores, preds


def score_ai4i(bronze: pd.DataFrame | None = None) -> pd.DataFrame:
    df = (
        bronze
        if bronze is not None
        else pd.read_parquet(SILVER_DIR / "fact_sensor_reading_ai4i.parquet")
    )
    scores, preds = _fit_score(df, AI4I_FEATURES)
    out = df[
        ["udi", "machine_id", "event_time", "product_type", "machine_failure"]
        + AI4I_FEATURES
    ].copy()
    out["anomaly_score"] = np.round(scores, 6)
    out["is_anomaly"] = (preds == -1).astype(int)
    out["model"] = "iforest_ai4i_v1"
    out["model_version"] = "1.0.0"
    return out


def score_cmapss(bronze: pd.DataFrame | None = None) -> pd.DataFrame:
    df = (
        bronze
        if bronze is not None
        else pd.read_parquet(SILVER_DIR / "fact_sensor_reading_cmapss.parquet")
    )
    features = _sensor_features_cmapss(df)
    scores, preds = _fit_score(df, features)
    out = df[["unit_id", "machine_id", "cycle", "event_time", "rul", "failed"]].copy()
    out["anomaly_score"] = np.round(scores, 6)
    out["is_anomaly"] = (preds == -1).astype(int)
    out["model"] = "iforest_cmapss_v1"
    out["model_version"] = "1.0.0"
    return out


def run() -> dict[str, pd.DataFrame]:
    ensure_dirs()
    tables = {
        "fact_anomaly_ai4i": score_ai4i(),
        "fact_anomaly_cmapss": score_cmapss(),
    }
    for name, df in tables.items():
        path = SILVER_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
    return tables


if __name__ == "__main__":
    for name, df in run().items():
        rate = df["is_anomaly"].mean()
        print(f"{name}: rows={len(df)} anomaly_rate={rate:.3%}")
