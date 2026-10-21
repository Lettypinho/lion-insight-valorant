"""Barra lateral: seleção de equipe e filtros."""
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
import streamlit as st

from src.ui.formatting import ROLE_EN, team_name


@dataclass
class Filters:
    team: str
    comps: List[str]
    maps: List[str]
    side: str             # rótulo exibido: "Todos", "Ataque" ou "Defesa"
    role: Optional[str]   # None, "Attacker" ou "Defender"
    player: Optional[str] = None  # chave "equipe|puuid"; None = toda a equipe
    puuid: Optional[str] = None
    nick: Optional[str] = None


def render_sidebar(df_all: pd.DataFrame, teams: pd.DataFrame, players: pd.DataFrame, names: dict) -> Filters:
    with st.sidebar:
        st.markdown("### Raio-X de time")
        team_list = teams.index.tolist()
        default_team = st.query_params.get("team", team_list[0])
        team = st.selectbox("Time", team_list, index=team_list.index(default_team) if default_team in team_list else 0,
                            format_func=lambda s: f"{team_name(s)} ({int(teams.loc[s, 'partidas'])})")
        st.caption("Entre parênteses: partidas do time na base.")
        player = None
        if not players.empty:
            roster = (players[players["team"] == team].groupby(["player", "puuid"])["match_id"].nunique()
                      .sort_values(ascending=False).reset_index())
            opts = [None] + roster["player"].tolist()
            n_by = dict(zip(roster["player"], roster["match_id"]))
            nick_by = dict(zip(roster["player"], roster["puuid"].map(names).fillna("?")))
            player = st.selectbox("Jogador", opts, key=f"player_{team}",
                                  format_func=lambda p: "Toda a equipe" if p is None else f"{nick_by[p]} ({n_by[p]})")
        comp_order = (df_all.groupby("competition")["match_date"].min().sort_values().index.tolist())
        comps = st.multiselect("Competição", comp_order, placeholder="Todas")
        map_order = df_all["map_name"].value_counts().index.tolist()
        maps = st.multiselect("Mapa", map_order, placeholder="Todos")
        side = st.radio("Lado", ["Todos", "Ataque", "Defesa"], horizontal=True)
        st.caption("A referência é sempre formada pelos **outros times**, nas mesmas condições dos filtros acima.")
        st.caption("Dados: somente os JSONs fornecidos pela organização. Análise pós-partida.")
    puuid = player.split("|", 1)[1] if player else None
    return Filters(team=team, comps=comps, maps=maps, side=side, role=ROLE_EN[side], player=player, puuid=puuid,
                   nick=names.get(puuid) if puuid else None)
