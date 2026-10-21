# Métricas Táticas

## 1. Objetivo

Definir de forma única e reproduzível as métricas utilizadas pelo Lion Insight.

Nenhuma métrica deve ser implementada sem possuir uma definição neste documento.

## 2. Regras gerais

Toda métrica deve armazenar:

- valor;
- numerador;
- denominador;
- tamanho da amostra;
- filtros aplicados;
- rounds utilizados.

Quando o denominador for zero, a métrica deve retornar ausência de dado, e não zero por padrão.

## 3. First Kill

Primeira eliminação registrada em um round.

Identificar:

- round;
- jogador que realizou a eliminação;
- jogador eliminado;
- equipe que realizou a First Kill;
- equipe que sofreu a First Death;
- timestamp.

## 4. First Kill Conversion

### Pergunta
Quando a equipe consegue a primeira eliminação, quantas vezes vence o round?

### Fórmula
`rounds vencidos após conseguir First Kill / rounds em que conseguiu First Kill`

## 5. First Death Recovery

### Pergunta
Quando a equipe sofre a primeira eliminação, quantas vezes consegue recuperar e vencer o round?

### Fórmula
`rounds vencidos após sofrer First Death / rounds em que sofreu First Death`

## 6. Trade

### Definição inicial
Uma eliminação é considerada trade quando um jogador elimina, dentro de uma janela temporal definida, o adversário responsável por eliminar um companheiro.

### Decisão pendente
Definir e validar a janela temporal do MVP.

Sugestão inicial para teste:
- até 5 segundos.

Essa regra deve ser validada antes de ser considerada definitiva.

## 7. Conversão de vantagem

Quando a equipe alcança uma vantagem numérica, com que frequência vence o round?

Exemplos:
- 5v4;
- 4v3;
- 3v2.

No MVP, priorizar pelo menos a situação 5v4, caso seja simples de calcular após a reconstrução do estado de jogadores vivos.

## 8. Conversão de pós-plant

### Fórmula
`rounds vencidos pelo ataque após plant / rounds com plant realizado pelo ataque`

### Por site
Mesma fórmula restrita aos plants de um site. Também é exibida a distribuição dos plants:
`plants da equipe no site / plants da equipe`. Só é comparada dentro do mesmo mapa (os sites diferem entre mapas).

## 9. Retake Success

### Fórmula inicial
`rounds vencidos pela defesa após plant adversário / rounds em que o adversário plantou`

### Observação
Validar se todos os cenários classificados como retake podem ser inferidos apenas pelo plant e resultado. Caso contrário, usar nomenclatura mais precisa, como "vitória defensiva após plant".

## 10. Ataque e defesa

Calcular separadamente:

- rounds jogados no ataque;
- rounds vencidos no ataque;
- win rate no ataque;
- rounds jogados na defesa;
- rounds vencidos na defesa;
- win rate na defesa.

## 11. Headshot Percentage

Pode ser apresentada como métrica descritiva, mas não deve ser tratada como principal diagnóstico tático do MVP.

Confirmar a definição exata suportada pelos dados antes de implementar.

## 12. Economia

Os dados observados incluem informações como loadout, arma, armadura, créditos restantes e gasto.

A análise econômica é P1 até que uma classificação confiável de eco, force, half-buy e full-buy seja definida.

## 13. Benchmark

Para métricas de taxa, a referência principal da competição deve ser calculada usando todas as oportunidades válidas do universo comparável.

Evitar média simples das porcentagens de cada equipe quando isso distorcer o resultado.

Referências usadas na aplicação:

- **recorte geral**: todas as outras equipes, com os mesmos filtros de competição, mapa e lado;
- **por mapa**: as outras equipes no mesmo mapa, com os mesmos filtros;
- **uma partida**: as outras equipes no mesmo mapa da partida, com os mesmos filtros. Dentro da própria partida o único outro time é o adversário, que não serve de referência.

## 14. Amostra mínima

Toda métrica deve mostrar o tamanho da amostra.

Para o Insight Engine, definir um limite mínimo antes de classificar algo como ponto forte ou ponto de atenção.

Valor inicial sugerido para discussão:
- mínimo de 10 oportunidades.

Esse número deve ser validado pelo grupo antes de ser congelado.

## 15. Diferença em pontos percentuais

Comparações entre taxas devem usar pontos percentuais.

Exemplo:

Equipe: 74%  
Competição: 65%  
Diferença: `+9 p.p.`

## 16. Métricas por jogador

Calculadas sobre `player_round.csv` (uma linha por jogador em cada round) com o mesmo método das equipes: razão `x / n`, partida como unidade e o mesmo critério para confirmar uma diferença.

- **Jogador** = par (equipe, `puuid`). Um mesmo `puuid` que jogou por duas equipes é analisado separadamente em cada uma.
- **Referência** = todos os outros jogadores do recorte, com os mesmos filtros de competição, mapa e lado.
- Só abates sobre inimigo contam (sem suicídio, teamkill ou detonação), como nas métricas de equipe.

| Métrica | Fórmula | Leitura |
|---|---|---|
| Participação no duelo de abertura | rounds em que o jogador fez ou sofreu o primeiro abate / rounds com algum abate | **perfil** |
| Vitória no duelo de abertura | rounds em que o jogador fez o primeiro abate / rounds em que fez ou sofreu o primeiro abate | maior é melhor |
| Conversão após o seu primeiro abate | rounds vencidos em que o jogador fez o primeiro abate / rounds em que fez o primeiro abate | maior é melhor |
| Sobrevivência | rounds em que o jogador não foi abatido por inimigo / rounds jogados | maior é melhor |
| Mortes trocadas | mortes do jogador vingadas em até 5 s / mortes do jogador | maior é melhor |
| Mortes isoladas | mortes com aliado vivo mais próximo a mais de 3.000 unidades / mortes com distância calculável | menor é melhor |
| Abates de troca | abates do jogador que vingaram um aliado em até 5 s / abates do jogador | **perfil** |

**Perfil**: métricas que dependem da função do jogador (um duelista abre mais rounds; um suporte faz mais trocas). Quando a diferença é confirmada, ela é apresentada como "acima/abaixo da referência", nunca como ponto forte ou ponto de atenção.

Números descritivos do elenco, sem veredito: partidas, rounds, abates, mortes, K/D (abates / mortes), dano por round (`damage_dealt` / rounds) e primeiros abates e mortes.
