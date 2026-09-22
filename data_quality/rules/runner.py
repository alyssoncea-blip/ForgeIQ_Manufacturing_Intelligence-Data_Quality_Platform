"""Run DQ checks against Bronze frames; return per-rule results."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class RuleResult:
    rule_id: str
    passed: bool
    failed_count: int
    total: int
    severity: str

    @property
    def failed_rate(self) -> float:
        return self.failed_count / self.total if self.total else 0.0


def _result(rule_id: str, severity: str, mask_ok: pd.Series) -> RuleResult:
    total = len(mask_ok)
    failed = int((~mask_ok).sum())
    return RuleResult(rule_id, failed == 0, failed, total, severity)


def check_ai4i(df: pd.DataFrame) -> list[RuleResult]:
    results = [
        _result("AI4I-COMP-001", "error",
                df[["udi", "product_id"]].notna().all(axis=1)),
        _result("AI4I-VAL-001", "error",
                df["air_temperature_k"].between(250, 350)),
        _result("AI4I-VAL-002", "error",
                df["process_temperature_k"].between(250, 400)),
        _result("AI4I-VAL-003", "error", df["rotational_speed_rpm"] >= 0),
        _result("AI4I-VAL-004", "error", df["torque_nm"] >= 0),
        _result("AI4I-VAL-005", "error", df["tool_wear_min"] >= 0),
        _result("AI4I-UNI-001", "error", ~df["udi"].duplicated(keep=False) | df["udi"].notna()),
    ]
    # uniqueness: proper check
    results[-1] = _result("AI4I-UNI-001", "error", ~df["udi"].duplicated(keep=False))
    fail_cols = ["failure_twf", "failure_hdf", "failure_pwf", "failure_osf", "failure_rnf"]
    fail_flags = df[fail_cols].sum(axis=1)
    consistency = (df["machine_failure"] == 0) | (fail_flags >= 1)
    results.append(_result("AI4I-CONS-001", "warn", consistency))
    return results


def check_cmapss(df: pd.DataFrame) -> list[RuleResult]:
    results = [
        _result("CMAPSS-COMP-001", "error", df[["unit_id", "cycle"]].notna().all(axis=1)),
        _result("CMAPSS-VAL-001", "error", df["cycle"] >= 1),
        _result("CMAPSS-VAL-002", "error", df["physical_fan_speed_rpm"] > 0),
        _result("CMAPSS-UNI-001", "error", ~df.duplicated(subset=["unit_id", "cycle"], keep=False)),
        _result("CMAPSS-CONS-001", "error", df["rul"] >= 0),
    ]
    return results


def check_mfg004(df: pd.DataFrame) -> list[RuleResult]:
    required = df[["inspection_id", "inspection_date", "disposition"]].notna().all(axis=1)
    results = [
        _result("MFG-COMP-001", "error", required),
        _result("MFG-VAL-001", "error",
                df["units_accepted"] + df["units_rejected"] == df["units_inspected"]),
        _result("MFG-VAL-002", "error",
                (df["units_inspected"] >= 0) & (df["defects_found_total"] >= 0)),
        _result("MFG-UNI-001", "error", ~df["inspection_id"].duplicated(keep=False)),
    ]
    inspected = df["units_inspected"].replace(0, pd.NA)
    fpy = df["units_accepted"] / inspected
    results.append(_result("MFG-CONS-001", "warn", fpy.between(0, 1) | fpy.isna()))
    dates = pd.to_datetime(df["inspection_date"], errors="coerce")
    results.append(_result(
        "MFG-FRESH-001", "warn",
        dates.isna() | (dates <= dates.max() + pd.Timedelta(days=1)),
    ))
    return results


def dq_score(results: list[RuleResult]) -> float:
    """Simple composite: share of passed rules (v0 weights = equal)."""
    if not results:
        return 0.0
    return sum(1.0 for r in results if r.passed) / len(results)
