# ForgeIQ — Prompts para Mockups dos Dashboards

Prompts para gerar imagens de referência dos 4 dashboards da plataforma.

Mockups já gerados: `dashboards_exemples/`

---

## Identidade Visual

**Direção:** sala de controle industrial moderna — aço escuro, sinalização de segurança, dados como instrumentação.

### Paleta

| Papel | Cor | Hex |
|---|---|---|
| Fundo | Grafite | `#12161C` |
| Cards | Aço | `#1C232D` |
| Destaque primário | Âmbar de segurança | `#F5A623` |
| Dados / OK | Ciano de instrumentação | `#4DD0E1` |
| Alarme / falha | Vermelho | `#E5484D` |
| Texto | Cinza claro | `#E8EAED` |

### Tipografia

- **Display:** Barlow Condensed / Oswald (condensada industrial)
- **Corpo:** Inter (sans neutra)
- **Números/dados:** JetBrains Mono / IBM Plex Mono

### Assinatura

- Faixas diagonais de segurança (hazard stripes) como acento fino nos headers
- Micro-labels em caixa-alta com letter-spacing — como painéis de máquina reais

---

## Prompt Base

Usar junto com o prompt de cada dashboard para manter consistência entre as imagens:

```text
Industrial control-room dashboard UI, ForgeIQ manufacturing intelligence platform,
dark graphite background #12161C, steel-toned cards #1C232D, safety amber #F5A623
and instrumentation cyan #4DD0E1 accents, condensed industrial display typography
with IBM Plex Mono numerals, thin hazard-stripe accent on header, uppercase
micro-labels, dense but breathable data layout, 16:10 desktop screenshot, crisp
flat UI design, no photorealism, high fidelity product design mockup
```

---

## 1. Factory Overview

```text
[BASE] Dashboard view "Factory Overview": top row of 7 KPI stat tiles
(Total Production, Production Target, OEE estimated badge, Defect Rate,
Downtime, Machine Failures, Active Machines) with large mono numbers and
small trend arrows; below, grid of charts: production volume over time
area chart, horizontal bar chart production by line, downtime ranking by
machine, defects by line, gauge-style OEE by line, target vs actual bullet
chart; left sidebar navigation with 4 icons; subtle amber accent on primary
KPI, red accent on failure metrics.
```

---

## 2. Machine Health

```text
[BASE] Dashboard view "Machine Health": machine selector dropdown at
top-left showing "M102"; row of sensor gauges/cards (Temperature, Pressure,
Vibration, RPM, Torque, Utilization) with sparklines; prominent anomaly
score card with radial meter reading 0.91 in red-amber; main area with
multi-line sensor trend chart, machine comparison small-multiples, failure
history timeline strip with event markers, anomalies-over-time scatter
highlighted in alarm red; selected machine highlighted in cyan on a
machine-list rail.
```

---

## 3. Quality Intelligence

```text
[BASE] Dashboard view "Quality Intelligence": top KPI row (Defect Rate,
First Pass Yield, Scrap Rate, Rework Rate, Total Defects); charts grid:
stacked defects by product, defects by machine heat-style bars, defects by
production line, defects by type donut, quality trend line over time,
dual-axis chart comparing sensor conditions vs defects; restrained palette —
amber for defect emphasis, cyan for yield/OK states, red only on critical
rates.
```

---

## 4. Data Quality & Maintenance

```text
[BASE] Dashboard view "Data Quality & Maintenance", split into two vertical
sections: left "Data Quality" with a large composite DQ Score radial, five
dimension bars (Completeness, Validity, Uniqueness, Consistency, Freshness),
quarantined/invalid records counters, failed-rules list, DQ trend sparkline;
right "Maintenance" with MTBF, MTTR, Downtime, Failure Count tiles,
preventive vs corrective maintenance split bar, maintenance events timeline;
status colors: cyan healthy, amber warning, red quarantine.
```

---

## Dicas de uso

- Geração de UI sai melhor em **16:10 ou 16:9**, com pedido explícito de "flat UI mockup / screenshot".
- Se o gerador embaralhar números/texto, pedir **"legible English labels"** ou gerar em resolução maior.
- Para manter coerência entre as 4, gerar todas com o **mesmo prompt base** e mudar apenas a parte final.
- Substituir `[BASE]` pelo conteúdo do Prompt Base acima.
