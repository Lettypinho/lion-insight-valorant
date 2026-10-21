# SPEC 001 — Ingestão de Dados

## Objetivo
Processar os arquivos JSON fornecidos pelo Hackathon e transformá-los em uma estrutura normalizada para análise.

## Requisitos
- RF-001 — localizar todos os JSONs do dataset.
- RF-002 — carregar o conteúdo e tratar arquivos inválidos.
- RF-003 — extrair competição, classificatória, número da partida, data, equipes, placar e mapa quando disponíveis no nome/caminho.
- RF-004 — gerar representação normalizada de partida.
- RF-005 — permitir acesso aos rounds e eventos necessários.
- RF-006 — relacionar Red/Blue às equipes reais.
- RF-007 — gerar relatório de ingestão.

## Critérios de aceite
- Todos os arquivos válidos são processados.
- Arquivos inválidos são contabilizados.
- É possível consultar equipe → partidas → rounds.
- O inventário final pode atualizar `dataset.md`.
