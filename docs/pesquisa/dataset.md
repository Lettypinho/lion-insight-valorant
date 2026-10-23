# Dataset

## 1. Objetivo

Documentar o conjunto de dados fornecido pelo Hackathon, sua estrutura, suas possibilidades e suas limitações.

Este arquivo deve ser atualizado sempre que a implementação confirmar ou refutar alguma hipótese sobre os JSONs.

## 2. Inventário validado da base completa

A fonte de verdade do Lion Insight é **toda a base tratada presente no repositório**. Nenhuma etapa é descartada durante o
processamento. Campeonato, etapa, mapa e lado existem como filtros de análise, não como mecanismos de exclusão do dataset.

Inventário validado pelo pipeline (`src/ingestion/ingest.py` + `src/ingestion/validate.py`):

| Item | Base completa |
|---|---|
| Arquivos JSON / partidas | 336 (nenhum `matchId` repetido) |
| Rounds | 6.618 |
| Eventos de morte | 46.753 (46.371 abates sobre inimigo, 327 detonações do spike, 46 suicídios, 9 teamkills) |
| Jogadores únicos (`puuid`) | 411 |
| Equipes | 68 |
| Mapas | 10 (Abyss, Ascent, Breeze, Fracture, Haven, Lotus, Pearl, Split, Summit, Sunset) |
| Partidas com prorrogação | 19 |

Partidas por contexto:

| Campeonato / circuito | Etapa | Partidas |
|---|---|---:|
| UNIVAVA | Classificatória 1 | 55 |
| UNIVAVA | Classificatória 2 | 39 |
| UNIVAVA | Classificatória 3 | 43 |
| UNIVAVA | Classificatória 4 | 62 |
| UNIVAVA | Fase de Grupos | 69 |
| Rush Series | Esquenta | 29 |
| Rush Series | Esquenta 2 | 26 |
| Rush Series | Inclusivo | 13 |

### 2.1 Regra de referência

Por padrão, a interface deixa toda a base disponível. A referência de uma métrica é calculada com os **outros times do
mesmo recorte**. Se nenhum filtro for aplicado, o recorte é a base completa. Se o usuário filtrar campeonato/circuito,
etapa, mapa ou lado, o mesmo filtro é aplicado ao time analisado e à referência.

## 3. Estrutura geral observada

Os JSONs possuem estruturas relacionadas a:

- `matchInfo`;
- `players`;
- `coaches`;
- `teams`;
- `roundResults`.

Dentro dos rounds existem informações suficientes para reconstruir diferentes eventos da partida, incluindo eliminações, dano, economia e objetivos.

## 4. Metadados da competição

O conteúdo do JSON não representa necessariamente toda a estrutura do campeonato.

Parte dos metadados da competição está presente no caminho ou nome dos arquivos.

Exemplo conceitual:

`UNIVAVA_C3_048_15-08-26_time_a_10_x_13_time_b_ascent.json`

A partir do nome podem ser obtidos, quando o padrão estiver correto:

- competição;
- classificatória;
- número da partida;
- data;
- equipe A;
- placar;
- equipe B;
- mapa.

O pipeline deve separar claramente:

- dados derivados do conteúdo JSON;
- dados derivados do nome/caminho do arquivo.

## 5. Informações de partida observadas

Em `matchInfo`, foram observados campos como:

- `matchId`;
- `mapId`;
- `gameVersion`;
- `gameLengthMillis`;
- `region`;
- `gameStartMillis`;
- `gameMode`.

A lista final deve ser confirmada pelo parser.

## 6. Jogadores

Os jogadores possuem informações que permitem relacionar:

- jogador;
- equipe/lado;
- agente;
- kills;
- deaths;
- assists;
- score;
- headshots;
- ability casts.

Alguns valores podem estar representados por IDs e precisar de mapeamento local para exibição amigável.

Confirmado na base (21/10/2026): 411 jogadores (`puuid`); 24 jogaram por mais de uma equipe e 55 usaram mais de um nick
ao longo das partidas. A interface exibe o nick mais recente (`dim_player.latest_game_name`). A soma dos abates, mortes e
primeiros abates dos jogadores de uma equipe bate com os totais da equipe (`tests/test_players.py`).

