"""DQ pipeline: validate Bronze frames → Silver-ready valid rows + quarantine + report."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd

from data_quality.rules.runner import (
    RuleResult,
    check_ai4i,
    check_cmapss,
    check_mfg004,
    dq_score,
)
from data_quality.schemas.schemas import Ai4iSchema, CmapssSchema, Mfg004Schema
from ingestion.paths import BRONZE_DIR, QUARANTINE_DIR, ensure_dirs, new_batch_id
from ingestion.pipelines import bronze

CHECKERS = {
    "ai4i_2020": (check_ai4i, Ai4iSchema),
    "cmapss_fd001": (check_cmapss, CmapssSchema),
    "mfg004_quality": (check_mfg004, Mfg004Schema),
}


def _load_bronze(table: str) -> pd.DataFrame:
    path = BRONZE_DIR / f"{table}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Bronze table missing: {path}")
    return pd.read_parquet(path)


def _schema_fail_mask(df: pd.DataFrame, schema) -> pd.Series:
    """Boolean mask: True = row passes schema (lazy validation)."""
    try:
        schema.validate(df, lazy=True)
        return pd.Series(True, index=df.index)
    except Exception:
        # row-level: validate column-by-column where possible
        ok = pd.Series(True, index=df.index)
        for col, column_schema in schema.columns.items():
            if col not in df.columns:
                continue
            series = df[col]
            try:
                col_ok = column_schema.validate(series, lazy=True) is not None
                if not col_ok:
                    ok &= False
            except Exception:
                # coerce failures → row invalid
                dtype_ok = True
                try:
                    column_schema.get_backend(series).validate(series)
                except Exception:
                    dtype_ok = False
                ok &= pd.Series(dtype_ok, index=df.index)
        return ok


def run_dq(bronze_tables: list[str] | None = None) -> dict:
    """Run all DQ checks. Writes quarantine parquets + JSON report.

    Returns report dict.
    """
    ensure_dirs()
    bronze.ensure_dirs() if hasattr(bronze, "ensure_dirs") else ensure_dirs()
    tables = bronze_tables or list(CHECKERS)
    batch_id = new_batch_id()
    now = datetime.now(timezone.utc).isoformat()

    report: dict = {
        "batch_id": batch_id,
        "run_timestamp": now,
        "tables": {},
        "overall_dq_score": 0.0,
    }
    all_results: list[RuleResult] = []

    for table in tables:
        check_fn, schema = CHECKERS[table]
        df = _load_bronze(table)
        results = check_fn(df)
        all_results.extend(results)

        # schema validation → invalid rows to quarantine
        schema_ok = _schema_fail_mask(df, schema)
        # Row-level quarantine: schema failures (v0). Full-frame consistency
        # rules stay at report level.
        invalid_mask = ~schema_ok
        n_invalid = int(invalid_mask.sum())

        if n_invalid > 0:
            q_path = QUARANTINE_DIR / f"{table}_{batch_id}.parquet"
            df.loc[invalid_mask].to_parquet(q_path, index=False)
            quarantine_file = str(q_path.name)
        else:
            quarantine_file = None

        table_score = dq_score([r for r in results if r.severity == "error"])
        report["tables"][table] = {
            "rows": len(df),
            "schema_valid_rows": int(schema_ok.sum()),
            "quarantined_rows": n_invalid,
            "quarantine_file": quarantine_file,
            "dq_score_error_rules": round(table_score, 4),
            "rules": [asdict(r) for r in results],
        }

    report["overall_dq_score"] = round(
        dq_score([r for r in all_results if r.severity == "error"]), 4
    )
    report["rules_total"] = len(all_results)
    report["rules_passed"] = sum(1 for r in all_results if r.passed)
    report["rules_failed"] = sum(1 for r in all_results if not r.passed)

    out = QUARANTINE_DIR / f"dq_report_{batch_id}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report_path"] = str(out)
    return report


if __name__ == "__main__":
    rep = run_dq()
    print(f"DQ Score: {rep['overall_dq_score']}")
    print(f"Rules: {rep['rules_passed']}/{rep['rules_total']} passed")
    for t, info in rep["tables"].items():
        print(
            f"  {t}: rows={info['rows']} "
            f"quarantined={info['quarantined_rows']} "
            f"score={info['dq_score_error_rules']}"
        )
    print(f"Report: {rep['report_path']}")
