"""ForgeIQ — Data Quality & Manufacturing Intelligence dashboard (Dash)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, ctx, dcc, html

from dashboard.charts import (
    anomaly_overview_card,
    cmapss_health_card,
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
    "text": "#E6EAF0",
    "muted": "#8A94A6",
    "green": "#3DDC97",
}

NAV = [
    ("overview", "Overview"),
    ("quality", "Quality"),
    ("health", "Machine Health"),
    ("dq", "Data Quality"),
]

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


def _load(name: str) -> pd.DataFrame:
    return pd.read_parquet(GOLD / f"{name}.parquet")


def _latest_report() -> dict | None:
    import json

    reports = sorted(QUARANTINE.glob("dq_report_*.json"))
    if not reports:
        return None
    return json.loads(reports[-1].read_text(encoding="utf-8"))


def _panel(title: str, graph) -> html.Div:
    return html.Div(
        [
            html.Div(
                title,
                style={"color": C["muted"], "fontSize": "13px", "marginBottom": "6px"},
            ),
            graph,
        ],
        style={
            "background": C["panel"],
            "border": f"1px solid {C['stroke']}",
            "borderRadius": "12px",
            "padding": "12px",
        },
    )


def _nav_btn_style(active: bool) -> dict:
    return {
        "background": C["amber"] if active else "transparent",
        "color": C["bg"] if active else C["text"],
        "border": f"1px solid {C['amber'] if active else C['stroke']}",
        "borderRadius": "8px",
        "padding": "8px 14px",
        "fontSize": "13px",
        "fontWeight": "600",
        "cursor": "pointer",
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def _page_overview() -> html.Div:
    kpis = _load("kpi_summary")
    kmap = {r.kpi: r for r in kpis.itertuples()}
    production = _load("fact_production")
    maint = _load("fact_maintenance")
    anomaly = _load("fact_anomaly")

    prod = production.sort_values("date")
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
        margin=dict(t=30, b=10, l=10, r=10),
        height=320,
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
        color_discrete_sequence=[C["amber"]],
    )
    fig_fail.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
    )

    cards = quality_kpi_row(kmap, C)

    return html.Div(
        [
            html.Div(
                cards,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(5, 1fr)",
                    "gap": "12px",
                },
            ),
            html.Div(
                [
                    _panel(
                        "Production units (accepted / rejected)",
                        dcc.Graph(figure=fig_prod),
                    ),
                    _panel("Top failure modes (AI4I)", dcc.Graph(figure=fig_fail)),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "3fr 2fr",
                    "gap": "12px",
                    "marginTop": "16px",
                },
            ),
            _panel(
                "Anomaly rate by source",
                dcc.Graph(figure=anomaly_overview_card(anomaly, C)),
            ),
        ]
    )


def _page_quality() -> html.Div:
    production = _load("fact_production")
    quality = _load("fact_quality")
    prod = production.sort_values("date")

    fig_fpy = px.line(
        prod,
        x="date",
        y="first_pass_yield",
        color="line_id",
        markers=True,
        color_discrete_sequence=[C["cyan"], C["amber"], C["green"]],
    )
    fig_fpy.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        yaxis_tickformat=".1%",
        legend=dict(orientation="h"),
        margin=dict(t=30, b=10, l=10, r=10),
        height=340,
    )

    top_defects = (
        quality.groupby("defect_type_primary")["units_rejected"]
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
        height=340,
    )

    disp = quality["disposition"].value_counts()
    fig_disp = px.pie(
        names=disp.index,
        values=disp.values,
        hole=0.55,
        color_discrete_sequence=[C["green"], C["amber"], C["red"]],
    )
    fig_disp.update_layout(
        paper_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=340,
    )

    return html.Div(
        [
            _panel("First Pass Yield by line", dcc.Graph(figure=fig_fpy)),
            html.Div(
                [
                    _panel("Top defect types", dcc.Graph(figure=fig_def)),
                    _panel("Disposition mix", dcc.Graph(figure=fig_disp)),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "2fr 1fr",
                    "gap": "12px",
                    "marginTop": "12px",
                },
            ),
        ]
    )


def _page_health() -> html.Div:
    cmapss = pd.read_parquet(SILVER / "fact_sensor_reading_cmapss.parquet")
    anomaly = _load("fact_anomaly")
    maint = _load("fact_maintenance")

    fig_rul = cmapss_health_card(cmapss, C)
    fig_anom = anomaly_timeline(anomaly, C)

    maint_summary = (
        maint[maint["event_type"] == "ai4i_failure"]
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
        height=340,
    )

    return html.Div(
        [
            _panel(
                "Fleet RUL (CMAPSS FD001 — sample units)",
                dcc.Graph(figure=fig_rul),
            ),
            html.Div(
                [
                    _panel(
                        "Anomaly score timeline",
                        dcc.Graph(figure=fig_anom),
                    ),
                    _panel(
                        "Downtime estimate by failure mode",
                        dcc.Graph(figure=fig_down),
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "12px",
                    "marginTop": "12px",
                },
            ),
        ]
    )


def _page_dq() -> html.Div:
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
    rules_df["value"] = 1

    color_map = {"PASS": C["green"], "FAIL": C["red"]}
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
        height=360,
    )

    score = report["overall_dq_score"]
    if score >= 0.99:
        score_color = C["green"]
    elif score >= 0.95:
        score_color = C["amber"]
    else:
        score_color = C["red"]

    table_cards = []
    for table, info in report["tables"].items():
        table_cards.append(
            html.Div(
                [
                    html.Div(
                        table,
                        style={"color": C["muted"], "fontSize": "13px"},
                    ),
                    html.Div(
                        f"{info['rows']:,} rows · Q:{info['quarantined_rows']}",
                        style={
                            "color": C["text"],
                            "fontSize": "14px",
                            "marginTop": "4px",
                        },
                    ),
                    html.Div(
                        f"score {info['dq_score_error_rules']:.2f}",
                        style={
                            "color": score_color,
                            "fontWeight": "600",
                            "marginTop": "4px",
                        },
                    ),
                ],
                style={
                    "background": C["panel"],
                    "border": f"1px solid {C['stroke']}",
                    "borderRadius": "10px",
                    "padding": "14px",
                },
            )
        )

    score_card = html.Div(
        [
            html.Div(
                "Overall DQ Score",
                style={"color": C["muted"], "fontSize": "13px"},
            ),
            html.Div(
                f"{score:.0%}",
                style={
                    "color": score_color,
                    "fontSize": "42px",
                    "fontWeight": "700",
                },
            ),
            html.Div(
                f"{report['rules_passed']}/{report['rules_total']} rules passed",
                style={"color": C["text"], "fontSize": "13px"},
            ),
            html.Div(
                f"batch {report['batch_id']}",
                style={
                    "color": C["muted"],
                    "fontSize": "11px",
                    "marginTop": "6px",
                },
            ),
        ],
        style={
            "background": C["panel"],
            "border": f"1px solid {C['stroke']}",
            "borderRadius": "12px",
            "padding": "20px",
        },
    )

    return html.Div(
        [
            score_card,
            html.Div(
                table_cards,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, 1fr)",
                    "gap": "12px",
                },
            ),
            _panel("Rule status", dcc.Graph(figure=fig)),
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
                                            "color": C["green"]
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
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "fontSize": "13px",
                },
            ),
        ],
        style={"display": "grid", "gap": "16px"},
    )


def anomaly_timeline(anomaly: pd.DataFrame, palette: dict) -> go.Figure:
    a = anomaly.copy()
    if a.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=palette["panel"], height=240)
        return fig
    a["date"] = pd.to_datetime(a["event_time"]).dt.date
    rate = a.groupby(["date", "source"], as_index=False)["is_anomaly"].mean()
    fig = px.line(
        rate,
        x="date",
        y="is_anomaly",
        color="source",
        markers=True,
        color_discrete_sequence=[palette["amber"], palette["cyan"]],
    )
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font_color=palette["text"],
        yaxis_tickformat=".1%",
        legend=dict(orientation="h"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=340,
    )
    return fig


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------

app = Dash(
    __name__,
    title="ForgeIQ",
    update_title="ForgeIQ…",
    suppress_callback_exceptions=True,
)
server = app.server


def _layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="page", data="overview"),
            html.Header(
                [
                    html.Div(
                        [
                            html.Span(
                                "FORGE",
                                style={
                                    "fontWeight": "800",
                                    "letterSpacing": "0.12em",
                                },
                            ),
                            html.Span(
                                "IQ",
                                style={
                                    "fontWeight": "800",
                                    "color": C["amber"],
                                    "letterSpacing": "0.12em",
                                },
                            ),
                        ],
                        style={"fontSize": "18px", "display": "flex", "gap": "2px"},
                    ),
                    html.Div(
                        "Manufacturing Intelligence · Data Quality",
                        style={
                            "color": C["muted"],
                            "fontSize": "12px",
                            "marginLeft": "14px",
                        },
                    ),
                    html.Nav(
                        [
                            html.Button(
                                label,
                                id={"type": "nav", "index": key},
                                n_clicks=0,
                                style=_nav_btn_style(key == "overview"),
                            )
                            for key, label in NAV
                        ],
                        style={"display": "flex", "gap": "8px", "marginLeft": "auto"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "padding": "14px 24px",
                    "background": C["panel"],
                    "borderBottom": f"2px solid {C['amber']}",
                },
            ),
            html.Div(
                id="content",
                style={
                    "padding": "20px 24px",
                    "maxWidth": "1440px",
                    "margin": "0 auto",
                },
            ),
        ],
        style={
            "background": (
                f"repeating-linear-gradient(135deg, {C['bg']}, {C['bg']} 40px, "
                "#151A21 40px, #151A21 80px)"
            ),
            "minHeight": "100vh",
            "fontFamily": "'Segoe UI', system-ui, sans-serif",
            "color": C["text"],
        },
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
    Output({"type": "nav", "index": "overview"}, "style"),
    Output({"type": "nav", "index": "quality"}, "style"),
    Output({"type": "nav", "index": "health"}, "style"),
    Output({"type": "nav", "index": "dq"}, "style"),
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
    return key, *[_nav_btn_style(key == k) for k, _ in NAV]


@callback(
    Output("content", "children"),
    Input("page", "data"),
)
def _render(page: str):
    builder = PAGES.get(page, _page_overview)
    return builder()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