## 7. Rounds

Os rounds contêm informações fundamentais para o produto, incluindo:

- vencedor do round;
- lado atacante/defensor;
- tipo de vitória;
- plant;
- defuse;
- site;
- tempos de eventos;
- eliminações;
- assistências;
- dano;
- equipamento;
- economia;
- posições de jogadores em determinados eventos.

## 8. Possibilidades de análise

Os dados observados permitem, em princípio:

- First Kill;
- First Death;
- First Kill Conversion;
- First Death Recovery;
- opening duels;
- trades;
- tempo de resposta para trade;
- situações 5v4, 4v3 e outras vantagens;
- ataque x defesa;
- plant;
- pós-plant;
- retake;
- pistol rounds;
- tipos de vitória;
- economia por round;
- mapa;
- consistência entre partidas;
- reconstrução de clutches;
- performance individual e coletiva.

## 9. Limitações conhecidas

### 9.1 Habilidades
Embora existam contadores agregados de uso de habilidades por jogador, os campos de efeitos de habilidades por round foram observados como ausentes ou nulos na base preliminar.

Portanto, não utilizar análise causal de habilidades como pilar do MVP.

### 9.2 Chaveamento
Os JSONs não fornecem, por si só, uma estrutura oficial completa de chaveamento.

Não reconstruir bracket oficial sem fonte confiável.

### 9.3 IDs
Agentes, armas, armaduras ou mapas podem aparecer como IDs.

Criar mapeamentos locais somente com fonte pública confiável e utilizá-los apenas para tradução de IDs estáticos.
Os dados de desempenho continuam vindo exclusivamente dos JSONs fornecidos pela organização.

Implementado em `data/reference/`: `armas.csv`, `agentes.csv` e `armaduras.csv`. O pipeline grava nome do agente, função,
arma e armadura em `player_round.csv` quando os IDs estão presentes.

### 9.4 Coordenadas
Existem coordenadas em eventos, mas visualizações espaciais confiáveis exigem calibração de cada mapa.

Não incluir heatmaps completos no MVP.

Confirmado na base (21/10/2026): todas as 46.753 mortes têm `victimLocation` e 4.653 plants têm `plantLocation` e site. As posições de todos os jogadores (`playerLocations`) desenham a silhueta de cada mapa em unidades do jogo, o que permite plotar pontos sem imagem e sem calibração. Há posições muito fora do mapa (ex.: x ≈ −50.000 em Breeze e Haven, contra um mapa que vai de cerca de −3.600 a 11.000); a área exibida usa os percentis 0,2% a 99,8% da silhueta. Para exibição, cada mapa é girado em passos de 90° (sem espelhar) até os sites ficarem na horizontal com o A à direita, a partir da posição mediana dos plants de cada site (`src/ui/map_view.py`). Não foi conferido se o resultado coincide com o minimapa oficial.

`playerLocations[].viewRadians` segue a convenção `atan2(dy, dx)` nas coordenadas do jogo: em 99% dos abates a mira do
matador aponta para a vítima (diferença mediana de 0,3°). Usado para desenhar a direção da mira no momento do abate.

Cada round com plant ou defuse traz `plantPlayerLocations` / `defusePlayerLocations` (posição e mira de cada jogador vivo
no instante): 4.653 plants e 1.349 defuses, todos com posições, e quem plantou/desarmou sempre aparece entre elas.
Ingeridos em `fact_objective_position.csv` (33.878 linhas). `plantRoundTime`/`defuseRoundTime` usam o mesmo relógio de
`timeSinceRoundStartMillis` dos abates: o número de posições no plant bate com os vivos calculados pelos horários dos
abates em 98,9% dos plants (98,2% dos defuses); com 30 s de deslocamento a concordância cai para ~10%.

## 10. Regras confirmadas pela ingestão

Validadas por `src/ingestion/validate.py` sobre a base completa:

