"""Gold layer: analytical marts + industrial KPIs from Silver (pandas/DuckDB)."""
from __future__ import annotations

import duckdb
import pandas as pd

from ingestion.paths import GOLD_DIR, SILVER_DIR, ensure_dirs


def _silver(name: str) -> pd.DataFrame:
    return pd.read_parquet(SILVER_DIR / f"{name}.parquet")


def gold_tables() -> dict[str, pd.DataFrame]:
    ensure_dirs()
    ai4i = _silver("fact_sensor_reading_ai4i")
    cmapss = _silver("fact_sensor_reading_cmapss")
    quality = _silver("fact_quality")

    # --- dim_date from quality event_time (dense calendar) ---
    dates = quality["event_time"].dropna().dt.normalize().drop_duplicates()
    dim_date = pd.DataFrame({"date": dates.sort_values()}).reset_index(drop=True)
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["week"] = dim_date["date"].dt.isocalendar().week.astype(int)

    # --- dim_machine: union of machine_ids across sources ---
    machines = pd.concat(
        [
            ai4i[["machine_id"]].drop_duplicates().assign(source="ai4i_2020"),
            cmapss[["machine_id"]].drop_duplicates().assign(source="cmapss_fd001"),
            quality[["machine_id"]].drop_duplicates().assign(source="mfg004_quality"),
        ],
        ignore_index=True,
    )
    # Prefer single row per machine_id (first source wins for attributes)
    dim_machine = (
        machines.groupby("machine_id", as_index=False)
        .agg(sources=("source", lambda s: "|".join(sorted(set(s)))), source=("source", "first"))
    )

    dim_product = (
        quality[["part_number", "product_family"]].drop_duplicates().reset_index(drop=True)
    )
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

    dim_line = pd.DataFrame({"line_id": sorted(quality["line_id"].dropna().unique())})
    dim_line.insert(0, "line_key", range(1, len(dim_line) + 1))

    # --- fact_production (grain: date x line) ---
    q = quality.copy()
    q["date"] = q["event_time"].dt.normalize()
    fact_production = (
        q.groupby(["date", "line_id"], as_index=False)
        .agg(
            units_inspected=("units_inspected", "sum"),
            units_accepted=("units_accepted", "sum"),
            units_rejected=("units_rejected", "sum"),
            defects_found_total=("defects_found_total", "sum"),
            inspections=("inspection_id", "count"),
        )
    )
    fact_production["date_id"] = fact_production["date"].dt.strftime("%Y%m%d").astype(int)
    fact_production["defect_rate"] = (
        fact_production["units_rejected"] / fact_production["units_inspected"]
    ).round(6)
    fact_production["first_pass_yield"] = (
        fact_production["units_accepted"] / fact_production["units_inspected"]
    ).round(6)

    # --- fact_quality (inspection grain) ---
    fact_quality = q.merge(dim_product, on=["part_number", "product_family"], how="left")
    fact_quality = fact_quality.merge(dim_line, on="line_id", how="left")
    fact_quality["date_id"] = fact_quality["event_time"].dt.strftime("%Y%m%d").astype(int)

    # --- fact_maintenance: failures + derived downtime ---
    # Premissa: repair_window = 8h per failure event (documented estimated downtime)
    REPAIR_WINDOW_H = 8.0

    ai4i_fail = ai4i[ai4i["machine_failure"] == 1][
        ["machine_id", "event_time", "failure_modes"]
    ].copy()
    ai4i_fail["event_type"] = "ai4i_failure"
    ai4i_fail["downtime_hours_estimated"] = REPAIR_WINDOW_H

    cmapss_fail = cmapss[cmapss["failed"] == 1][
        ["machine_id", "event_time", "cycle", "rul"]
    ].copy()
    cmapss_fail["failure_modes"] = "run_to_failure"
    cmapss_fail["event_type"] = "cmapss_eol"
    cmapss_fail["downtime_hours_estimated"] = REPAIR_WINDOW_H

    fact_maintenance = pd.concat(
        [
            ai4i_fail[["machine_id", "event_time", "event_type", "failure_modes",
                       "downtime_hours_estimated"]],
            cmapss_fail[["machine_id", "event_time", "event_type", "failure_modes",
                         "downtime_hours_estimated"]],
        ],
        ignore_index=True,
    )

    # --- KPI summary (factory overview grain) ---
    total_inspected = int(quality["units_inspected"].sum())
    total_accepted = int(quality["units_accepted"].sum())
    total_rejected = int(quality["units_rejected"].sum())
    scrap_n = int((quality["disposition"] == "scrap").sum())
    rework_n = int((quality["disposition"] == "rework").sum())
    n_insp = len(quality)

    mtbf_cycles = float(cmapss.groupby("unit_id")["cycle"].max().mean())

    kpi_summary = pd.DataFrame(
        [
            {
                "kpi": "total_production_units",
                "value": total_inspected,
                "status": "ok",
            },
            {
                "kpi": "defect_rate",
                "value": round(total_rejected / total_inspected, 6),
                "status": "ok",
            },
            {
                "kpi": "first_pass_yield",
                "value": round(total_accepted / total_inspected, 6),
                "status": "ok",
            },
            {
                "kpi": "scrap_rate",
                "value": round(scrap_n / n_insp, 6),
                "status": "ok",
            },
            {
                "kpi": "rework_rate",
                "value": round(rework_n / n_insp, 6),
                "status": "ok",
            },
            {
                "kpi": "total_defects",
                "value": int(quality["defects_found_total"].sum()),
                "status": "ok",
            },
            {
                "kpi": "machine_failures_ai4i",
                "value": int(ai4i["machine_failure"].sum()),
                "status": "ok",
            },
            {
                "kpi": "active_machines_cmapss",
                "value": int(cmapss["machine_id"].nunique()),
                "status": "ok",
            },
            {
                "kpi": "downtime_hours_estimated",
                "value": float(fact_maintenance["downtime_hours_estimated"].sum()),
                "status": "estimated",
            },
            {
                "kpi": "mtbf_cycles_cmapss",
                "value": round(mtbf_cycles, 2),
                "status": "ok",
            },
        ]
    )

    # --- fact_anomaly (if anomaly outputs exist) ---
    anomaly_frames = []
    for src, path in [
        ("ai4i", SILVER_DIR / "fact_anomaly_ai4i.parquet"),
        ("cmapss", SILVER_DIR / "fact_anomaly_cmapss.parquet"),
    ]:
        if path.exists():
            adf = pd.read_parquet(path)
            adf["source"] = src
            anomaly_frames.append(adf)

    if anomaly_frames:
        fact_anomaly = pd.concat(anomaly_frames, ignore_index=True, sort=False)
        rate = fact_anomaly["is_anomaly"].mean()
        kpi_summary = pd.concat(
            [
                kpi_summary,
                pd.DataFrame(
                    [
                        {
                            "kpi": "anomaly_rate",
                            "value": round(float(rate), 6),
                            "status": "ok",
                        },
                        {
                            "kpi": "anomaly_events",
                            "value": int(fact_anomaly["is_anomaly"].sum()),
                            "status": "ok",
                        },
                    ]
                ),
            ],
            ignore_index=True,
        )
    else:
        fact_anomaly = pd.DataFrame(
            columns=["machine_id", "event_time", "anomaly_score", "is_anomaly", "source"]
        )

    return {
        "dim_date": dim_date,
        "dim_machine": dim_machine,
        "dim_product": dim_product,
        "dim_line": dim_line,
        "fact_production": fact_production,
        "fact_quality": fact_quality,
        "fact_maintenance": fact_maintenance,
        "fact_anomaly": fact_anomaly,
        "kpi_summary": kpi_summary,
    }


def write_gold() -> dict:
    tables = gold_tables()
    paths = {}
    for name, df in tables.items():
        path = GOLD_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
        paths[name] = path
    # DuckDB convenience views
    con = duckdb.connect(str(GOLD_DIR / "forgeiq.duckdb"))
    for name, df in tables.items():
        con.register(f"_{name}", df)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _{name}")
    con.close()
    return paths


if __name__ == "__main__":
    for name, p in write_gold().items():
        print(f"{name}: {p.name}")
