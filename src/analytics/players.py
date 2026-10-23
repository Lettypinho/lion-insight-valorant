"""
Metricas por jogador, calculadas sobre player_round.csv (uma linha por jogador em cada round).

Mesmo metodo de metrics.py (razao x/n, partida como unidade, mesmo criterio de veredito); muda a unidade:
  * jogador  = par (equipe, puuid) - o mesmo puuid pode ter jogado por mais de uma equipe;
  * referencia = todos os OUTROS jogadores de `df`, com os mesmos filtros (competicao, mapa, lado).
Definicoes registradas em docs/pesquisa/metricas.md (secao "Metricas por jogador").
"""
from pathlib import Path

import pandas as pd

from src.analytics import metrics as M
from src.analytics.metrics import Metric, _b

PLAYER_METRICS = [
    Metric("p_open_part", "Participação no duelo de abertura",
           "% dos rounds com abate em que o jogador faz ou sofre o primeiro abate",
           lambda d: _b(d.first_kill | d.first_death), lambda d: _b(d.has_fk), group="Abertura do round",
           neutral=True),
    Metric("p_open_win", "Vitória no duelo de abertura",
           "% dos duelos de abertura do jogador em que ele faz o primeiro abate",
           lambda d: _b(d.first_kill), lambda d: _b(d.first_kill | d.first_death), unit="duelos",
           group="Abertura do round"),
    Metric("p_fk_conv", "Conversão após o seu primeiro abate",
           "% de rounds vencidos quando o jogador faz o primeiro abate",
           lambda d: _b(d.first_kill & d.won), lambda d: _b(d.first_kill), group="Abertura do round"),
    Metric("p_survival", "Sobrevivência",
           "% dos rounds em que o jogador não é abatido por um inimigo",
           lambda d: _b(d.deaths_enemy == 0), lambda d: d.deaths_enemy * 0 + 1, group="Jogo individual"),
    Metric("p_trade_rate", "Mortes trocadas",
           "% das mortes do jogador com aliado vivo vingadas pela equipe em até 5 s",
           lambda d: d.deaths_traded, lambda d: d.deaths_tradeable, unit="mortes", group="Jogo coletivo"),
    Metric("p_isolated", "Mortes isoladas",
           "% das mortes do jogador com o aliado vivo mais próximo muito longe",
           lambda d: d.isolated_deaths, lambda d: d.deaths_with_dist, higher_better=False, unit="mortes",
           group="Jogo coletivo"),
    Metric("p_ability_kills", "Abates com habilidade",
           "% dos abates do jogador feitos com habilidade ou ultimate",
           lambda d: d.kills_ability, lambda d: d.kills_enemy, unit="abates", group="Tipo de abate", neutral=True),
    Metric("p_ability_deaths", "Mortes por habilidade",
           "% das mortes do jogador causadas por habilidade ou ultimate do adversário",
           lambda d: d.deaths_ability, lambda d: d.deaths_enemy, unit="mortes", group="Tipo de abate", neutral=True),
    Metric("p_trade_kills", "Abates de troca",
           "% dos abates do jogador que vingam um aliado morto em até 5 s",
           lambda d: d.trade_kills, lambda d: d.kills_enemy, unit="abates", group="Jogo coletivo", neutral=True),
]
BY_KEY = {m.key: m for m in PLAYER_METRICS}


def load(processed_dir="data/processed") -> pd.DataFrame:
    pr = pd.read_csv(Path(processed_dir) / "player_round.csv", low_memory=False)
    pr["player"] = pr["team"] + "|" + pr["puuid"]
    return pr


def load_names(processed_dir="data/processed") -> dict:
    """puuid -> nick mais recente (dim_player)."""
    dp = pd.read_csv(Path(processed_dir) / "dim_player.csv")
    return dict(zip(dp["puuid"], dp["latest_game_name"]))


def roster(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Numeros descritivos de cada jogador do time em `df` (ja filtrado). Contagens, sem veredito."""
    d = df[df["team"] == team]
    g = d.groupby(["player", "puuid"]).agg(
        partidas=("match_id", "nunique"), rounds=("round_num", "size"), abates=("kills_enemy", "sum"),
        mortes=("deaths_enemy", "sum"), dano=("damage_dealt", "sum"), primeiros_abates=("first_kill", "sum"),
        primeiras_mortes=("first_death", "sum"), mortes_trocadas=("deaths_traded", "sum"),
        abates_de_troca=("trade_kills", "sum"), abates_habilidade=("kills_ability", "sum"),
        mortes_habilidade=("deaths_ability", "sum")).reset_index()
    g["kd"] = g["abates"] / g["mortes"].where(g["mortes"] > 0)
    g["adr"] = g["dano"] / g["rounds"]
    duels = g["primeiros_abates"] + g["primeiras_mortes"]
    g["open_win"] = g["primeiros_abates"] / duels.where(duels > 0)

    # Agentes/funções mais usados no recorte. Como o agente se repete em todos os rounds da partida,
    # ordenar por frequência de rounds também funciona como uma leitura simples de preferência no recorte.
    if "agent" in d.columns:
        def _top(values):
            vc = values.dropna().astype(str).value_counts()
            return ", ".join(vc.index[:3]) if len(vc) else "—"
        agent = d.groupby("player")["agent"].apply(_top).rename("agentes")
        roles = d.groupby("player")["agent_role"].apply(_top).rename("funcoes") if "agent_role" in d.columns else None
        g = g.merge(agent, on="player", how="left")
        if roles is not None:
            g = g.merge(roles, on="player", how="left")
    else:
        g["agentes"] = "—"
        g["funcoes"] = "—"
    return g.sort_values(["rounds", "abates"], ascending=False).reset_index(drop=True)


def player_metrics(df: pd.DataFrame, player: str) -> pd.DataFrame:
    """`df` ja filtrado. Referencia = todos os outros jogadores de `df`."""
    return M.team_metrics(df, player, metrics=PLAYER_METRICS, key_col="player")
