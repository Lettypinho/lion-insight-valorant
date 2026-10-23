# Design e Experiência

## 1. Objetivo

Definir a experiência mínima necessária para demonstrar o valor do Lion Insight de forma rápida e compreensível.

## 2. Princípio de experiência

Selecionar equipe  
→ Entender identidade do time  
→ Encontrar ponto forte ou fragilidade  
→ Comparar com a referência do recorte  
→ Abrir evidências

## 3. Tela principal

### Cabeçalho
Exibir nome do produto, equipe selecionada e contexto atual (base completa ou filtros aplicados).

### Filtros principais
Organizar em duas etapas para reduzir carga cognitiva:
1. **Quem analisar** — equipe e, opcionalmente, jogador;
2. **Contexto da análise** — campeonato/circuito, etapa, mapa e lado.

Nenhum filtro de contexto selecionado significa **base completa**. O filtro nunca remove dados da fonte: apenas define o recorte usado na análise e na referência.

## 4. Resumo da equipe

Exibir:
- partidas analisadas;
- rounds analisados;
- vitórias;
- derrotas;
- mapas presentes na amostra.

## 5. Métricas

Cada card deve conter:
- nome da métrica;
- valor da equipe;
- referência do recorte;
- diferença em pontos percentuais;
- tamanho da amostra.

## 6. Insights

Separar claramente:
- pontos fortes;
- pontos de atenção.

A aba Diagnóstico é organizada em:
- **Panorama geral** — insights confirmados somando todos os mapas do recorte, mais a tabela com todos os números;
- **Por mapa** — resumo de cada mapa jogado (partidas, rounds vencidos, pontos confirmados, amostra) e uma aba por mapa com insights, todos os números e os rounds de cada métrica.

Duas leituras convivem:
- **confirmada** — ponto forte ou ponto de atenção, somente quando o critério estatístico é atendido;
- **descritiva** — todas as métricas, inclusive de um mapa com uma única partida, ordenadas da melhor para a pior em relação à referência, sempre com amostra e com aviso de amostra pequena. Uma partida não confirma padrão, mas deve continuar analisável.

### 6.1 Mapa tático

Mapa desenhado com as coordenadas da base (sem imagem). Seletor de mapa e de camada:
mortes do time (trocada, isolada sem troca, sem troca), abates do time, primeiro duelo, plants no ataque e plants sofridos na defesa.
Selecionar pontos lista os rounds correspondentes. Abaixo, plants por site comparados com a referência do mesmo mapa.

### 6.2 Jogadores

Filtro "Jogador" na barra lateral, logo abaixo da equipe. A aba Jogadores mostra o elenco (números descritivos e pontos
confirmados de cada jogador) e, com um jogador escolhido, os insights dele em três grupos: o que está funcionando, o que
precisa de atenção e perfil (métricas que dependem da função). O mapa tático passa a mostrar só o jogador, e a aba de
partidas lista as partidas dele e destaca as linhas dele na sequência de abates.

Abaixo do elenco, **Armas** (do time ou do jogador escolhido), com duas visões: com qual arma mata e morre, e o
rendimento com a arma principal do round (abates por round, sobrevivência, vitória do round) contra os outros com a
mesma arma. Headhunter, Tour de Force e Overdrive aparecem pelo nome. Na sequência de abates, a coluna "Como" mostra o
nome da arma (ou da habilidade, como "Headhunter (habilidade)"); no momento do round, o hover de cada
jogador mostra a arma do round.

Também abaixo do elenco, **Como mata e como morre**: abates e mortes por tipo (arma, habilidade, ultimate, faca, outro), em
quantidade e %, ao lado da referência. Mostra o time ou, com um jogador escolhido, o jogador. Na sequência de abates do
round, a coluna **Como** informa o tipo de cada abate (ex.: "Ultimate", "Habilidade de granada").

### 6.3 Partidas e rounds

Profundidade depois do panorama: escolher uma partida, ver a linha do tempo (round vencido ou perdido, lado) e abrir um round
clicando nele. O round mostra resultado, lado, economia, spike, sequência de abates e as posições das mortes.

**Momentos do round**: abates, plant e defuse num mesmo seletor, em ordem cronológica. Ao clicar numa linha da
sequência de abates (ou escolher no seletor), o mapa mostra a foto daquele instante — quem morreu (✕), quem
abateu/plantou/desarmou (círculo com anel; linha tracejada até a vítima num abate), todos os vivos dos dois times com
nick e um traço curto na direção da mira. O spike (◆) só aparece se já estava plantado naquele instante.
As posições só existem nos instantes de abates, plant e defuse (não é replay contínuo).

**Zoom nos mapas**: roda do mouse aproxima, arrastar move, duplo clique volta ao enquadramento inicial. O zoom feito
pelo usuário é mantido ao trocar de momento; a opção "Aproximar no lance" enquadra automaticamente quem agiu, a vítima
e o spike.

**Cores**: azul = seu time, vermelho = adversário nos mapas de round, como no jogo; na linha do tempo da partida, azul =
round vencido e vermelho = round perdido. O par foi validado para daltonismo (ΔE 21,6 no tema claro, 19,2 no escuro).
Vermelho sempre indica algo negativo para o time (adversário, round perdido, ponto de atenção). O estado (vivo, abateu,
morreu) é dado pelo formato, não por outra cor. No plant e no defuse, quem agiu está em cima do spike: aparece um único
◆ com o nick, com a borda na cor do time dele.

## 7. Evidências

Ao abrir um insight, mostrar tabela com:
- partida;
- round;
- mapa;
- lado;
- contexto;
- resultado.

## 8. Competição

Se houver tempo, incluir uma visão simples da base/competição com classificatórias, equipes, partidas e referências gerais.

Não construir chaveamento visual sem dados confiáveis sobre o bracket.

## 9. Hierarquia visual

Priorizar:
1. insight;
2. comparação;
3. métrica;
4. detalhes.

## 10. Streamlit

Preferir componentes nativos como:
- `st.metric`;
- `st.selectbox`;
- `st.tabs`;
- `st.dataframe`;
- containers;
- columns;
- expander.

Customizações CSS devem ser pontuais.

## 11. Figma

O Figma poderá ser utilizado para definir fluxo, validar hierarquia, alinhar identidade visual e complementar telas que não entrarem no MVP.

## 12. Identidade

A identidade visual deve remeter à Lion Tech e manter relação com a Team Lion, mas a prioridade do Hackathon é legibilidade e compreensão dos dados.
