# Data Sources — ForgeIQ Phase 1

Três datasets públicos, unificados na Silver em um modelo canônico de fábrica fictícia.

---

## 1. AI4I 2020 Predictive Maintenance

| Campo | Valor |
|---|---|
| Origem | UCI Machine Learning Repository #601 |
| URL | https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset |
| Licença | UCI terms (uso livre para pesquisa/educação) |
| Tipo | Simulação de usinagem (milling), 10.000 observações |
| Granularidade | 1 linha = 1 operação/produto |
| Download | `ingestion/sources/ai4i.py` → `data/raw/ai4i2020.csv` |

### Estrutura (14 colunas originais + metadata Bronze)

| Coluna canônica | Original | Tipo | Unidade |
|---|---|---|---|
| udi | UDI | int | — |
| product_id | Product ID | str | — |
| product_type | Type (L/M/H) | cat | — |
| air_temperature_k | Air temperature [K] | float | K |
| process_temperature_k | Process temperature [K] | float | K |
| rotational_speed_rpm | Rotational speed [rpm] | int | rpm |
| torque_nm | Torque [Nm] | float | Nm |
| tool_wear_min | Tool wear [min] | int | min |
| machine_failure | Machine failure | int 0/1 | — |
| failure_twf/hdf/pwf/osf/rnf | 5 failure modes | int 0/1 | — |

### Limitações

- **Sem timestamps** → event_time sintético na Silver (ordinal → janela documentada no data dictionary).
- **Sem vibration/pressure** → Machine Health usa tool wear no lugar de vibration; pressure só do CMAPSS.
- **Sem machine_id de frota** → cada linha é uma operação; entity resolution mapeia para máquina canônica via regra (ver data dictionary).
- **Sem quantidade produzida, alvo, downtime, manutenção.**
- Sem valores missing no arquivo original (dataset limpo/sintético).

### Papel no ForgeIQ

Sensores + falhas (339 failures, 5 modos) → Machine Health, Failure Count, anomaly detection supervisionada parcial.

### Achado de DQ conhecido (fonte)

Regra `AI4I-CONS-001` (severidade warn): existem ~9 linhas com `machine_failure = 1` sem nenhum flag `failure_*` ativo — inconsistência documentada do dataset original. Demonstração real do módulo DQ na Phase 3.

---

## 2. NASA CMAPSS FD001

| Campo | Valor |
|---|---|
| Origem | NASA Prognostics Center of Excellence (Turbofan Engine Degradation) |
| Espelho estável | Hugging Face `SoyVitou/NASA-C-MAPSS-Turbofan-Engine` / mapr-demos |
| Licença | NASA public domain |
| Tipo | Simulação C-MAPSS, turbofans run-to-failure |
| Granularidade | 1 linha = 1 cycle de 1 unit |
| Download | `ingestion/sources/cmapss.py` → `data/raw/train_FD001.txt` |

### Estrutura

- 20.631 linhas, 100 unidades, 128–362 cycles por unidade
- `unit_id`, `cycle`, 3 operational settings, 21 sensores nomeados (temperaturas °R, pressões psia, speeds rpm)
- Derivados: `rul` (max cycle − cycle), `failed` (último cycle da unidade)

### Limitações

- **Não é chão de fábrica** — é frota de motores turbofan; tratada como “fleet de máquinas” no modelo canônico.
- **Sem produtos, linhas, defeitos, quantities.**
- **Sem downtime/MTTR/preventive×corrective.**
- MTBF derivável (ciclos até failure por unit); downtime só como estimativa documentada.
- Vários sensores constantes em FD001 (settings_3, sensor_1, 5, 10, 16, 18, 19) — úteis pouco para anomaly.

### Papel no ForgeIQ

Frota + série temporal + pressão → Machine Health trends, comparison, failure history, RUL-related analytics.

---

## 3. MFG-004 Quality Control (sample)

| Campo | Valor |
|---|---|
| Origem | Hugging Face `xpertsystems/mfg004-sample` |
| URL | https://huggingface.co/datasets/xpertsystems/mfg004-sample |
| Licença | ver README do repositório HF (sample público) |
| Tipo | Sintético — inspection records QC |
| Granularidade | 1 linha = 1 inspeção |
| Download | `ingestion/sources/mfg004.py` → `data/raw/mfg004_inspection_records.csv` |

### Estrutura (112 colunas; núcleo para Phase 1)

| Grupo | Colunas principais |
|---|---|
| Identidade | inspection_id, work_order_id, part_number, lot_number, inspection_date, inspection_shift |
| Resultado | units_inspected, units_accepted, units_rejected, defects_found_total |
| Defeito | defect_type_primary/secondary, defect_severity_class, defect_cause_category |
| Disposição | disposition ∈ accept, rework, scrap, reject, reinspect, … |
| SPC/CpK | cpk_process_capability_index, control_chart_*, sigma_level_estimated |

### Estatísticas observadas (amostra)

- 3.000 inspeções, 2015-01-03 → 2024-12-30
- FPY global ≈ **90.1%** (accepted/inspected)
- scrap = 61, rework = 304, reject = 141
- 287.747 units inspected, 36.052 defects
- 6 product families; defect types: dimensional, functional, contamination, labelling, …
- Nulos esperados: defect_type_* quando não há defeito; ncr_number/containment quando não há NCR — **não são missing aleatórios**

### Limitações

- **Sem machine_id estável por linha de máquina** no sample enxuto — mapear machine canônica via `part_number`/`work_order` prefix ou hash documentado.
- Disposição não equivale a downtime.
- Sample (3k); full product é comercial.

### Papel no ForgeIQ

Quality Intelligence (FPY, scrap, rework, defects por family/type/severity), Total Production (units_inspected), Factory Overview temporal.

---

## Entity resolution — plano v0

| Fonte | Chave natural | Regra canônica (Silver) |
|---|---|---|
| CMAPSS | unit_id (1–100) | `machine_id = "M" + unit_id:04d` |
| AI4I | product_id (ex: M14860) | prefixo L/M/H → cluster de tipo; máquina canônica = bucket determinístico por `udi % N_fleet` **ou** tratar AI4I como operações da frota CMAPSS com join probabilístico — **decisão na Phase 4** |
| MFG-004 | part_number / work_order | machine canônica via hash estável de `work_order_id` documentado |

Premissa de tempo:

| Fonte | event_time |
|---|---|
| MFG-004 | `inspection_date` (real) |
| CMAPSS | `cycle` → data sintética `2024-01-01 + (cycle-1) days` por unit (documentado) |
| AI4I | ordinal `udi` → mesma janela linear sobre 10k passos (documentado) |

---

## Freshness / periodicidade

Datasets estáticos (snapshot). Freshness DQ = idade do arquivo local vs data de ingestão, não latência de stream.
