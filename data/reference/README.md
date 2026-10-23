# Catálogos de referência

Esta pasta contém catálogos estáticos usados **somente para traduzir IDs do jogo em nomes legíveis**.
Eles não são fonte de resultados, eventos, placares, métricas ou qualquer outro dado de partida.

- `armas.csv`: UUID, nome, categoria, preço e tipo do item.
- `agentes.csv`: UUID, nome do agente e função.
- `armaduras.csv`: UUID e nome da armadura.

## Proveniência

A organização do Hackathon autorizou a tradução dos IDs por documentação pública. Os nomes foram conferidos em catálogos
públicos do ecossistema de VALORANT, principalmente Valorant-API (`https://valorant-api.com/`). Para agentes mais recentes,
a identificação também foi cruzada com páginas públicas de referência da comunidade (Liquipedia/Wikilorant).

Snapshot revisado em 22/10/2026. Se surgir um UUID novo na base, o pipeline deve falhar na validação em vez de inventar um nome.
