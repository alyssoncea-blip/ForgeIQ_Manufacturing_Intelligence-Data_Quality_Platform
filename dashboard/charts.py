"""Shared chart builders for ForgeIQ dashboard."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html


def html_card(label: str, value: str, color: str, palette: dict) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"color": palette["muted"], "fontSize": "12px"}),
            html.Div(
                value,
                style={
                    "color": color,
                    "fontSize": "26px",
                    "fontWeight": "700",
                    "marginTop": "4px",
                },
            ),
        ],
        style={
            "background": palette["panel"],
            "border": f"1px solid {palette['stroke']}",
            "borderRadius": "12px",
            "padding": "14px 16px",
        },
    )


def quality_kpi_row(kmap: dict, palette: dict) -> list:
    metrics = [
        ("FPY", kmap.get("first_pass_yield"), "{:.1%}", palette["cyan"]),
        ("Defect rate", kmap.get("defect_rate"), "{:.2%}", palette["red"]),
        ("Scrap rate", kmap.get("scrap_rate"), "{:.1%}", palette["amber"]),
        ("Failures", kmap.get("machine_failures_ai4i"), "{:,.0f}", palette["amber"]),
        (
            "Downtime h",
            kmap.get("downtime_hours_estimated"),
            "{:,.0f}",
            palette["muted"],
        ),
    ]
    cards = []
    for label, row, fmt, color in metrics:
        value = "—" if row is None else fmt.format(row.value)
        status = "" if row is None or getattr(row, "status", "ok") == "ok" else " · est"
        cards.append(html_card(label, value + status, color, palette))
    return cards


def anomaly_overview_card(anomaly: pd.DataFrame, palette: dict) -> go.Figure:
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
        legendOrientation="h",
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
    )
    return fig


def cmapss_health_card(cmapss: pd.DataFrame, palette: dict) -> go.Figure:
    """Mean RUL by cycle for a sample of units."""
    sample = sorted(cmapss["unit_id"].unique())[:20]
    sub = cmapss[cmapss["unit_id"].isin(sample)]
    agg = sub.groupby("cycle", as_index=False)["rul"].mean()
    fig = go.Figure(
        go.Scatter(
            x=agg["cycle"],
            y=agg["rul"],
            mode="lines",
            line=dict(color=palette["cyan"], width=2),
            fill="tozeroy",
            fillcolor="rgba(77, 208, 225, 0.12)",
        )
    )
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font_color=palette["text"],
        xaxis_title="Cycle",
        yaxis_title="Mean RUL",
        margin=dict(t=10, b=10, l=10, r=10),
        height=340,
    )
    return fig


def failure_modes_card(maint: pd.DataFrame, palette: dict) -> go.Figure:
    modes = (
        maint[maint["event_type"] == "ai4i_failure"]["failure_modes"]
        .fillna("unknown")
        .value_counts()
        .head(6)
    )
    fig = px.bar(
        x=modes.values,
        y=modes.index,
        orientation="h",
        labels={"x": "Failures", "y": ""},
        color_discrete_sequence=[palette["amber"]],
    )
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font_color=palette["text"],
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
    )
    return fig


def line_fpy_card(production: pd.DataFrame, palette: dict) -> go.Figure:
    prod = production.sort_values("date")
    fig = px.line(
        prod,
        x="date",
        y="first_pass_yield",
        color="line_id",
        markers=True,
        color_discrete_sequence=[palette["cyan"], palette["amber"], palette["green"]],
    )
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font_color=palette["text"],
        yaxis_tickformat=".1%",
        legendOrientation="h",
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
    )
    return fig


def dq_overview_card(report: dict, palette: dict) -> go.Figure:
    tables = list(report.get("tables", {}))
    scores = [report["tables"][t]["dq_score_error_rules"] for t in tables]
    fig = go.Figure(
        go.Bar(
            x=tables,
            y=scores,
            marker_color=palette["green"],
            text=[f"{s:.2f}" for s in scores],
            textposition="outside",
        )
    )
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font_color=palette["text"],
        yaxis=dict(range=[0, 1.1]),
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
    )
    return fig
