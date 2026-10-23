# Atualização de integração — 22/10/2026

Esta atualização foi aplicada sobre o repositório com a base completa já tratada pela equipe.

## O que foi preservado

- 336 partidas da base completa;
- 6.618 rounds;
- 68 equipes;
- 411 jogadores;
- ingestão e tabelas tratadas existentes;
- métricas, diagnósticos, mapa tático, partidas, armas e evidências já implementados.

Nenhuma competição ou etapa foi removida. Os filtros da interface apenas definem o recorte de análise.

## O que foi acrescentado

### Tradução de IDs

- `data/reference/agentes.csv`;
- `data/reference/armaduras.csv`;
- agente, função e armadura adicionados a `player_round.csv`;
- validação automática para impedir UUID usado na base sem tradução.

Os catálogos públicos são utilizados somente para traduzir IDs estáticos. Dados de desempenho continuam vindo exclusivamente
das partidas fornecidas pela organização.

### Experiência da interface

A barra lateral foi reorganizada em:

1. Quem analisar: time e jogador;
2. Contexto: campeonato/circuito, etapa, mapa e lado.

Sem filtro de contexto, a aplicação usa a base completa. A referência é formada pelos outros times do mesmo recorte.

Outras melhorias:

- abas renomeadas para linguagem mais direta;
- explicação rápida no início da Visão geral;
- quantidade de times/partidas que formam a referência visível no cabeçalho;
- coluna “O que mede” nas tabelas de métricas;
- agentes e funções exibidos no elenco;
- agente principal aparece no seletor de jogador;
- nomes de competição formatados para leitura;
- metodologia explica claramente diferença entre dados de partida e catálogos de IDs.

## Validações

`src/ingestion/validate.py` foi executado sobre a base completa e retornou **RESULTADO: TUDO OK**.

`src/ingestion/build_features.py` foi executado novamente e validou:

- `team_round.csv`: 13.236 linhas;
- `player_round.csv`: 66.180 linhas;
- 28 agentes utilizados, todos traduzidos;
- 3 armaduras utilizadas, todas traduzidas;
- itens de arma/faca presentes na base com nomes resolvidos.

Foram adicionados dois testes para os catálogos de agentes e armaduras, totalizando 22 testes coletados no projeto.

## Como executar

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Para reconstruir as features a partir das tabelas tratadas:

```bash
python src/ingestion/build_features.py --processed data/processed
```
