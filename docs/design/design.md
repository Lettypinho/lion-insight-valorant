# Design e Experiência

## 1. Objetivo

Definir a experiência mínima necessária para demonstrar o valor do Lion Insight de forma rápida e compreensível.

## 2. Princípio de experiência

Selecionar equipe  
→ Entender identidade do time  
→ Encontrar ponto forte ou fragilidade  
→ Comparar com a competição  
→ Abrir evidências

## 3. Tela principal

### Cabeçalho
Exibir nome do produto, competição atual e equipe selecionada.

### Filtros principais
Prioridade:
- equipe;
- mapa, se implementado;
- classificatória, se implementado.

Evitar excesso de filtros no MVP.

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
- referência da competição;
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

## 7. Evidências

Ao abrir um insight, mostrar tabela com:
- partida;
- round;
- mapa;
- lado;
- contexto;
- resultado.

## 8. Competição

Se houver tempo, incluir uma visão simples da competição com classificatórias, equipes, partidas e referências gerais.

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
