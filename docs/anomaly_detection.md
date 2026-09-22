# Phase 5 — Anomaly Detection (IsolationForest)

Phase 5.5 do roadmap (após DQ/Silver/Gold, antes do dashboard Machine Health).

## Design

- **Modelo:** `sklearn.ensemble.IsolationForest` (n_estimators=200, contamination=0.05, seed=42)
- **Features AI4I:** air_temperature_k, process_temperature_k, rotational_speed_rpm, torque_nm, tool_wear_min
- **Features CMAPSS:** todas as colunas numéricas de sensores/settings da tabela Silver (exclui ids, cycle, rul, failed, metadata)
- **Saída:** `anomaly_score` (decision_function — menor = mais anômalo) + `is_anomaly` (0/1) + `model`/`model_version`
- **Persistência:** `data/silver/fact_anomaly_{ai4i,cmapss}.parquet`
- **Gold:** `fact_anomaly` (união com `source`) + KPIs `anomaly_rate`, `anomaly_events` em `kpi_summary`

## Limitações v0

- contamination fixa 5% (não calibrada por linha de produto)
- treino full-batch (não online)
- não usa labels de `machine_failure` para validação supervisionada (fase futura: precision@k vs failures)