- **Nome da equipe só existe no nome do arquivo.** Red/Blue é identificado cruzando o placar do arquivo com `teams[].roundsWon` (336/336 consistentes).
- Padrão de nome: `<COMPETIÇÃO>_<nº><sufixo>_<dd-mm-aa>_<equipe_a>_<placar_a>_x_<placar_b>_<equipe_b>_<mapa>.json`. Códigos: `RUSHE`, `RUSH2`, `RUSH_INCLUSIVO`, `UNIVAVA_G`, `UNIVAVA_C1` a `UNIVAVA_C4`.
- **Sufixos a/b/c** no número (ex.: `G_012c`) são jogos de uma mesma série, não duplicatas (75 partidas com sufixo).
- A data do arquivo coincide com `gameStartMillis` no fuso de São Paulo em todas as partidas.
- **Kill** do placar oficial = abate sobre inimigo (exclui suicídio e teamkill); reproduz `stats.kills` em 100% dos casos. **Death** = qualquer morte exceto detonação do spike; reproduz `stats.deaths` com 2 divergências em 3.360 registros jogador × partida.
- Lado atacante/defensor por round vem de `winningTeam` + `winningTeamRole` (correto também na prorrogação). O lado é fixo em cada metade e troca no intervalo.
- `playerLocations` de uma eliminação = jogadores vivos **menos a vítima** em cerca de 99% dos casos; a posição da vítima está em `victimLocation`. Contar ali os aliados da vítima dá quantos companheiros ainda estavam vivos: bate com `5 − mortes do lado até aquele abate` em 99,5% dos abates (46.371 abates sobre inimigo; 2 sem posições). Coluna `victim_allies_alive` de `kill_events.csv`.
- Observadores (`isObserver`) aparecem em 22 partidas e ficam fora das tabelas de jogadores. Após removê-los, toda partida tem 10 jogadores, 5 por lado.
- `mapId` usa nomes internos, com correspondência 1:1 ao mapa do nome do arquivo (ex.: Jam = Lotus, Triad = Haven, Bonsai = Split, Plummet = Summit).
- Agente, arma e armadura são UUIDs; **os nomes não estão na base** (nenhum nome de arma aparece no texto dos 336 JSONs; 21 armas e 4 armaduras distintas). O único dado legível sobre o que causou um abate é `finishingDamage.damageType` (`Weapon`, `Ability`, `Melee`, `Fall`, `Crush`, `Bomb`) e, para habilidades, `damageItem` (`Ability1`, `Ability2`, `GrenadeAbility`, `Ultimate`).
- **Nomes das armas (21/10/2026, uso autorizado pela organização):** tabela estática `data/reference/armas.csv` (código, nome, categoria, preço, tipo). Não é dado de partida: é o catálogo de itens do jogo, tirado de `valorant-api.com/v1/weapons` (espelho comunitário dos dados do jogo). Cobre os 21 códigos de arma da base e todas as armas principais de `economy.weapon`. 169 abates com arma e 16 linhas jogador × round não trazem o código do item.
- **Armas de habilidade (inferidas):** 3 códigos registrados como `Weapon` não estão no catálogo. Pelo agente de quem abate, são do Chamber (481 e 42 abates) e da Neon (207). Teste de pontos de ultimate (máximo por round = abates + 1 morte + 1 plant/defuse + 2 orbes; ultimate de 7 a 8 pontos): nos rounds seguidos em que o mesmo jogador abateu com o item, nenhum par é impossível para os códigos de 42 e 207 abates (0 de 7 e 0 de 38), enquanto o de 481 falha em 71 de 244 pares (controle: é usado todo round). Conclusão: 481 = Headhunter (habilidade), 42 = Tour de Force (ultimate), 207 = Overdrive (ultimate; 155 rounds com abate contra 413 ultimates usadas pelas Neons). Marcados como `fonte = inferido` na tabela.
- Há equipes com nomes parecidos (ex.: `inatel`, `inatel_gray`, `inatel_legacy`; `usp_stars`, `usp_stars_gc`) que devem ser tratadas como equipes distintas até confirmação.

## 11. Regra de atualização

Ao implementar a ingestão, produzir automaticamente um relatório de validação contendo:

- quantidade de arquivos;
- arquivos inválidos;
- quantidade de partidas;
- quantidade de rounds;
- quantidade de equipes;
- quantidade de jogadores;
- mapas encontrados;
- campos ausentes;
- valores inesperados.

Atualizar este documento após essa validação.
