# SPEC 002 — Análise da Equipe

## Objetivo
Calcular métricas táticas para uma equipe a partir dos rounds de suas partidas.

## Requisitos
- RF-001 — identificar First Kill.
- RF-002 — calcular First Kill Conversion.
- RF-003 — calcular First Death Recovery.
- RF-004 — identificar trades conforme `metricas.md`.
- RF-005 — calcular pós-plant.
- RF-006 — calcular recuperação defensiva após plant.
- RF-007 — retornar rounds utilizados como evidência.

## Critérios de aceite
- Cada métrica retorna valor, numerador, denominador e evidências.
- Denominador zero é tratado corretamente.
- Há testes com cenários conhecidos.
