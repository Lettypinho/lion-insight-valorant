# Arquitetura do Sistema

## 1. Objetivo

Definir uma arquitetura simples, modular e adequada ao prazo do Hackathon.

## 2. Decisão principal

O MVP utilizará Python e Streamlit.

Não haverá frontend React separado nem API FastAPI no caminho crítico.

## 3. Fluxo

Arquivos JSON  
→ Ingestão  
→ Normalização  
→ Analytics  
→ Benchmark  
→ Insight Engine  
→ Streamlit

## 4. Estrutura técnica sugerida

```text
src/
├── ingestion/
│   ├── loader.py
│   ├── filename_parser.py
│   └── normalizer.py
├── models/
│   ├── match.py
│   ├── round.py
│   └── metric.py
├── analytics/
│   ├── opening.py
│   ├── trades.py
│   ├── objectives.py
│   ├── economy.py
│   └── benchmark.py
├── insights/
│   └── engine.py
└── ui/
    ├── components.py
    └── pages.py

app.py
```

A estrutura pode ser simplificada durante a implementação se houver pouco código.

### 4.1 Estrutura atual

Código migrado do protótipo anterior (ver `docs/arquitetura/legado.md`):

```text
src/
├── ingestion/
│   ├── ingest.py          # JSONs → tabelas CSV (data/processed)
│   ├── validate.py        # confere as tabelas contra os JSONs
│   └── build_features.py  # gera team_round, player_round, kill_events e map_silhouette (CSV)
├── analytics/
│   ├── metrics.py         # métricas, referência da competição, intervalos e análise por mapa
│   ├── players.py         # métricas, elenco e insights por jogador
│   ├── kill_types.py      # tipo de abate (arma, habilidade, ultimate...)
│   ├── weapons.py         # armas: abates/mortes por arma e rendimento com a arma do round
│   ├── objectives.py      # plants por site
│   └── matches.py         # partidas do time e referência de uma partida
├── insights/
│   └── engine.py          # diagnósticos e rounds de evidência
└── ui/
    ├── data.py            # carregamento e cálculo com cache do Streamlit
    ├── formatting.py      # formatação de nomes, porcentagens e números
    ├── styles.py          # CSS pontual
    ├── sidebar.py         # seleção de equipe e filtros
    ├── components.py      # cabeçalho, cartão de insight e tabela de evidências
    ├── charts.py          # gráficos Plotly: comparação, mapa tático, sites e linha do tempo
    └── tabs/
        ├── diagnostico.py # aba Diagnóstico
        ├── jogadores.py   # aba Jogadores
        ├── mapa_tatico.py # aba Mapa tático
        ├── partidas.py    # aba Partidas e rounds
        ├── comparacao.py  # aba Comparação com a competição
        ├── rounds.py      # aba Rounds de evidência
        └── metodologia.py # aba Metodologia

tests/
├── test_metrics.py        # confere as métricas por caminho independente
├── test_objectives_matches.py # casos pequenos: sites, placar, referência de partida, por mapa
├── test_players.py        # casos pequenos por jogador e soma do elenco = equipe
├── test_kill_types.py     # classificação e distribuição por tipo de abate
├── smoke_report.py        # relatório de uma equipe no terminal
└── calibration.py         # taxa de falso alerta com equipes sorteadas

data/
├── input/                 # JSONs fornecidos pelo Hackathon
├── processed/             # CSVs gerados pela ingestão
└── reference/armas.csv    # nomes das armas (catálogo estático, usado por build_features.py)

app.py                     # ponto de entrada: só orquestra a página
```

Diferenças em relação à estrutura sugerida: não há `models/` (os dados circulam como DataFrames do pandas), o benchmark está em `analytics/metrics.py` e cada aba da UI tem seu próprio arquivo em `ui/tabs/`. Nenhum arquivo de `ui/` calcula métricas: todos consomem `analytics` e `insights`. O pipeline gera CSVs em `data/processed/`, que funcionam como o pré-processamento previsto na seção 6.

## 5. Camadas

### 5.1 Ingestion
Responsável por localizar arquivos, abrir JSONs, interpretar nomes, validar estrutura e normalizar dados.

### 5.2 Models
Representações simples das entidades necessárias. Evitar modelagem excessiva.

### 5.3 Analytics
Responsável exclusivamente por cálculos. A interface não deve implementar lógica de métrica.

### 5.4 Benchmark
Calcula referências da competição usando as mesmas regras das métricas de equipe.

### 5.5 Insight Engine
Transforma diferenças relevantes em diagnósticos explicáveis. No MVP, utilizar regras determinísticas.

### 5.6 UI
Streamlit apresenta filtros, métricas, comparações, insights e evidências.

## 6. Persistência

Para o MVP, priorizar processamento em memória com cache do Streamlit.

Se o carregamento integral ficar lento, considerar cache, arquivos Parquet ou pré-processamento.

## 7. Dependências sugeridas

- Python 3.11+
- streamlit
- pandas
- plotly ou altair
- pytest

Adicionar outras dependências somente quando necessárias.

## 8. Testabilidade

Funções analíticas devem receber estruturas de dados e retornar resultados sem depender da interface Streamlit.

## 9. Evolução futura

Após o Hackathon, a mesma camada analítica poderá ser reaproveitada em uma API, frontend dedicado, banco de dados e múltiplas competições.
