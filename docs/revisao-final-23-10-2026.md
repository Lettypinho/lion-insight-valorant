# Revisão final — 23/10/2026

## Resultado da comparação com o último commit recebido

A versão do último commit foi comparada arquivo a arquivo com a versão atual do Lion Insight.

- Os dois repositórios possuem os mesmos 336 JSONs em `data/input/`.
- Não existe arquivo de código, teste ou documentação presente no último commit que esteja ausente na versão atual.
- A versão atual preserva toda a implementação do último commit e acrescenta:
  - tradução de IDs de agentes e suas funções;
  - tradução de IDs de armaduras;
  - validação automática dos catálogos de referência;
  - agentes e funções nas análises de jogadores;
  - filtros organizados por campeonato/circuito, etapa, mapa e lado;
  - base completa como contexto padrão quando nenhum filtro é escolhido;
  - explicações mais claras para referência, métricas, diagnósticos e evidências;
  - nomenclatura da interface simplificada para demonstração.

## Estado validado da base

- 336 partidas
- 6.618 rounds
- 13.236 registros time x round
- 66.180 registros jogador x round
- 46.371 eventos de abate sobre adversários
- 68 times
- 411 jogadores
- 28 agentes usados na base, todos traduzidos
- 3 armaduras usadas na base, todas traduzidas
- 20 armas usadas em `player_round.csv`, todas traduzidas

## Validação técnica

Executado antes da entrega:

```bash
python -m pytest -q
```

Resultado: **22 testes aprovados**.

Também foi executado `python -m compileall` sobre `app.py`, `src/` e `tests/` sem erro de sintaxe.

## Fluxo recomendado para a demonstração

1. Abra o Lion Insight e escolha uma equipe com boa quantidade de partidas.
2. Comece sem filtros para explicar que a base completa é o universo disponível.
3. Mostre a Visão geral e explique um ponto forte ou ponto de atenção.
4. Compare o valor do time com a referência e destaque a diferença em pontos percentuais.
5. Abra as Evidências e mostre os rounds reais que sustentam o diagnóstico.
6. Mostre Jogadores para demonstrar agentes, funções e métricas individuais.
7. Use Partidas ou Mapa tático como aprofundamento visual, sem desviar do fluxo principal.
8. Termine reforçando o diferencial: o sistema não entrega apenas estatísticas; ele conecta métrica, contexto, diagnóstico e evidência.

## Antes de gravar/enviar

- Rodar `python -m streamlit run app.py` no computador da equipe.
- Conferir visualmente filtros, gráficos, tabelas e mapa tático.
- Escolher previamente a equipe e o diagnóstico que serão usados no pitch.
- Evitar navegar de forma improvisada entre muitas abas durante o vídeo.
- Não afirmar que os diagnósticos são causalidade; apresentar como padrões/indícios encontrados nos dados pós-partida.
