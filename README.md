# Lion Insight

Ferramenta de análise tática pós-partida de VALORANT desenvolvida pela Lion Tech para o Hackathon.

## Proposta

Transformar dados brutos das partidas em informações que ajudem jogadores, IGLs, coaches e analistas a compreender como uma equipe está jogando, identificar padrões, reconhecer pontos fortes e encontrar oportunidades de melhoria.

A solução trabalha em duas frentes complementares:

1. **Análise da equipe** — comportamento, métricas, padrões, pontos fortes, pontos de atenção e rounds que sustentam cada conclusão.
2. **Análise da competição** — uso das partidas do campeonato como referência para contextualizar o desempenho de cada equipe.

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
- `docs/design/design.md` — diretrizes de UX/UI.
- `specs/` — especificações, planos e tarefas de implementação.

## Fluxo principal

Dados da partida  
→ Contexto dos rounds  
→ Métricas  
→ Comparação  
→ Diagnóstico  
→ Evidências

## Regra principal

Nenhum insight pode ser apresentado sem ser derivado de dados disponíveis e rastreável até as métricas e rounds que o sustentam.
