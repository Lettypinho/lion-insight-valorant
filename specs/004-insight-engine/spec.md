# SPEC 004 — Motor de Insights

## Objetivo
Transformar métricas e benchmarks em diagnósticos explicáveis.

## Requisitos
- RF-001 — classificar em ponto forte, próximo da referência ou ponto de atenção.
- RF-002 — não gerar diagnóstico forte com amostra insuficiente.
- RF-003 — informar métrica, valor, referência, diferença, amostra, interpretação e rounds.
- RF-004 — utilizar regras determinísticas no MVP.

## Critérios de aceite
- O mesmo conjunto de métricas gera a mesma classificação.
- Amostras insuficientes são sinalizadas.
- Todo insight possui evidência.
