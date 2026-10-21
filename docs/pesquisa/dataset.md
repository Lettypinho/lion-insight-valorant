# Dataset

## 1. Objetivo

Documentar o conjunto de dados fornecido pelo Hackathon, sua estrutura, suas possibilidades e suas limitações.

Este arquivo deve ser atualizado sempre que a implementação confirmar ou refutar alguma hipótese sobre os JSONs.

## 2. Inventário preliminar

Levantamento preliminar da base fornecida:

- 199 arquivos JSON de partidas;
- 3.859 rounds;
- aproximadamente 27 mil eliminações;
- aproximadamente 47 mil registros de dano;
- cerca de 350 jogadores únicos;
- 61 equipes identificáveis pelos nomes dos arquivos;
- 9 mapas;
- 4 classificatórias.

Distribuição preliminar:

- C1: 55 partidas;
- C2: 39 partidas;
- C3: 43 partidas;
- C4: 62 partidas.

Esses números devem ser revalidados automaticamente pelo pipeline de ingestão e tratados como inventário preliminar até a primeira execução oficial.

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

Criar mapeamentos locais somente quando houver fonte confiável dentro do material disponível.

### 9.4 Coordenadas
Existem coordenadas em eventos, mas visualizações espaciais confiáveis exigem calibração de cada mapa.

Não incluir heatmaps completos no MVP.

## 10. Regra de atualização

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
