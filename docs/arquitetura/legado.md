# Migração do protótipo anterior

## 1. Objetivo

Registrar como o código do protótipo anterior (antiga pasta `OLD/Hackathon Vava`) foi incorporado à estrutura do Lion Insight e quais pontos ainda divergem da documentação oficial.

## 2. Mapeamento de arquivos

| Origem (`OLD/Hackathon Vava/`) | Destino |
|---|---|
| `etl/ingest.py` | `src/ingestion/ingest.py` |
| `etl/validate.py` | `src/ingestion/validate.py` |
| `etl/build_features.py` | `src/ingestion/build_features.py` |
| `core/metrics.py` | `src/analytics/metrics.py` |
| `core/diagnostics.py` | `src/insights/engine.py` |
| `app/streamlit_app.py` | `app.py` |
| `.streamlit/config.toml` | `.streamlit/config.toml` |
| `requirements.txt` | `requirements.txt` |
| `tests/*.py` | `tests/` |
| `data/input/` | `data/input/` |
| `data/processed/` | `data/processed/` |
| `README.md` | conteúdo distribuído em `README.md`, `docs/pesquisa/dataset.md` e neste arquivo |

Não migrados (removidos junto com a pasta `OLD/`):

- `json/` — cópia idêntica de `data/input/` (conferido arquivo a arquivo).
- `db/` — esquema e carga para PostgreSQL; banco de dados está fora do MVP (`docs/produto/mvp.md`, seção 6).

Alterações de código na migração: apenas imports e caminhos. `tests/test_metrics.py` foi envolvido em uma função para poder ser executado também pelo pytest.

## 3. Validação da migração

Executado sobre a base real em 21/10/2026:

- `ingest.py` → 336 arquivos, 336 partidas, 0 avisos;
- `validate.py` → todas as verificações OK;
- `build_features.py` → todas as verificações OK;
- os 12 CSVs gerados são byte a byte idênticos aos CSVs do protótipo;
- `tests/test_metrics.py` → todas as verificações OK;
- `app.py` abre sem exceções.

## 4. Divergências em relação à documentação

Pontos a decidir pelo grupo antes de considerar as specs concluídas.

### 4.1 Métricas sem definição em `metricas.md`

O protótipo calcula 11 métricas. Cinco delas estão definidas em `metricas.md` (First Kill Conversion, First Death Recovery, Trade, pós-plant, retake). As demais **não** têm definição registrada e, pela regra do `AGENTS.md`, precisam ser documentadas ou retiradas da interface:

| Chave | Métrica | Regra no código |
|---|---|---|
| `fk_rate` | Primeiro abate (taxa) | rounds com First Kill da equipe / rounds com First Kill |
| `isolated_rate` | Mortes isoladas | mortes com aliado vivo mais próximo a mais de 3.000 unidades / mortes com distância calculável |
| `pistol_win` | Rounds de pistola | pistols vencidos / pistols jogados (rounds 1 e 13) |
| `econ_adv_conv` | Conversão de vantagem econômica | loadout da equipe ≥ 1,25 × adversário, exceto pistol |
| `econ_disadv_win` | Vitórias em desvantagem econômica | loadout da equipe ≤ 0,80 × adversário, exceto pistol |
| `plant_rate` | Plant (ataque) | rounds de ataque com plant / rounds de ataque |

Observação: `metricas.md` classifica economia como P1 até que exista uma classificação confiável.

### 4.2 Regras implementadas que precisam ser registradas

- **First Kill**: o código considera a primeira morte causada por um **inimigo**, ignorando suicídio, detonação do spike e teamkill. `metricas.md` fala em "primeira eliminação registrada".
- **Trade**: janela de 5 s (`TRADE_WINDOW_MS`), igual à sugestão de `metricas.md`, ainda não congelada.
- **Retake**: implementado como vitória da defesa após plant adversário, ainda com o nome "Retake (defesa)". `metricas.md` sugere avaliar o nome "vitória defensiva após plant".
- **Benchmark**: a referência é calculada com **todas as outras equipes** (exclui a própria), com os mesmos filtros, agregando oportunidades (não média de porcentagens).
- **Amostra mínima**: o código exige ≥ 15 oportunidades em ≥ 3 partidas, diferença ≥ 3 p.p. e diferença maior que a incerteza (intervalo de 95% com cada partida como unidade). `metricas.md` sugere 10 oportunidades.
- **Classificação extra**: além de ponto forte, próximo da referência e ponto de atenção, o código usa "amostra insuficiente", "sem dados" e insights combinados ("misto").

### 4.3 Funcionalidades além do P0

A aplicação já possui filtros por competição, mapa e lado, percentil entre equipes e download de evidências em CSV. Estão listados como P1/desejáveis no backlog; podem ser mantidos, mas não são caminho crítico.

### 4.4 Dados

- Os CSVs em `data/processed/` somam cerca de 80 MB e os JSONs em `data/input/` cerca de 194 MB. O app só precisa de `data/processed/team_round.csv`.
- O CSV usado pelo app não contém nicks de jogadores, apenas nomes de equipes. Confirmar com a organização antes de expor nicks publicamente.
- Os dados (`data/`) não são versionados no git (ver `.gitignore`). Para rodar, copiar os JSONs para `data/input/` e gerar `data/processed/` com a ingestão.
