# Escopo do MVP

## 1. Objetivo

Definir o menor conjunto de funcionalidades capaz de provar a proposta de valor do Lion Insight durante o Hackathon.

O MVP deve ser funcional e usar os JSONs reais fornecidos pela organização.

## 2. Resultado esperado

Ao final, deve ser possível executar a aplicação, selecionar uma equipe e demonstrar:

- quais partidas dela existem na base;
- como ela se comporta em algumas situações táticas;
- como esse desempenho se compara à competição;
- quais diagnósticos podem ser extraídos;
- quais rounds sustentam esses diagnósticos.

## 3. Caminho crítico

JSONs  
→ Ingestão  
→ Normalização  
→ Métricas  
→ Benchmark  
→ Insights  
→ Streamlit  
→ Pitch

## 4. Funcionalidades obrigatórias

### MVP-01 — Carregar os dados
A aplicação deve processar os arquivos JSON fornecidos.

### MVP-02 — Identificar contexto da competição
A aplicação deve identificar, quando disponível nos arquivos e nomes dos arquivos:
- classificatória;
- partida;
- data;
- equipes;
- placar;
- mapa.

### MVP-03 — Selecionar equipe
O usuário deve conseguir escolher uma equipe presente na base.

### MVP-04 — Exibir partidas da equipe
A aplicação deve listar as partidas relacionadas à equipe selecionada.

### MVP-05 — Calcular métricas táticas
Prioridade inicial:
1. conversão após First Kill;
2. recuperação após First Death;
3. Trade Rate ou métrica equivalente de resposta a eliminações;
4. conversão de pós-plant;
5. eficiência de retake.

Economia pode entrar se estiver validada a tempo.

### MVP-06 — Comparar com a competição
Para métricas compatíveis, a aplicação deve calcular uma referência da competição e apresentar a diferença para a equipe selecionada.

### MVP-07 — Gerar insights
A aplicação deve classificar resultados relevantes como:
- ponto forte;
- comportamento próximo da referência;
- ponto de atenção.

### MVP-08 — Mostrar evidências
O usuário deve conseguir consultar os rounds ou partidas utilizados para sustentar pelo menos os principais insights.

### MVP-09 — Interface funcional
A aplicação será demonstrável via Streamlit.

## 5. Funcionalidades desejáveis, mas não obrigatórias

- filtros por mapa;
- filtros por classificatória;
- filtros por ataque/defesa;
- ranking de equipes por métrica;
- percentis;
- visualização de evolução ao longo das partidas;
- resumo da competição;
- página individual de partida.

### Decisão de escopo — visualização espacial (21/10/2026)

Incluídos a pedido do time, por não exigirem calibração nem imagem externa:

- **mapa tático por pontos**: mortes, abates, primeiro duelo e plants da equipe, desenhados sobre uma silhueta formada pelas posições de todos os jogadores registradas na própria base;
- **plants por site**: distribuição e vitória pós-plant por site, comparadas com a referência do mesmo mapa;
- **partidas e rounds**: linha do tempo da partida e detalhe de cada round (sequência de abates, economia, spike e posições).

Heatmaps de densidade e calibração com imagens oficiais continuam fora do MVP.

### Decisão de escopo — análise por jogador (21/10/2026)

Incluída a pedido do time: filtro por jogador da equipe, aba Jogadores (elenco, destaques e insights por jogador)
e nicks na sequência de abates. Métricas definidas em `metricas.md`, seção 16. Os nicks vêm dos JSONs (`gameName`);
o repositório é privado e os dados não são versionados. Confirmar com a organização antes de publicar nicks.

## 6. Fora do MVP

- autenticação;
- cadastro de usuário;
- upload de novos campeonatos;
- banco de dados complexo;
- API pública;
- React separado do Streamlit;
- análise em tempo real;
- integração com cliente do VALORANT;
- scraping;
- APIs externas de partidas;
- heatmaps completos;
- calibração espacial dos mapas e uso de imagens oficiais de mapa;
- análise avançada de habilidades;
- inteligência artificial generativa como dependência central;
- sistema completo de chaveamento sem fonte confiável de bracket.

## 7. Critério de sucesso

O MVP é considerado funcional quando:

1. processa a base real;
2. permite selecionar ao menos uma equipe;
3. calcula corretamente as métricas escolhidas;
4. compara com uma referência da competição;
5. apresenta pelo menos dois insights explicáveis;
6. permite abrir evidências em nível de round;
7. pode ser demonstrado de ponta a ponta durante o pitch.

## 8. Estratégia de contingência

Se o tempo ficar crítico:

1. reduzir quantidade de métricas;
2. manter apenas uma visão principal de equipe;
3. preservar benchmark;
4. preservar evidências;
5. usar Figma somente para complementar telas não implementadas.

Nunca sacrificar confiabilidade dos cálculos para aumentar quantidade de funcionalidades.
