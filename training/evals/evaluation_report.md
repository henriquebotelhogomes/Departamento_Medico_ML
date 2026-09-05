# Relatório de Avaliação Sistemática de LLM Médica (Evals)

> **Modelo Avaliado:** `deterministic-local`  
> **Total de Casos de Teste:** 30  

## Métricas Consolidadas

| Métrica | Resultado Obtido | Meta Regulamentar | Status |
| :--- | :--- | :--- | :--- |
| **Concordância CID-10** | **100.0%** | >= 98.0% | APROVADO |
| **Completude das 5 Seções** | **100.0%** | 100.0% | APROVADO |
| **Taxa de Alucinação** | **0.0%** | 0.0% | APROVADO |
| **Fidelidade ao Human-in-the-Loop** | **100.0%** | 100.0% | APROVADO |
| **Latência Média** | **0.0 ms** | < 2500 ms | DENTRO DO SLA |
| **Consumo Total de Tokens** | **0** | Monitoramento | Telemetria |
| **Custo Total Estimado** | **$0.00000 USD** | FinOps Control | Eficiência |

## Detalhamento dos Casos Avaliados

| Caso ID | Categoria | CID-10 | Seções | Alucinação | Latência |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `COVID-01-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.85 ms |
| `COVID-02-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.05 ms |
| `COVID-03-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.02 ms |
| `COVID-04-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.02 ms |
| `COVID-05-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.01 ms |
| `COVID-06-TYP` | typical_covid | Match | 5/5 | Nenhuma | 0.01 ms |
| `NORM-01-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.01 ms |
| `NORM-02-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.01 ms |
| `NORM-03-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.02 ms |
| `NORM-04-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.02 ms |
| `NORM-05-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.01 ms |
| `NORM-06-TYP` | typical_normal | Match | 5/5 | Nenhuma | 0.02 ms |
| `VIRAL-01-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.02 ms |
| `VIRAL-02-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.01 ms |
| `VIRAL-03-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.02 ms |
| `VIRAL-04-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.02 ms |
| `VIRAL-05-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.01 ms |
| `VIRAL-06-TYP` | typical_viral | Match | 5/5 | Nenhuma | 0.02 ms |
| `BACT-01-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.02 ms |
| `BACT-02-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.02 ms |
| `BACT-03-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.01 ms |
| `BACT-04-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.01 ms |
| `BACT-05-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.02 ms |
| `BACT-06-TYP` | typical_bacterial | Match | 5/5 | Nenhuma | 0.02 ms |
| `AMB-01-UNCERTAINTY` | ambiguity | Match | 5/5 | Nenhuma | 0.01 ms |
| `AMB-02-UNCERTAINTY` | ambiguity | Match | 5/5 | Nenhuma | 0.02 ms |
| `AMB-03-UNCERTAINTY` | ambiguity | Match | 5/5 | Nenhuma | 0.02 ms |
| `HITL-01-OVERRIDE` | human_override | Match | 5/5 | Nenhuma | 0.02 ms |
| `HITL-02-OVERRIDE` | human_override | Match | 5/5 | Nenhuma | 0.02 ms |
| `HITL-03-OVERRIDE` | human_override | Match | 5/5 | Nenhuma | 0.01 ms |