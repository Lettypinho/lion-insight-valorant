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


def render_sidebar(df_all: pd.DataFrame, teams: pd.DataFrame) -> Filters:
    with st.sidebar:
        st.markdown("### Raio-X de time")
        team_list = teams.index.tolist()
        default_team = st.query_params.get("team", team_list[0])
        team = st.selectbox("Time", team_list, index=team_list.index(default_team) if default_team in team_list else 0,
                            format_func=lambda s: f"{team_name(s)} ({int(teams.loc[s, 'partidas'])})")
        st.caption("Entre parênteses: partidas do time na base.")
        comp_order = (df_all.groupby("competition")["match_date"].min().sort_values().index.tolist())
        comps = st.multiselect("Competição", comp_order, placeholder="Todas")
        map_order = df_all["map_name"].value_counts().index.tolist()
        maps = st.multiselect("Mapa", map_order, placeholder="Todos")
        side = st.radio("Lado", ["Todos", "Ataque", "Defesa"], horizontal=True)
        st.caption("A referência é sempre formada pelos **outros times**, nas mesmas condições dos filtros acima.")
        st.caption("Dados: somente os JSONs fornecidos pela organização. Análise pós-partida.")
    return Filters(team=team, comps=comps, maps=maps, side=side, role=ROLE_EN[side])
