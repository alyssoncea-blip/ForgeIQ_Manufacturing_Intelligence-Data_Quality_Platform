"""ForgeIQ — Data Quality & Manufacturing Intelligence dashboard (Dash)."""
from __future__ import annotations

import json
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, ctx, dcc, html

from dashboard.charts import (
    anomaly_overview_card,
    anomaly_rate_figure,
    cmapss_health_card,
    kpi_color,
    kpi_tile,
    quality_kpi_row,
)

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
SILVER = ROOT / "data" / "silver"
QUARANTINE = ROOT / "data" / "quarantine"

C = {
    "bg": "#12161C",
    "panel": "#1C232D",
    "stroke": "#2A3342",
    "amber": "#F5A623",
    "cyan": "#4DD0E1",
    "red": "#E5484D",
    "text": "#E8EAED",
    "muted": "#8A94A6",
    "green": "#3DDC97",
}

NAV = [
    ("overview", "Overview"),
    ("quality", "Quality"),
    ("health", "Machine Health"),
    ("dq", "Data Quality"),
]

FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Barlow+Condensed:wght@500;600;700&"
    "family=Inter:wght@400;500;600&"
    "family=JetBrains+Mono:wght@400;500;700&display=swap"
)

INDEX_STRING = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --bg: #12161C; --panel: #1C232D; --stroke: #2A3342;
                --amber: #F5A623; --cyan: #4DD0E1; --red: #E5484D;
                --text: #E8EAED; --muted: #8A94A6;
            }
            html, body { margin: 0; padding: 0; }
            body {
                background: var(--bg);
                color: var(--text);
                font-family: 'Inter', system-ui, sans-serif;
            }
            .container-fluid, .container {
                padding-left: 14px !important;
                padding-right: 14px !important;
                max-width: 100% !important;
            }
            .fiq-hazard {
                height: 5px;
                background: repeating-linear-gradient(
                    -45deg, var(--amber), var(--amber) 10px,
                    #12161C 10px, #12161C 20px);
            }
            .fiq-topbar {
                background: var(--panel);
                border-bottom: 1px solid var(--stroke);
                padding-top: 4px;
                padding-bottom: 4px;
            }
            .fiq-brand {
                font-family: 'Barlow Condensed', sans-serif;
                font-weight: 700;
                font-size: 22px;
                letter-spacing: 0.14em;
                text-transform: uppercase;
            }
            .fiq-brand-accent { color: var(--amber); }
            .fiq-tagline {
                color: var(--muted);
                font-size: 10px;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                margin-left: 14px;
            }
            .fiq-nav-btn {
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0;
                color: var(--muted);
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                padding: 6px 12px;
                cursor: pointer;
            }
            .fiq-nav-btn:hover { color: var(--amber); }
            .fiq-nav-btn.active {
                color: var(--amber);
                border-bottom-color: var(--amber);
            }
            .fiq-page-header {
                display: flex;
                align-items: flex-end;
                justify-content: space-between;
                gap: 16px;
                flex-wrap: wrap;
            }
            .fiq-title-block { min-width: 0; }
            .fiq-filterbar {
                display: flex;
                flex-direction: row;
                justify-content: flex-end;
                align-items: flex-end;
                flex-wrap: wrap;
                gap: 12px;
            }
            .filter-group {
                display: flex;
                flex-direction: row;
                align-items: flex-end;
                flex-wrap: wrap;
                gap: 12px;
            }
            .fiq-filter-item {
                min-width: 0;
                max-width: none;
                width: 165px;
                flex: 0 0 auto;
            }
            .fiq-filter-item.fiq-date-item { width: auto; }
            .fiq-date .DateRangePickerInput {
                background: var(--bg);
                border: 1px solid var(--stroke);
                border-radius: 6px;
            }
            .fiq-date .DateInput { background: transparent; width: 96px; }
            .fiq-date .DateInput_input {
                background: transparent;
                color: #1f1f1f;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                padding: 6px 8px;
            }
            .fiq-date .DateInput_input:focus {
                outline: none;
                border-bottom-color: var(--amber);
            }
            .fiq-date .DateInput_placeholder { color: #8a8a8a; }
            .fiq-date .DateRangePickerDivider { border-color: var(--stroke); }
            .fiq-date .DayPickerKeyboardShortcuts__button { display: none; }
            .fiq-date .DateRangePicker { z-index: 3000; }
            .fiq-date .CalendarDay { color: var(--text); }
            .fiq-date .CalendarDay__selected {
                background: var(--amber) !important;
                color: #12161C !important;
            }
            .fiq-date .CalendarDay__selected_span {
                background: rgba(245, 166, 35, 0.25) !important;
                color: var(--text) !important;
            }
            .fiq-label {
                color: var(--muted);
                font-size: 10px;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                margin-bottom: 4px;
            }
            .fiq-filter .Select-control {
                background: var(--bg) !important;
                border-color: var(--stroke) !important;
                border-radius: 6px;
                min-height: 32px !important;
            }
            .fiq-filter .Select-placeholder,
            .fiq-filter .Select-value-label,
            .fiq-filter .Select-value-label span {
                color: var(--muted) !important;
                line-height: 32px !important;
            }
            .fiq-filter .Select-input > input { color: var(--text) !important; }
            .fiq-filter .Select-menu-outer {
                background: var(--panel) !important;
                border-color: var(--stroke) !important;
            }
            .fiq-filter .VirtualizedSelectOption { background: var(--panel); color: var(--text); }
            .fiq-filter .VirtualizedSelectFocusedOption { background: var(--stroke); }
            .fiq-filter .Select-clear-zone { color: var(--muted) !important; }
            .fiq-card {
                background: var(--panel);
                border: 1px solid var(--stroke);
                border-radius: 8px;
                padding: 12px 14px;
            }
            .fiq-section-title {
                color: var(--muted);
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin-bottom: 6px;
            }
            .fiq-value {
                font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
                font-size: 26px;
                font-weight: 700;
                margin-top: 4px;
            }
            .fiq-page-title {
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin: 0;
            }
            .fiq-mono {
                font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
            }
            .fiq-table { color: var(--text); font-size: 13px; margin-top: 10px; }
            .fiq-table th {
                color: var(--muted);
                font-size: 11px;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                border-bottom: 1px solid var(--stroke) !important;
            }
            .fiq-table td { border-color: var(--stroke) !important; }
            .js-plotly-plot .plotly .main-svg { background: transparent; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

th_style = {
    "textAlign": "left",
    "padding": "8px 10px",
    "borderBottom": f"1px solid {C['stroke']}",
    "color": C["muted"],
    "fontWeight": "600",
}

td_style = {
    "textAlign": "left",
    "padding": "7px 10px",
    "borderBottom": f"1px solid {C['stroke']}",
    "color": C["text"],
}

_DF_CACHE: dict[str, pd.DataFrame] = {}


def _load(name: str) -> pd.DataFrame:
    if name not in _DF_CACHE:
        _DF_CACHE[name] = pd.read_parquet(GOLD / f"{name}.parquet")
    return _DF_CACHE[name]


def _latest_report() -> dict | None:
    reports = sorted(QUARANTINE.glob("dq_report_*.json"))
    if not reports:
        return None
    return json.loads(reports[-1].read_text(encoding="utf-8"))


def _panel(title: str, graph) -> html.Div:
    return html.Div(
        [html.Div(title.upper(), className="fiq-section-title"), graph],
        className="fiq-card",
    )


def _nav_class(active: bool) -> str:
    return "fiq-nav-btn active" if active else "fiq-nav-btn"


def _group_class(active: bool) -> str:
    return "filter-group" if active else "d-none"


PAGE_META: dict[str, tuple[str, str]] = {
    "overview": (
        "Factory Overview",
        "Production · quality · anomalies at a glance",
    ),
    "quality": ("Quality Intelligence", "FPY · defects · disposition"),
    "health": ("Machine Health", "RUL · anomalies · downtime"),
    "dq": ("Data Quality", "Rule results · quarantine · score"),
}


def _grid(children, cols: list[str]) -> dbc.Row:
    return dbc.Row(
        [dbc.Col(child, width=w) for child, w in zip(children, cols, strict=True)],
        className="g-3 mb-3",
    )


def _kpi_row(cards: list) -> dbc.Row:
    return dbc.Row(
        [dbc.Col(card, width=True) for card in cards],
        className="g-2 mb-3",
    )


def _sel(values) -> list:
    if not values:
        return []
    return list(values)


def _filter_item(label: str, id_: str, options: list) -> html.Div:
    return html.Div(
        [
            html.Div(label.upper(), className="fiq-label"),
            dcc.Dropdown(
                id=id_,
                options=[{"label": str(o), "value": o} for o in options],
                multi=True,
                clearable=True,
                placeholder="Todos",
                className="fiq-filter",
            ),
        ],
        className="fiq-filter-item",
    )


def _date_filter_item(label: str, id_: str, min_d, max_d) -> html.Div:
    props: dict = {
        "id": id_,
        "className": "fiq-date",
        "display_format": "YYYY-MM-DD",
        "clearable": True,
    }
    if min_d:
        props["min_date_allowed"] = min_d
        props["start_date"] = min_d
    if max_d:
        props["max_date_allowed"] = max_d
        props["end_date"] = max_d
    return html.Div(
        [
            html.Div(label.upper(), className="fiq-label"),
            dcc.DatePickerRange(**props),
        ],
        className="fiq-filter-item fiq-date-item",
    )


def _date_mask(series, dr):
    """Boolean mask for [start, end] inclusive; None when no range set."""
    if not dr or len(dr) < 2 or not dr[0] or not dr[1]:
        return None
    s = pd.to_datetime(series)
    if getattr(s.dt, "tz", None) is not None:
        s = s.dt.tz_localize(None)
    d0 = pd.Timestamp(dr[0])
    d1 = pd.Timestamp(dr[1]) + pd.Timedelta(days=1)
    return (s >= d0) & (s < d1)


def _apply_date(df, col, dr):
    mask = _date_mask(df[col], dr) if col in df.columns else None
    return df if mask is None else df[mask]


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default if default is not None else []


def _opt_lines() -> list:
    def go_():
        return sorted(
            set(_load("fact_production")["line_id"].dropna())
            | set(_load("fact_quality")["line_id"].dropna())
        )

    return _safe(go_)


def _opt_sources() -> list:
    return _safe(lambda: sorted(_load("fact_anomaly")["source"].dropna().unique()))


def _opt_dispositions() -> list:
    return _safe(lambda: sorted(_load("fact_quality")["disposition"].dropna().unique()))


def _opt_severities() -> list:
    return _safe(
        lambda: sorted(
            _load("fact_quality")["defect_severity_class"].dropna().unique()
        )
    )


def _opt_machines() -> list:
    def go_():
        m = _load("fact_maintenance")["machine_id"].dropna().unique()
        return sorted(m)

    return _safe(go_)


def _opt_modes() -> list:
    return _safe(
        lambda: sorted(
            _load("fact_maintenance")["failure_modes"].dropna().unique()
        )
    )


def _opt_units() -> list:
    def go_():
        c = pd.read_parquet(SILVER / "fact_sensor_reading_cmapss.parquet")
        return sorted(int(u) for u in c["unit_id"].unique())

    return _safe(go_)


def _opt_conditions() -> list:
    return ["anomaly", "normal"]


def _opt_dq_severities() -> list:
    def go_():
        report = _latest_report()
        if report is None:
            return []
        sev = {
            r["severity"]
            for info in report["tables"].values()
            for r in info["rules"]
        }
        return sorted(sev)

    return _safe(go_)


def _opt_dq_status() -> list:
    return ["PASS", "FAIL"]


def _prod_bounds() -> tuple:
    def go_():
        s = pd.to_datetime(_load("fact_production")["date"])
        return s.min().date(), s.max().date()

    return _safe(go_, (None, None))


def _health_bounds() -> tuple:
    def go_():
        s = pd.to_datetime(_load("fact_anomaly")["event_time"], utc=True)
        return s.min().date(), s.max().date()

    return _safe(go_, (None, None))


def _filter_bar() -> html.Div:
    ov_min, ov_max = _prod_bounds()
    hl_min, hl_max = _health_bounds()
    return html.Div(
        [
            html.Div(
                id="fgrp-overview",
                className="filter-group",
                children=[
                    _filter_item("Line", "flt-ov-line", _opt_lines()),
                    _filter_item("Source", "flt-ov-source", _opt_sources()),
                    _filter_item("Condition", "flt-ov-condition", _opt_conditions()),
                    _date_filter_item("Date range", "flt-ov-date", ov_min, ov_max),
                ],
            ),
            html.Div(
                id="fgrp-quality",
                className="d-none",
                children=[
                    _filter_item("Line", "flt-qt-line", _opt_lines()),
                    _filter_item(
                        "Disposition", "flt-qt-disp", _opt_dispositions()
                    ),
                    _filter_item("Severity", "flt-qt-sev", _opt_severities()),
                    _date_filter_item("Date range", "flt-qt-date", ov_min, ov_max),
                ],
            ),
            html.Div(
                id="fgrp-health",
                className="d-none",
                children=[
                    _filter_item("Machine", "flt-hl-machine", _opt_machines()),
                    _filter_item("Source", "flt-hl-source", _opt_sources()),
                    _filter_item("Failure mode", "flt-hl-mode", _opt_modes()),
                    _filter_item("CMAPSS unit", "flt-hl-unit", _opt_units()),
                    _date_filter_item("Date range", "flt-hl-date", hl_min, hl_max),
                ],
            ),
            html.Div(
                id="fgrp-dq",
                className="d-none",
                children=[
                    _filter_item("Severity", "flt-dq-sev", _opt_dq_severities()),
                    _filter_item("Status", "flt-dq-status", _opt_dq_status()),
                ],
            ),
        ],
        className="fiq-filterbar",
    )


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def _overview_kpis(
    line_sel: list,
    src_sel: list,
    date_range: tuple | None = None,
) -> dict:
    production = _load("fact_production")
    quality = _load("fact_quality")
    maint = _load("fact_maintenance")
    anomaly = _load("fact_anomaly")
    kpis = _load("kpi_summary")
    kmap = {r.kpi: r.value for r in kpis.itertuples()}

    prod = production
    if line_sel:
        prod = prod[prod["line_id"].isin(line_sel)]
    prod = _apply_date(prod, "date", date_range)
    qual = quality
    if line_sel:
        qual = qual[qual["line_id"].isin(line_sel)]
    qual = _apply_date(qual, "date", date_range)

    inspected = prod["units_inspected"].sum()
    accepted = prod["units_accepted"].sum()
    rejected = prod["units_rejected"].sum()
    defects = prod["defects_found_total"].sum()

    anom = anomaly
    if src_sel:
        anom = anom[anom["source"].isin(src_sel)]
    anom = _apply_date(anom, "event_time", date_range)

    return {
        "fpy": (accepted / inspected) if inspected else None,
        "defect_rate": (defects / inspected) if inspected else None,
        "scrap_rate": (rejected / inspected) if inspected else None,
        "anomaly_rate": (
            float(anom["is_anomaly"].mean()) if not anom.empty else None
        ),
        "failures": int(maint["event_type"].eq("ai4i_failure").sum()),
        "downtime": float(maint["downtime_hours_estimated"].sum()),
        "total_production": float(inspected) if inspected else kmap.get(
            "total_production_units"
        ),
    }


def _page_overview(
    line_sel: list | None = None,
    src_sel: list | None = None,
    cond_sel: list | None = None,
    date_range: tuple | None = None,
) -> html.Div:
    line_sel, src_sel, cond_sel = _sel(line_sel), _sel(src_sel), _sel(cond_sel)
    production = _load("fact_production")
    maint = _load("fact_maintenance")
    anomaly = _load("fact_anomaly")

    prod = production
    if line_sel:
        prod = prod[prod["line_id"].isin(line_sel)]
    prod = _apply_date(prod, "date", date_range)
    prod = prod.sort_values("date")

    fig_prod = go.Figure()
    fig_prod.add_trace(
        go.Bar(
            x=prod["date"],
            y=prod["units_rejected"],
            name="Rejected",
            marker_color=C["red"],
        )
    )
    fig_prod.add_trace(
        go.Bar(
            x=prod["date"],
            y=prod["units_accepted"],
            name="Accepted",
            marker_color=C["cyan"],
        )
    )
    fig_prod.update_layout(
        barmode="stack",
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        legend=dict(orientation="h"),
        margin=dict(t=26, b=10, l=10, r=10),
        height=300,
        xaxis=dict(gridcolor=C["stroke"], zeroline=False),
        yaxis=dict(gridcolor=C["stroke"], zeroline=False),
    )

    fail_modes = (
        maint[maint["event_type"] == "ai4i_failure"]["failure_modes"]
        .fillna("unknown")
        .value_counts()
        .head(6)
    )
    fig_fail = px.bar(
        x=fail_modes.values,
        y=fail_modes.index,
        orientation="h",
        labels={"x": "Failures", "y": ""},
        color_discrete_sequence=[C["red"]],
    )
    fig_fail.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        xaxis=dict(gridcolor=C["stroke"], zeroline=False),
        yaxis=dict(gridcolor=C["stroke"], zeroline=False),
    )

    anom = anomaly
    if src_sel:
        anom = anom[anom["source"].isin(src_sel)]
    anom = _apply_date(anom, "event_time", date_range)
    if cond_sel:
        want = {c == "anomaly" for c in cond_sel}
        if len(want) == 1:
            anom = anom[anom["is_anomaly"].isin(want)]

    kpis = _overview_kpis(line_sel, src_sel, date_range)

    return html.Div(
        [
            _kpi_row(quality_kpi_row(kpis, C)),
            _grid(
                [
                    _panel(
                        "Production units (accepted / rejected)",
                        dcc.Graph(figure=fig_prod, config={"displayModeBar": False}),
                    ),
                    _panel(
                        "Top failure modes (AI4I)",
                        dcc.Graph(figure=fig_fail, config={"displayModeBar": False}),
                    ),
                ],
                ["lg-8", "lg-4"],
            ),
            _panel(
                "Anomaly rate by source",
                dcc.Graph(
                    figure=anomaly_overview_card(anom, C),
                    config={"displayModeBar": False},
                ),
            ),
        ]
    )


def _page_quality(
    line_sel: list | None = None,
    disp_sel: list | None = None,
    sev_sel: list | None = None,
    date_range: tuple | None = None,
) -> html.Div:
    line_sel, disp_sel, sev_sel = _sel(line_sel), _sel(disp_sel), _sel(sev_sel)
    production = _load("fact_production")
    quality = _load("fact_quality")

    prod = production
    if line_sel:
        prod = prod[prod["line_id"].isin(line_sel)]
    prod = _apply_date(prod, "date", date_range)
    prod = prod.sort_values("date")

    qual = quality
    if line_sel:
        qual = qual[qual["line_id"].isin(line_sel)]
    qual = _apply_date(qual, "date", date_range)
    if disp_sel:
        qual = qual[qual["disposition"].isin(disp_sel)]
    if sev_sel:
        qual = qual[qual["defect_severity_class"].isin(sev_sel)]

    inspected = prod["units_inspected"].sum() or 1
    kpi = {
        "fpy": prod["units_accepted"].sum() / inspected,
        "defect_rate": prod["defects_found_total"].sum() / inspected,
        "scrap_rate": prod["units_rejected"].sum() / inspected,
        "anomaly_rate": None,
        "failures": int(qual["units_rejected"].sum()),
        "downtime": None,
        "total_production": float(prod["units_inspected"].sum()),
    }

    fig_fpy = px.line(
        prod,
        x="date",
        y="first_pass_yield",
        color="line_id",
        markers=True,
        color_discrete_sequence=[C["cyan"], C["amber"], C["text"]],
    )
    fig_fpy.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        yaxis_tickformat=".1%",
        legend=dict(orientation="h"),
        margin=dict(t=26, b=10, l=10, r=10),
        height=320,
        xaxis=dict(gridcolor=C["stroke"], zeroline=False),
        yaxis=dict(gridcolor=C["stroke"], zeroline=False),
    )

    top_defects = (
        qual.groupby("defect_type_primary")["units_rejected"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
    )
    fig_def = px.bar(
        x=top_defects.index,
        y=top_defects.values,
        color_discrete_sequence=[C["red"]],
        labels={"x": "Defect type", "y": "Units rejected"},
    )
    fig_def.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
        xaxis=dict(gridcolor=C["stroke"], zeroline=False),
        yaxis=dict(gridcolor=C["stroke"], zeroline=False),
    )

    disp = qual["disposition"].value_counts()
    if disp.empty:
        fig_disp = go.Figure()
        fig_disp.update_layout(
            paper_bgcolor=C["panel"],
            height=320,
            annotations=[
                {
                    "text": "No data for current filters",
                    "showarrow": False,
                    "font": {"color": C["muted"]},
                }
            ],
        )
    else:
        fig_disp = px.pie(
            names=disp.index,
            values=disp.values,
            hole=0.55,
            color_discrete_sequence=[C["cyan"], C["amber"], C["red"]],
        )
        fig_disp.update_layout(
            paper_bgcolor=C["panel"],
            font_color=C["text"],
            legend=dict(orientation="h"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )

    return html.Div(
        [
            _kpi_row(
                [
                    kpi_tile("FPY", f"{kpi['fpy']:.1%}", kpi_color("fpy", kpi["fpy"], C)),
                    kpi_tile(
                        "Defect rate",
                        f"{kpi['defect_rate']:.2%}",
                        kpi_color("defect_rate", kpi["defect_rate"], C),
                    ),
                    kpi_tile(
                        "Scrap rate",
                        f"{kpi['scrap_rate']:.1%}",
                        kpi_color("scrap_rate", kpi["scrap_rate"], C),
                    ),
                    kpi_tile(
                        "Rejected units",
                        f"{kpi['failures']:,.0f}",
                        C["text"],
                    ),
                    kpi_tile(
                        "Total production",
                        f"{kpi['total_production']:,.0f}",
                        C["cyan"],
                    ),
                ]
            ),
            _panel(
                "First Pass Yield by line",
                dcc.Graph(figure=fig_fpy, config={"displayModeBar": False}),
            ),
            html.Div(style={"height": "12px"}),
            _grid(
                [
                    _panel(
                        "Top defect types",
                        dcc.Graph(figure=fig_def, config={"displayModeBar": False}),
                    ),
                    _panel(
                        "Disposition mix",
                        dcc.Graph(figure=fig_disp, config={"displayModeBar": False}),
                    ),
                ],
                ["lg-8", "lg-4"],
            ),
        ]
    )


def _page_health(
    mach_sel: list | None = None,
    src_sel: list | None = None,
    mode_sel: list | None = None,
    unit_sel: list | None = None,
    date_range: tuple | None = None,
) -> html.Div:
    mach_sel, src_sel = _sel(mach_sel), _sel(src_sel)
    mode_sel, unit_sel = _sel(mode_sel), _sel(unit_sel)
    cmapss = pd.read_parquet(SILVER / "fact_sensor_reading_cmapss.parquet")
    anomaly = _load("fact_anomaly")
    maint = _load("fact_maintenance")

    anom = anomaly
    if mach_sel:
        anom = anom[anom["machine_id"].isin(mach_sel)]
    if src_sel:
        anom = anom[anom["source"].isin(src_sel)]
    anom = _apply_date(anom, "event_time", date_range)

    mnt = maint
    if mach_sel:
        mnt = mnt[mnt["machine_id"].isin(mach_sel)]
    if mode_sel:
        mnt = mnt[mnt["failure_modes"].isin(mode_sel)]
    mnt = _apply_date(mnt, "event_time", date_range)

    cmap = cmapss
    if unit_sel:
        cmap = cmap[cmap["unit_id"].isin(unit_sel)]

    fig_rul = cmapss_health_card(cmap, C)
    fig_anom = anomaly_timeline(anom, C)

    maint_summary = (
        mnt[mnt["event_type"] == "ai4i_failure"]
        .groupby("failure_modes")
        .agg(
            events=("event_type", "count"),
            downtime=("downtime_hours_estimated", "sum"),
        )
        .sort_values("events", ascending=False)
        .head(6)
        .reset_index()
    )
    fig_down = px.bar(
        maint_summary,
        x="downtime",
        y="failure_modes",
        orientation="h",
        color_discrete_sequence=[C["amber"]],
        labels={"downtime": "Estimated downtime (h)", "failure_modes": ""},
    )
    fig_down.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
        xaxis=dict(gridcolor=C["stroke"], zeroline=False),
        yaxis=dict(gridcolor=C["stroke"], zeroline=False),
    )

    failures = int((mnt["event_type"] == "ai4i_failure").sum())
    downtime = float(mnt["downtime_hours_estimated"].sum())
    units = int(cmapss["unit_id"].nunique())
    max_rul = int(cmapss["cycle"].max()) if not cmapss.empty else 0

    tiles = [
        kpi_tile("Fleet units", f"{units:,}", kpi_color("units", 1, C)),
        kpi_tile("Failure events", f"{failures:,}", kpi_color("failures", 1, C)),
        kpi_tile("Downtime h (est)", f"{downtime:,.0f}", kpi_color("downtime", 1, C)),
        kpi_tile("Max RUL (cycles)", f"{max_rul:,}", kpi_color("max_rul", 1, C)),
    ]

    return html.Div(
        [
            _kpi_row(tiles),
            _panel(
                "Fleet RUL (CMAPSS FD001 — sample units)",
                dcc.Graph(figure=fig_rul, config={"displayModeBar": False}),
            ),
            html.Div(style={"height": "12px"}),
            _grid(
                [
                    _panel(
                        "Anomaly score timeline",
                        dcc.Graph(figure=fig_anom, config={"displayModeBar": False}),
                    ),
                    _panel(
                        "Downtime estimate by failure mode",
                        dcc.Graph(figure=fig_down, config={"displayModeBar": False}),
                    ),
                ],
                ["lg", "lg"],
            ),
        ]
    )


def _page_dq(
    sev_sel: list | None = None,
    status_sel: list | None = None,
) -> html.Div:
    sev_sel, status_sel = _sel(sev_sel), _sel(status_sel)
    report = _latest_report()
    if report is None:
        return html.Div(
            "No DQ report found. Run `python -m data_quality.pipeline`.",
            style={"color": C["muted"]},
        )

    rows = []
    for table, info in report["tables"].items():
        for rule in info["rules"]:
            rows.append(
                {
                    "table": table,
                    "rule": rule["rule_id"],
                    "severity": rule["severity"],
                    "passed": "PASS" if rule["passed"] else "FAIL",
                }
            )
    rules_df = pd.DataFrame(rows)
    if sev_sel:
        rules_df = rules_df[rules_df["severity"].isin(sev_sel)]
    if status_sel:
        rules_df = rules_df[rules_df["passed"].isin(status_sel)]
    rules_df = rules_df.reset_index(drop=True)
    rules_df["value"] = 1

    color_map = {"PASS": C["cyan"], "FAIL": C["red"]}
    if rules_df.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=C["panel"],
            height=200,
            annotations=[
                {
                    "text": "No rules match the selected filters",
                    "showarrow": False,
                    "font": {"color": C["muted"]},
                }
            ],
        )
    else:
        fig = px.bar(
            rules_df.sort_values(["table", "rule"]),
            x="rule",
            y="value",
            color="passed",
            color_discrete_map=color_map,
            labels={"y": "", "rule": "Rule"},
        )
        fig.update_layout(
            showlegend=False,
            paper_bgcolor=C["panel"],
            plot_bgcolor=C["panel"],
            font_color=C["text"],
            margin=dict(t=10, b=40, l=10, r=10),
            height=340,
            xaxis=dict(gridcolor=C["stroke"], zeroline=False),
            yaxis=dict(gridcolor=C["stroke"], zeroline=False),
        )

    score = report["overall_dq_score"]
    score_color = kpi_color("dq_score", score, C)

    table_cards = []
    for table, info in report["tables"].items():
        table_cards.append(
            html.Div(
                [
                    html.Div(table.upper(), className="fiq-label"),
                    html.Div(
                        f"{info['rows']:,} rows · Q:{info['quarantined_rows']}",
                        className="fiq-mono",
                        style={"fontSize": "13px", "marginTop": "6px"},
                    ),
                    html.Div(
                        f"score {info['dq_score_error_rules']:.2f}",
                        className="fiq-mono",
                        style={
                            "color": kpi_color(
                                "dq_score", info["dq_score_error_rules"], C
                            ),
                            "fontWeight": "600",
                            "marginTop": "4px",
                        },
                    ),
                ],
                className="fiq-card",
            )
        )

    score_card = html.Div(
        [
            html.Div("OVERALL DQ SCORE", className="fiq-label"),
            html.Div(
                f"{score:.0%}",
                className="fiq-value",
                style={"color": score_color, "fontSize": "44px"},
            ),
            html.Div(
                f"{report['rules_passed']}/{report['rules_total']} rules passed",
                className="fiq-mono",
                style={"fontSize": "13px", "marginTop": "6px"},
            ),
            html.Div(
                f"batch {report['batch_id']}",
                style={"color": C["muted"], "fontSize": "11px", "marginTop": "6px"},
            ),
        ],
        className="fiq-card",
    )

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(score_card, md=4),
                    dbc.Col(
                        html.Div(children=table_cards, className="d-grid gap-3"),
                        md=8,
                    ),
                ],
                className="g-3 mb-3",
            ),
            _panel(
                "Rule status",
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
            ),
            html.Div(style={"height": "12px"}),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Rule", style=th_style),
                                html.Th("Table", style=th_style),
                                html.Th("Severity", style=th_style),
                                html.Th("Status", style=th_style),
                            ]
                        )
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(r["rule"], style=td_style),
                                    html.Td(r["table"], style=td_style),
                                    html.Td(r["severity"], style=td_style),
                                    html.Td(
                                        r["passed"],
                                        style={
                                            **td_style,
                                            "color": C["cyan"]
                                            if r["passed"] == "PASS"
                                            else C["red"],
                                            "fontWeight": "600",
                                        },
                                    ),
                                ]
                            )
                            for r in rules_df.to_dict("records")
                        ]
                    ),
                ],
                className="fiq-table",
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
        ],
        style={"display": "grid", "gap": "0"},
    )


