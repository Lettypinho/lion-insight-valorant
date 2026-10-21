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

### Fórmula (decisão de 21/10/2026)
`mortes trocadas / mortes trocáveis`

**Morte trocável**: a vítima tinha ao menos um aliado vivo logo após o abate (ou a morte foi trocada). A morte de quem era
o último vivo do time fica fora do denominador: não havia quem trocasse, e contá-la penalizaria quem perde rounds por
eliminação ou joga clutches. Abates sem posições registradas (2 na base) contam como trocáveis. Vale para o time
(`trade_rate`) e para o jogador (`p_trade_rate`); colunas `deaths_tradeable` em `team_round` e `player_round`.

Impacto na base: 40.331 mortes trocáveis de 46.371; a taxa geral passa de 21,3% para 24,5%. Nenhum veredicto de equipe
mudou; 19 de 411 jogadores mudaram de veredicto (10 deixaram de aparecer abaixo da referência).

### Classificação de cada morte (detalhe do round)
Na aba Partidas e rounds, cada morte recebe uma classificação descritiva. Não é métrica nova: usa só a regra de trade
acima e a contagem de aliados vivos.

| Classificação | Regra |
|---|---|
| Trocada | um aliado da vítima abateu quem a matou em até 5 s (`death_was_traded`) |
| Não trocada | não foi trocada **e** havia ao menos um aliado vivo logo após o abate |
| Sem aliado vivo | não foi trocada e a vítima era a última viva do time: não havia quem trocasse |

Complementos exibidos junto: primeiro abate do round, abate de troca, vítima isolada (aliado vivo mais próximo a mais de 3.000 unidades, seção 16) e plantador punido (9.1).

Validação (21/10/2026): das 36.504 mortes não trocadas, 6.042 (16,5%) foram de quem era o último vivo do time. Por isso
elas saem do denominador de "Mortes trocadas" (fórmula acima).

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

## 9.1 Plant sem cobertura e punição ao plant

### Pergunta
Quando a equipe planta, o plantador fica exposto? Quando o adversário planta, a defesa pune quem plantou?

### Evento
**Plantador punido**: quem plantou é abatido por um inimigo em até **5 s** depois do plant (`PLANT_COVER_MS`, mesma janela do trade) e essa morte **não é trocada**.

### Fórmulas
- **Plant sem cobertura (ataque)**: `plants da equipe com plantador punido / plants da equipe`. Menor é melhor.
- **Punição ao plant (defesa)**: `plants adversários com plantador punido / plants adversários`. Maior é melhor.

### Validação na base (21/10/2026)
217 de 4.653 plants (4,7%). O ataque vence 21% desses rounds, contra 73% nos demais plants. A mediana do tempo entre o plant e a morte do plantador (quando ele morre) é de 17 s; a janela de 5 s capta só a punição imediata.

### Não incluído
"Morte durante o defuse" não é calculável: a base registra apenas o defuse concluído, não as tentativas. Inferir pela proximidade do spike misturaria tentativas de defuse com lutas no site.

## 9.2 Tipo de abate

### Classificação (de `finishingDamage` de cada abate sobre inimigo)
| `damageType` | `damageItem` | Tipo |
|---|---|---|
| `Weapon` | UUID da arma | arma |
| `Ability` | `Ultimate` | ultimate |
| `Ability` | `Ability1`, `Ability2`, `GrenadeAbility` | habilidade |
| `Melee` | UUID da faca | faca |
| `Fall`, `Crush` | vazio | outro |

Base (21/10/2026): 45.121 arma, 812 ultimate, 414 habilidade, 15 faca, 9 outro. As armas só têm UUID, sem nome.

### Fórmulas (equipe e jogador)
- **Abates com habilidade**: `abates com habilidade ou ultimate / abates sobre inimigo`. **Perfil**.
- **Mortes por habilidade**: `mortes por habilidade ou ultimate do adversário / mortes por inimigo`. **Perfil**.

São perfil porque dependem dos agentes escolhidos (e dos agentes do adversário). Na base, nenhuma equipe teve diferença
confirmada; 17 jogadores tiveram perfil confirmado. A distribuição completa por tipo (arma, habilidade, ultimate, faca,
outro) é exibida de forma descritiva, ao lado da referência (todos os outros do recorte).

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

### Critério implementado

Uma diferença só é confirmada (ponto forte / ponto de atenção) quando, ao mesmo tempo:

1. há ao menos 15 oportunidades em ao menos 3 partidas;
2. a diferença para a referência supera a incerteza do time e da referência (intervalo de 95% com cada partida como unidade);
3. a diferença é de ao menos 3 p.p.;
4. a taxa da referência fica **fora do intervalo de Wilson (95%)** da proporção `x / n` da equipe.

O item 4 é uma trava para eventos raros: com 0 eventos, o erro-padrão por partida vira zero e confirmaria diferenças
compatíveis com o acaso (ex.: 0 de 28 plants contra uma referência de 4,7%; o intervalo de Wilson de 0/28 vai até ~12%).
Adotada em 21/10/2026 para todas as métricas: derrubou 18 dos 19 vereditos das métricas de plant e 7 dos 70 das demais.
A taxa de falso alerta com equipes sorteadas ao acaso ficou entre 4,1% e 4,5% (`tests/calibration.py`).

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
| Mortes trocadas | mortes do jogador vingadas em até 5 s / mortes do jogador com aliado vivo (seção 6) | maior é melhor |
| Mortes isoladas | mortes com aliado vivo mais próximo a mais de 3.000 unidades / mortes com distância calculável | menor é melhor |
| Abates de troca | abates do jogador que vingaram um aliado em até 5 s / abates do jogador | **perfil** |
| Abates com habilidade | abates com habilidade ou ultimate / abates do jogador (ver 9.2) | **perfil** |
| Mortes por habilidade | mortes por habilidade ou ultimate / mortes do jogador (ver 9.2) | **perfil** |

**Perfil**: métricas que dependem da função do jogador (um duelista abre mais rounds; um suporte faz mais trocas). Quando a diferença é confirmada, ela é apresentada como "acima/abaixo da referência", nunca como ponto forte ou ponto de atenção.

Números descritivos do elenco, sem veredito: partidas, rounds, abates, mortes, K/D (abates / mortes), dano por round (`damage_dealt` / rounds) e primeiros abates e mortes.
