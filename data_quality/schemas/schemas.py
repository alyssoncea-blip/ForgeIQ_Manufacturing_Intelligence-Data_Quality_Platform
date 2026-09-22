"""Pandera schemas for Bronze/Silver validation (v0)."""
from __future__ import annotations

from pandera import Check, Column, DataFrameSchema

Ai4iSchema = DataFrameSchema(
    {
        "udi": Column(int, unique=True, nullable=False),
        "product_id": Column(str, nullable=False),
        "product_type": Column(str, Check.isin(["L", "M", "H"]), nullable=False),
        "air_temperature_k": Column(float, checks=[Check.greater_than(250), Check.less_than(350)]),
        "process_temperature_k": Column(
            float, checks=[Check.greater_than(250), Check.less_than(400)]
        ),
        "rotational_speed_rpm": Column(int, Check.greater_than_or_equal_to(0)),
        "torque_nm": Column(float, Check.greater_than_or_equal_to(0)),
        "tool_wear_min": Column(int, Check.greater_than_or_equal_to(0)),
        "machine_failure": Column(int, Check.isin([0, 1])),
    },
    strict=False,
    coerce=True,
)

CmapssSchema = DataFrameSchema(
    {
        "unit_id": Column(int, Check.greater_than_or_equal_to(1), nullable=False),
        "cycle": Column(int, Check.greater_than_or_equal_to(1), nullable=False),
        "rul": Column(int, Check.greater_than_or_equal_to(0)),
    },
    strict=False,
    coerce=True,
)

Mfg004Schema = DataFrameSchema(
    {
        "inspection_id": Column(str, unique=True, nullable=False),
        "inspection_date": Column(str, nullable=False),
        "disposition": Column(str, nullable=False),
        "units_inspected": Column(int, Check.greater_than_or_equal_to(0)),
        "units_accepted": Column(int, Check.greater_than_or_equal_to(0)),
        "units_rejected": Column(int, Check.greater_than_or_equal_to(0)),
        "defects_found_total": Column(int, Check.greater_than_or_equal_to(0)),
    },
    strict=False,
    coerce=False,
)