def anomaly_timeline(anomaly: pd.DataFrame, palette: dict) -> go.Figure:
    a = anomaly.copy()
    if a.empty:
        return anomaly_rate_figure(a, palette, height=320)
    a["date"] = pd.to_datetime(a["event_time"]).dt.date
    rate = a.groupby(["date", "source"], as_index=False)["is_anomaly"].mean()
    return anomaly_rate_figure(rate, palette, height=320)


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------

app = Dash(
    __name__,
    title="ForgeIQ",
    update_title="ForgeIQ…",
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, FONTS],
    index_string=INDEX_STRING,
)
server = app.server


def _layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="page", data="overview"),
            html.Div(className="fiq-hazard"),
            html.Header(
                dbc.Container(
                    [
                        html.Div(
                            [
                                html.Span("FORGE", className="fiq-brand"),
                                html.Span(
                                    "IQ", className="fiq-brand fiq-brand-accent"
                                ),
                            ],
                            style={"display": "flex"},
                        ),
                        html.Div(
                            "Manufacturing Intelligence · Data Quality",
                            className="fiq-tagline",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "■ OK",
                                    style={"color": C["cyan"]},
                                ),
                                html.Span(
                                    "■ ATTENTION",
                                    style={"color": C["amber"]},
                                ),
                                html.Span(
                                    "■ FAILURE",
                                    style={"color": C["red"]},
                                ),
                            ],
                            className="fiq-tagline",
                            style={
                                "marginLeft": "24px",
                                "display": "flex",
                                "gap": "12px",
                            },
                        ),
                        html.Nav(
                            [
                                html.Button(
                                    label,
                                    id={"type": "nav", "index": key},
                                    n_clicks=0,
                                    className=_nav_class(key == "overview"),
                                )
                                for key, label in NAV
                            ],
                            className="d-flex ms-auto",
                        ),
                    ],
                    fluid=True,
                    className="d-flex align-items-center py-2",
                ),
                className="fiq-topbar",
            ),
            dbc.Container(
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2(
                                    PAGE_META["overview"][0],
                                    id="page-title",
                                    className="fiq-page-title",
                                ),
                                html.Div(
                                    PAGE_META["overview"][1].upper(),
                                    id="page-subtitle",
                                    className="fiq-label",
                                ),
                            ],
                            className="fiq-title-block",
                        ),
                        _filter_bar(),
                    ],
                    className="fiq-page-header",
                ),
                fluid=True,
                className="px-3 pt-3",
            ),
            dbc.Container(
                id="content",
                fluid=True,
                className="p-3",
            ),
        ],
        style={"minHeight": "100vh", "background": C["bg"]},
    )


