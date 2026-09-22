# Data Dictionary — ForgeIQ (v0)

Granularidade, colunas canônicas e premissas derivadas. Atualizar a cada mudança de schema Silver.

---

## 1. `raw.ai4i2020` / Bronze AI4I

| Coluna | Tipo | Nullable | Descrição | Unidade |
|---|---|---|---|---|
| udi | int | N | Unique ID 1..10000 | — |
| product_id | str | N | Ex: M14860 | — |
| product_type | cat(L/M/H) | N | Variante de qualidade do produto | — |
| air_temperature_k | float | N | Temperatura do ar | K |
| process_temperature_k | float | N | Temperatura de processo | K |
| rotational_speed_rpm | int | N | Velocidade rotacional | rpm |
| torque_nm | float | N | Torque | Nm |
| tool_wear_min | int | N | Desgaste de ferramenta | min |
| machine_failure | int(0/1) | N | Falha na observação | — |
| failure_twf | int(0/1) | N | Tool wear failure | — |
| failure_hdf | int(0/1) | N | Heat dissipation failure | — |
| failure_pwf | int(0/1) | N | Power failure | — |
| failure_osf | int(0/1) | N | Overstrain failure | — |
| failure_rnf | int(0/1) | N | Random failure | — |
| source | str | N | `ai4i_2020` | — |
| batch_id | str | N | Lote de ingestão | — |
| ingestion_timestamp | ts | N | UTC ISO8601 | — |

**Premissa temporal:** AI4I não tem timestamp. Na Silver, `event_time = t0 + (udi-1) * Δt` com `t0 = 2024-01-01`, `Δt = 5 min` (janela ~34 dias) — **apenas para ordenação/trends**, não é tempo real.

---

## 2. `raw.cmapss_fd001` / Bronze CMAPSS

| Coluna | Tipo | Nullable | Descrição |
|---|---|---|---|
| unit_id | int | N | Identificador da unidade (1–100) |
| cycle | int | N | Cycle operacional (tempo relativo) |
| setting_1..3 | float | N | Operational settings |
| total_temp_* / pressure_* / *_speed_* | float | N | 21 sensores nomeados |
| rul | int | N | Derived: max(cycle por unit) − cycle |
| failed | int(0/1) | N | Derived: último cycle da unit |

**Unidades:** temperaturas °R, pressões psia, speeds rpm (colunas já renomeadas na ingestão).

**Premissa temporal:** `event_time = 2024-01-01 + (cycle − 1) days` por unit (ordenar/trends).

**Sensores constantes em FD001:** setting_3, sensor 1, 5, 10, 16, 18, 19 — candidatos a drop na feature engineering.

---

## 3. `raw.mfg004` / Bronze MFG-004 (núcleo)

| Coluna | Tipo | Nullable | Descrição |
|---|---|---|---|
| inspection_id | str | N | PK lógico |
| work_order_id | str | N | Ordem de produção |
| part_number | str | N | Peça |
| product_family | cat | N | automotive, aerospace, … |
| lot_number | str | N | Lote |
| inspection_date | date | N | Data da inspeção |
| inspection_shift | cat | day/evening/night | Turno |
| disposition | cat | N | accept, rework, scrap, reject, … |
| units_inspected | int | N | Amostra inspecionada |
| units_accepted | int | N | Aceitos |
| units_rejected | int | N | Rejeitados |
| defects_found_total | int | N | Total de defeitos |
| defect_type_primary | str | **Y** | NULL quando sem defeito classificado |
| defect_severity_class | cat | Y | critical/major/minor/incidental |
| defect_cause_category | cat | Y | Ishikawa 6M |
| cpk_process_capability_index | float | Y | Índice Cpk |
| sigma_level_estimated | float | Y | Sigma level |
| source / batch_id / ingestion_timestamp | | N | Bronze metadata |

**Nulos estruturais (esperados):** defect_type_*, ncr_number, containment_action_taken, defect_cause_* — significam “sem defeito/NCR”, não data quality failure de completeness nesses campos (regra DQ usa semantic null).

---

## 4. KPIs derivados (Gold — especificação)

| KPI | Fórmula | Fonte | Status |
|---|---|---|---|
| Total Production | Σ units_inspected | MFG-004 | pronto |
| Defect Rate | Σ units_rejected / Σ units_inspected | MFG-004 | pronto |
| First Pass Yield | Σ units_accepted / Σ units_inspected | MFG-004 | pronto |
| Scrap Rate | inspections(scrap) / total inspections **ou** units em scrap / inspected | MFG-004 | definir grão na Phase 4 |
| Rework Rate | idem para rework | MFG-004 | idem |
| Total Defects | Σ defects_found_total | MFG-004 | pronto |
| Machine Failures | Σ machine_failure (AI4I) + units failed (CMAPSS) | AI4I/CMAPSS | pronto |
| Active Machines | unit_id distinct (CMAPSS) | CMAPSS | pronto |
| Downtime | Σ (janela de reparo fixa após failure/end-of-life) | derivado | **premissa:** repair_window = 8h por evento; documentar sempre como “estimated” |
| MTBF | mean cycles between failures (CMAPSS: vida até failed) | CMAPSS | pronto (em cycles) |
| Utilization | cycles operados / max cycles da frota (proxy) | CMAPSS | proxy documentado |
| Anomaly Score | módulo Phase 5.5 | derivado | futuro |
| DQ Score | média ponderada das 5 dimensões DQ | pipeline DQ | Phase 3 |

**Fora do escopo (sem dado):** Production Target, OEE, Vibration, MTTR, Preventive × Corrective.

---

## 5. Modelo dimensional canônico (Gold — alvo)

```text
dim_machine      -- machine_id, source, unit ref, attributes
dim_product      -- part_number / product_id / family
dim_line         -- MFG line ou proxy (facility/shift como fallback)
dim_date         -- calendar a partir de event_time
dim_defect       -- defect_type, severity, cause
dim_maintenance  -- tipos de evento de falha (failure modes)

fact_sensor_reading  -- machine_id, event_time, metrics (AI4I/CMAPSS)
fact_production      -- date/line, units_inspected/accepted (MFG-004)
fact_quality         -- inspection grain + defect FKs
fact_maintenance     -- failure events + downtime derivado
```
