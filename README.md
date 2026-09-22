# ForgeIQ — Manufacturing Intelligence & Data Quality Platform

End-to-end data platform for manufacturing analytics: ingestion → Bronze → Data Quality → Silver (entity resolution) → Gold (dbt/DuckDB) → Dash dashboards.

See `projeto.txt` for the full project plan.

## Stack

- **Python** + Pandas + PyArrow
- **Parquet** local (Bronze/Silver/Gold)
- **Pandera** + custom rules (Data Quality)
- **dbt-core + DuckDB** (transformation)
- **Dash + Plotly** (dashboards)
- **pytest + ruff** (tests/lint)

## Datasets (Phase 1)

| Dataset | Role | Source |
|---|---|---|
| AI4I 2020 | Sensors + failures | UCI #601 |
| NASA CMAPSS FD001 | Fleet time series + pressure | NASA |
| MFG-004 sample | Quality (FPY, scrap, rework, defects) | Hugging Face |

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

python -m ingestion.sources.download_all
pytest
```

## Layout

```
ingestion/          # source loaders + download scripts
data_quality/       # rules, schemas, quarantine
transformation/dbt/ # dbt models (DuckDB backend)
analytics/          # KPI computations
anomaly_detection/  # anomaly score module
dashboard/          # Dash app + pages
data/               # raw/bronze/silver/gold (gitignored)
docs/               # architecture, sources, dictionary, DQ
tests/
```
