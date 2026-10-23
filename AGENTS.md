# AGENTS.md

## Objetivo

Este arquivo define como agentes de IA devem trabalhar neste repositório.

## Idioma

- Toda documentação deve ser escrita em português.
- Mensagens de interface destinadas ao usuário devem ser escritas em português.
- Nomes técnicos do código podem permanecer em inglês quando forem convenções comuns do ecossistema Python.
- Não traduzir nomes de diretórios técnicos como `src`, `data`, `tests` e `specs`.

## Fonte de verdade

Antes de implementar qualquer funcionalidade, consultar:

1. `docs/constituicao.md`
2. `docs/produto/mvp.md`
3. `docs/pesquisa/dataset.md`
4. `docs/pesquisa/metricas.md`
5. A `spec.md` correspondente à funcionalidade

## Regras obrigatórias

- Não inventar campos que não existam nos dados.
- Não inventar métricas sem definição registrada em `metricas.md`.
- Não utilizar dados externos de partidas de VALORANT.
- Não implementar funcionalidades fora do escopo do MVP sem solicitação explícita.
- Todo insight deve ser reproduzível a partir dos dados.
- Toda comparação deve informar qual referência foi utilizada. A base completa é o padrão; filtros apenas recortam a análise e nunca eliminam dados da fonte.
- Toda métrica percentual deve manter também numerador, denominador e tamanho da amostra.
- Amostras pequenas devem ser sinalizadas.
- Priorizar simplicidade e entrega do MVP.
- Evitar abstrações, camadas e dependências desnecessárias.

## Processo de desenvolvimento

Para cada especificação:

1. Ler `spec.md`.
2. Verificar `plan.md`.
3. Executar as tarefas de `tasks.md`.
4. Implementar em incrementos pequenos.
5. Validar com dados reais.
6. Atualizar a documentação caso alguma hipótese sobre o dataset seja confirmada ou refutada.
7. Marcar tarefas concluídas somente após validação.

## Testes

As métricas devem ser testadas com casos pequenos e previsíveis antes de serem executadas sobre toda a base.

Sempre que possível, criar testes para:

- identificação da primeira eliminação;
- cálculo de conversão;
- identificação de trades;
- pós-plant;
- retake;
- agregação por equipe;
- agregação por competição;
- tratamento de amostras vazias.

## Princípio

A IA deve ajudar a entregar o MVP no prazo, e não aumentar o escopo do projeto.