app.layout = _layout()

PAGES = {
    "overview": _page_overview,
    "quality": _page_quality,
    "health": _page_health,
    "dq": _page_dq,
}


@callback(
    Output("page", "data"),
    Output({"type": "nav", "index": "overview"}, "className"),
    Output({"type": "nav", "index": "quality"}, "className"),
    Output({"type": "nav", "index": "health"}, "className"),
    Output({"type": "nav", "index": "dq"}, "className"),
    Output("fgrp-overview", "className"),
    Output("fgrp-quality", "className"),
    Output("fgrp-health", "className"),
    Output("fgrp-dq", "className"),
    Output("page-title", "children"),
    Output("page-subtitle", "children"),
    Input({"type": "nav", "index": "overview"}, "n_clicks"),
    Input({"type": "nav", "index": "quality"}, "n_clicks"),
    Input({"type": "nav", "index": "health"}, "n_clicks"),
    Input({"type": "nav", "index": "dq"}, "n_clicks"),
    prevent_initial_call=True,
)
def _nav(_o, _q, _h, _d):
    key = "overview"
    if isinstance(ctx.triggered_id, dict):
        key = ctx.triggered_id.get("index", "overview")
    title, sub = PAGE_META.get(key, PAGE_META["overview"])
    return (
        key,
        *[_nav_class(key == k) for k, _ in NAV],
        *[_group_class(key == k) for k, _ in NAV],
        title,
        sub.upper(),
    )


