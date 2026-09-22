"""DQ rule catalog v0 — versioned, dimension-tagged rules."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    id: str
    version: str
    dimension: str  # completeness | validity | uniqueness | consistency | freshness | referential
    severity: str  # error | warn
    description: str
    applies_to: str  # source name or table


RULES: list[Rule] = field(default_factory=list)  # placeholder overwritten below

RULES = [
    # --- AI4I validity / completeness ---
    Rule("AI4I-COMP-001", "1.0", "completeness", "error",
         "udi, product_id, timestamps columns non-null", "ai4i_2020"),
    Rule("AI4I-VAL-001", "1.0", "validity", "error",
         "air_temperature_k between 250 and 350", "ai4i_2020"),
    Rule("AI4I-VAL-002", "1.0", "validity", "error",
         "process_temperature_k between 250 and 400", "ai4i_2020"),
    Rule("AI4I-VAL-003", "1.0", "validity", "error",
         "rotational_speed_rpm >= 0", "ai4i_2020"),
    Rule("AI4I-VAL-004", "1.0", "validity", "error",
         "torque_nm >= 0", "ai4i_2020"),
    Rule("AI4I-VAL-005", "1.0", "validity", "error",
         "tool_wear_min >= 0", "ai4i_2020"),
    Rule("AI4I-UNI-001", "1.0", "uniqueness", "error",
         "udi unique", "ai4i_2020"),
    Rule("AI4I-CONS-001", "1.0", "consistency", "warn",
         "machine_failure == 1 implies at least one failure_* flag == 1 "
         "(known: ~9 source rows violate this — DQ demo finding)", "ai4i_2020"),

    # --- CMAPSS ---
    Rule("CMAPSS-COMP-001", "1.0", "completeness", "error",
         "unit_id, cycle non-null", "cmapss_fd001"),
    Rule("CMAPSS-VAL-001", "1.0", "validity", "error",
         "cycle >= 1", "cmapss_fd001"),
    Rule("CMAPSS-VAL-002", "1.0", "validity", "error",
         "physical_fan_speed_rpm > 0", "cmapss_fd001"),
    Rule("CMAPSS-UNI-001", "1.0", "uniqueness", "error",
         "(unit_id, cycle) unique", "cmapss_fd001"),
    Rule("CMAPSS-CONS-001", "1.0", "consistency", "error",
         "rul >= 0", "cmapss_fd001"),

    # --- MFG-004 ---
    Rule("MFG-COMP-001", "1.0", "completeness", "error",
         "inspection_id, inspection_date, disposition non-null", "mfg004_quality"),
    Rule("MFG-VAL-001", "1.0", "validity", "error",
         "units_accepted + units_rejected == units_inspected", "mfg004_quality"),
    Rule("MFG-VAL-002", "1.0", "validity", "error",
         "units_inspected >= 0 and defects_found_total >= 0", "mfg004_quality"),
    Rule("MFG-UNI-001", "1.0", "uniqueness", "error",
         "inspection_id unique", "mfg004_quality"),
    Rule("MFG-CONS-001", "1.0", "consistency", "warn",
         "FPY (accepted/inspected) between 0 and 1", "mfg004_quality"),
    Rule("MFG-FRESH-001", "1.0", "freshness", "warn",
         "inspection_date not in future relative to max(date) + 1 day", "mfg004_quality"),
]

RULE_INDEX = {r.id: r for r in RULES}
