"""Shared chart builders for ForgeIQ dashboard."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html


def _layout(fig: go.Figure, palette: dict, **kw) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font=dict(color=palette["text"], family="Inter, sans-serif"),
        legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=14, b=12, l=12, r=12),
        **kw,
    )
    return fig


def kpi_color(metric: str, value, palette: dict) -> str:
    """Status band color: fail=red, danger/warn=amber, OK=cyan."""
    if value is None:
        return palette["muted"]
    v = float(value)
    if metric == "fpy":
        if v >= 0.95:
            return palette["cyan"]
        if v >= 0.90:
            return palette["amber"]
        return palette["red"]
    if metric == "defect_rate":
        if v <= 0.05:
            return palette["cyan"]
        if v <= 0.10:
            return palette["amber"]
        return palette["red"]
    if metric == "scrap_rate":
        if v <= 0.02:
            return palette["cyan"]
        if v <= 0.05:
            return palette["amber"]
        return palette["red"]
    if metric == "anomaly_rate":
        if v <= 0.05:
            return palette["cyan"]
        if v <= 0.10:
            return palette["amber"]
        return palette["red"]
    if metric == "failures":
        return palette["red"]
    if metric == "downtime":
        return palette["amber"]
    if metric == "dq_score":
        if v >= 0.99:
            return palette["cyan"]
        if v >= 0.95:
            return palette["amber"]
        return palette["red"]
    if metric in ("total_production", "units", "max_rul"):
        return palette["cyan"]
    return palette["text"]


def kpi_tile(label: str, value: str, color: str) -> html.Div:
    return html.Div(
        [
            html.Div(label.upper(), className="fiq-label"),
            html.Div(value, className="fiq-value", style={"color": color}),
        ],
        className="fiq-card fiq-kpi",
    )


def html_card(label: str, value: str, color: str, palette: dict) -> html.Div:
    return kpi_tile(label, value, color)


def quality_kpi_row(kpi: dict, palette: dict) -> list:
    """KPI tiles with status-band colors (fail=red, warn=amber, ok=cyan)."""
    metrics = [
        ("FPY", "fpy", kpi.get("fpy"), "{:.1%}"),
        ("Defect rate", "defect_rate", kpi.get("defect_rate"), "{:.2%}"),
        ("Scrap rate", "scrap_rate", kpi.get("scrap_rate"), "{:.1%}"),
        ("Anomaly rate", "anomaly_rate", kpi.get("anomaly_rate"), "{:.2%}"),
        ("Failure events", "failures", kpi.get("failures"), "{:,.0f}"),
        ("Downtime h", "downtime", kpi.get("downtime"), "{:,.0f}"),
        ("Total production", "total_production", kpi.get("total_production"), "{:,.0f}"),
    ]
    cards = []
    for label, metric, value, fmt in metrics:
        text = "—" if value is None else fmt.format(value)
        cards.append(kpi_tile(label, text, kpi_color(metric, value, palette)))
    return cards


def anomaly_rate_figure(rate: pd.DataFrame, palette: dict, height: int = 280) -> go.Figure:
    """Anomaly-rate lines: markers gradient amber->red for values > 0.

    Exactly 0% stays cyan (within normal); any positive rate ramps from
    amber (low) to red (high) across the visible data range.
    """
    if rate.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=palette["panel"],
            height=height,
            annotations=[
                {
                    "text": "No data for current filters",
                    "showarrow": False,
                    "font": {"color": palette["muted"]},
                }
            ],
        )
        return fig

    vmax = float(rate["is_anomaly"].max())
    if vmax <= 0:
        vmax = 0.01
    colorscale = [
        [0.0, palette["cyan"]],
        [1e-9, palette["amber"]],
        [1.0, palette["red"]],
    ]

    fig = go.Figure()
    first = True
    for src, g in rate.groupby("source"):
        g = g.sort_values("date")
        vals = g["is_anomaly"].tolist()
        fig.add_trace(
            go.Scatter(
                x=g["date"],
                y=vals,
                name=str(src),
                mode="lines+markers",
                line=dict(color="rgba(138, 148, 166, 0.45)", width=1.5),
                marker=dict(
                    color=vals,
                    colorscale=colorscale,
                    cmin=0.0,
                    cmax=vmax,
                    size=7,
                    line=dict(width=0),
                    showscale=first,
                    colorbar=(
                        dict(
                            title="rate",
                            tickformat=".0%",
                            outlinewidth=0,
                            bgcolor="rgba(0,0,0,0)",
                            len=0.6,
                        )
                        if first
                        else None
                    ),
                ),
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>rate %{y:.1%}<extra>"
                    + str(src)
                    + "</extra>"
                ),
            )
        )
        first = False

    fig.update_layout(
        paper_bgcolor=palette["panel"],
        plot_bgcolor=palette["panel"],
        font=dict(color=palette["text"], family="Inter, sans-serif"),
        yaxis_tickformat=".1%",
        legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=14, b=12, l=12, r=12),
        height=height,
        xaxis=dict(gridcolor=palette["stroke"], zeroline=False),
        yaxis=dict(
            gridcolor=palette["stroke"],
            zeroline=False,
            rangemode="tozero",
        ),
    )
    return fig


def anomaly_overview_card(anomaly: pd.DataFrame, palette: dict) -> go.Figure:
    a = anomaly.copy()
    if a.empty:
        return anomaly_rate_figure(a, palette, height=280)
    a["date"] = pd.to_datetime(a["event_time"]).dt.date
    rate = a.groupby(["date", "source"], as_index=False)["is_anomaly"].mean()
    return anomaly_rate_figure(rate, palette, height=280)


def cmapss_health_card(cmapss: pd.DataFrame, palette: dict) -> go.Figure:
    """Mean RUL by cycle for a sample of units."""
    if cmapss.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=palette["panel"], height=240)
        return fig
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
    return _layout(
        fig,
        palette,
        xaxis_title="Cycle",
        yaxis_title="Mean RUL",
        height=340,
        xaxis=dict(gridcolor=palette["stroke"], zeroline=False),
        yaxis=dict(gridcolor=palette["stroke"], zeroline=False),
    )


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
        color_discrete_sequence=[palette["red"]],
    )
    return _layout(
        fig,
        palette,
        height=300,
        xaxis=dict(gridcolor=palette["stroke"], zeroline=False),
        yaxis=dict(gridcolor=palette["stroke"], zeroline=False),
    )


def line_fpy_card(production: pd.DataFrame, palette: dict) -> go.Figure:
    prod = production.sort_values("date")
    fig = px.line(
        prod,
        x="date",
        y="first_pass_yield",
        color="line_id",
        markers=True,
        color_discrete_sequence=[palette["cyan"], palette["amber"], palette["text"]],
    )
    return _layout(
        fig,
        palette,
        yaxis_tickformat=".1%",
        height=300,
        xaxis=dict(gridcolor=palette["stroke"], zeroline=False),
        yaxis=dict(gridcolor=palette["stroke"], zeroline=False),
    )


def dq_overview_card(report: dict, palette: dict) -> go.Figure:
    tables = list(report.get("tables", {}))
    scores = [report["tables"][t]["dq_score_error_rules"] for t in tables]
    fig = go.Figure(
        go.Bar(
            x=tables,
            y=scores,
            marker_color=palette["cyan"],
            text=[f"{s:.2f}" for s in scores],
            textposition="outside",
        )
    )
    return _layout(
        fig,
        palette,
        yaxis=dict(range=[0, 1.1], gridcolor=palette["stroke"], zeroline=False),
        height=260,
    )