@callback(
    Output("content", "children"),
    Input("page", "data"),
    Input("flt-ov-line", "value"),
    Input("flt-ov-source", "value"),
    Input("flt-ov-condition", "value"),
    Input("flt-qt-line", "value"),
    Input("flt-qt-disp", "value"),
    Input("flt-qt-sev", "value"),
    Input("flt-hl-machine", "value"),
    Input("flt-hl-source", "value"),
    Input("flt-hl-mode", "value"),
    Input("flt-hl-unit", "value"),
    Input("flt-dq-sev", "value"),
    Input("flt-dq-status", "value"),
    Input("flt-ov-date", "start_date"),
    Input("flt-ov-date", "end_date"),
    Input("flt-qt-date", "start_date"),
    Input("flt-qt-date", "end_date"),
    Input("flt-hl-date", "start_date"),
    Input("flt-hl-date", "end_date"),
)
def _render(
    page,
    ov_line,
    ov_src,
    ov_cond,
    qt_line,
    qt_disp,
    qt_sev,
    hl_mach,
    hl_src,
    hl_mode,
    hl_unit,
    dq_sev,
    dq_status,
    ov_d0,
    ov_d1,
    qt_d0,
    qt_d1,
    hl_d0,
    hl_d1,
):
    if page == "quality":
        return _page_quality(
            _sel(qt_line), _sel(qt_disp), _sel(qt_sev), (qt_d0, qt_d1)
        )
    if page == "health":
        return _page_health(
            _sel(hl_mach),
            _sel(hl_src),
            _sel(hl_mode),
            _sel(hl_unit),
            (hl_d0, hl_d1),
        )
    if page == "dq":
        return _page_dq(_sel(dq_sev), _sel(dq_status))
    return _page_overview(
        _sel(ov_line), _sel(ov_src), _sel(ov_cond), (ov_d0, ov_d1)
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
