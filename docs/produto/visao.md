# Visão do Produto

## 1. Contexto

O Hackathon disponibilizou um conjunto de partidas reais de uma competição de VALORANT. Esses arquivos contêm informações detalhadas sobre partidas, jogadores, rounds, eliminações, dano, economia e situações relacionadas aos objetivos do jogo.

Esse volume de informação permite ir além de estatísticas tradicionais como KDA, headshot percentage e taxa de vitória.

O desafio do Lion Insight é transformar eventos registrados nos rounds em uma leitura tática que ajude uma equipe a entender como está jogando e quais comportamentos contribuem para suas vitórias e derrotas.

## 2. Problema

Estatísticas isoladas descrevem o que aconteceu, mas nem sempre ajudam a explicar por que aconteceu.

Uma equipe pode saber quantas eliminações conseguiu ou quantos rounds venceu, mas ainda precisar responder perguntas como:

- O time converte vantagem depois de conseguir a primeira eliminação?
- O que acontece quando começa o round em desvantagem?
- As eliminações sofridas são rapidamente tradadas?
- O time consegue manter vantagens numéricas?
- Como se comporta em situações de pós-plant?
- Qual é sua eficiência em retakes?
- A condição econômica interfere significativamente no resultado?
- Esse comportamento é comum ou está acima/abaixo do padrão observado na competição?

O problema central é transformar dados brutos em informações úteis para tomada de decisão competitiva.

## 3. Proposta de solução

Desenvolver uma ferramenta de análise tática pós-partida voltada principalmente para:

- jogadores;
- IGLs;
- coaches;
- analistas;
- equipes competitivas de VALORANT.

A solução será estruturada em duas frentes complementares.

### 3.1 Análise da equipe

O usuário seleciona uma equipe e visualiza como ela se comporta nas partidas disponíveis.

A análise deve identificar padrões relacionados a situações relevantes de jogo, como:

- first kill;
- first death;
- conversão de vantagem;
- recuperação de desvantagem;
- trades;
- pós-plant;
- retake;
- economia;
- ataque;
- defesa.

O objetivo não é apenas exibir métricas, mas transformar essas métricas em pontos fortes e pontos de atenção.

### 3.2 Análise da competição

As partidas da competição também serão utilizadas como base de referência.

A mesma métrica calculada para uma equipe poderá ser comparada com o comportamento observado no restante da competição.

Exemplo:

> Equipe X — Conversão após First Kill: 74%  
> Referência da competição: 65%

A comparação deve ajudar o usuário a entender se determinado comportamento está acima, próximo ou abaixo do padrão observado no campeonato.

Quando houver amostra suficiente, a referência poderá ser contextualizada por mapa, lado ou classificatória.

## 4. Diferencial

O diferencial do Lion Insight é não parar na estatística.

Em vez de apresentar somente:

> Conversão após First Kill: 74%

A solução deve ser capaz de apresentar algo como:

> A equipe apresenta boa capacidade de conversão quando consegue a primeira eliminação, acima da referência da competição. Entretanto, apresenta dificuldade para se recuperar quando sofre a primeira morte.

Sempre que possível, o usuário deve conseguir abrir as partidas e rounds que sustentam aquela análise.

O fluxo central do produto é:

Dados da partida  
→ Contexto dos rounds  
→ Métricas  
→ Padrões  
→ Comparação  
→ Diagnóstico  
→ Evidências

## 5. Proposta de valor

> Transformar dados brutos das partidas em informações que ajudem uma equipe a entender como está jogando, identificar padrões e descobrir onde pode melhorar.

## 6. Experiência esperada

O usuário deve conseguir:

1. visualizar o contexto da competição;
2. selecionar uma equipe;
3. consultar suas partidas;
4. visualizar métricas táticas;
5. comparar essas métricas com referências da competição;
6. identificar pontos fortes e pontos de atenção;
7. consultar os rounds que sustentam os insights.

## 7. Objetivo do Hackathon

Entregar um MVP funcional que também sirva como protótipo demonstrável durante o pitch.

O MVP deve provar três coisas:

1. os dados fornecidos podem ser transformados em métricas táticas úteis;
2. o campeonato pode servir como contexto de comparação;
3. as métricas podem ser transformadas em diagnósticos explicáveis.

## 8. Visão futura

Após o Hackathon, a solução poderá evoluir para:

- análises por jogador;
- comparações entre equipes específicas;
- análises espaciais;
- visualizações de posicionamento;
- heatmaps;
- métricas avançadas de economia;
- evolução histórica;
- suporte a múltiplas competições;
- recomendações táticas mais avançadas.

Essas evoluções não fazem parte automaticamente do MVP.
