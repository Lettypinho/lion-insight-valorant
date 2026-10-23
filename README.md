# Lion Insight

Ferramenta de análise tática pós-partida de VALORANT desenvolvida pela Lion Tech para o Hackathon.

## Proposta

Transformar dados brutos das partidas em informações que ajudem jogadores, IGLs, coaches e analistas a compreender como uma equipe está jogando, identificar padrões, reconhecer pontos fortes e encontrar oportunidades de melhoria.

A solução trabalha em duas frentes complementares:

1. **Análise da equipe** — comportamento, métricas, padrões, pontos fortes, pontos de atenção e rounds que sustentam cada conclusão.
2. **Análise contextual** — uso de toda a base tratada como universo disponível, com filtros opcionais por campeonato/circuito, etapa, mapa e lado. A referência é sempre formada pelos outros times do mesmo recorte.

## Objetivo do Hackathon

Entregar um **MVP funcional** que também sirva como protótipo demonstrável durante o pitch.

O foco não é construir uma plataforma completa, mas provar o núcleo da proposta de valor usando os dados reais fornecidos no Hackathon.

## Stack inicial

- Python
- Streamlit
- Pandas
- Plotly ou Altair, conforme necessidade
- Arquivos JSON fornecidos pelo Hackathon

## Estrutura da documentação

- `docs/constituicao.md` — princípios e regras obrigatórias do projeto.
- `docs/produto/visao.md` — visão do produto.
- `docs/produto/mvp.md` — escopo do MVP.
- `docs/produto/backlog.md` — funcionalidades priorizadas e futuras.
- `docs/pesquisa/dataset.md` — estrutura e limitações dos dados.
- `docs/pesquisa/metricas.md` — definições das métricas táticas.
- `docs/arquitetura/arquitetura.md` — arquitetura técnica.
- `docs/arquitetura/legado.md` — migração do protótipo anterior e divergências pendentes.
- `docs/design/design.md` — diretrizes de UX/UI.
- `specs/` — especificações, planos e tarefas de implementação.

## Estrutura do código

- `src/ingestion/` — leitura dos JSONs, validação e geração das tabelas.
- `src/analytics/` — métricas e referência contextual do recorte.
- `src/insights/` — diagnósticos e rounds de evidência.
- `src/ui/` — interface Streamlit: dados com cache, filtros, componentes, gráficos e uma pasta `tabs/` com um arquivo por aba.
- `app.py` — ponto de entrada da aplicação; só monta a página a partir de `src/ui/`.
- `tests/` — testes e relatórios de conferência.
- `data/input/` — JSONs fornecidos pelo Hackathon.
- `data/processed/` — tabelas geradas pela ingestão.
- `data/reference/armas.csv` — nomes/categorias das armas.
- `data/reference/agentes.csv` — tradução de UUID dos agentes para nome e função.
- `data/reference/armaduras.csv` — tradução de UUID das armaduras para nome.

Os arquivos de `data/reference/` são catálogos estáticos para **tradução de IDs**. Eles não adicionam nenhum dado de partida ao sistema.

## Como rodar

Todos os comandos a partir da raiz do projeto:

```
pip install -r requirements.txt

python src/ingestion/ingest.py         --input data/input --output data/processed
python src/ingestion/validate.py       --input data/input --processed data/processed
python src/ingestion/build_features.py --processed data/processed

python tests/test_metrics.py
python tests/test_objectives_matches.py
python tests/test_players.py
python tests/test_kill_types.py
python tests/test_references.py
python tests/smoke_report.py --team ufmt_turuna

python -m streamlit run app.py
```

O app abre em http://localhost:8501 e trabalha com a **base completa tratada**. Lê de `data/processed/` os arquivos `team_round.csv`, `player_round.csv`, `kill_events.csv` e `map_silhouette.csv` (gerados por `build_features.py`) e `dim_player.csv`, `fact_kill_position.csv` e `fact_objective_position.csv` (gerados por `ingest.py`). Para abrir direto em uma equipe: `http://localhost:8501/?team=azure_bears_golden`.

Observações sobre o tema do Streamlit:

- Não definir `[theme] base/primaryColor` direto no `.streamlit/config.toml`, pois isso desliga o tema automático e o gráfico fica ilegível no modo escuro. Usar `[theme.light]` e `[theme.dark]`.
- Não usar seletor CSS genérico (`[class*="st-"]`) para trocar a fonte, pois isso quebra os ícones do Streamlit.

## Fluxo principal

Dados da partida  
→ Contexto dos rounds  
→ Métricas  
→ Comparação  
→ Diagnóstico  
→ Evidências

## Regra principal

Nenhum insight pode ser apresentado sem ser derivado de dados disponíveis e rastreável até as métricas e rounds que o sustentam.
