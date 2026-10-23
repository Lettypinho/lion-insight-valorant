"""Barra lateral: seleção de equipe, jogador e contexto da análise."""
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
import streamlit as st

from src.ui.formatting import ROLE_EN, competition_name, team_name


@dataclass
class Filters:
    team: str
    groups: List[str]       # campeonato/circuito escolhido pelo usuário
    stages: List[str]       # etapas escolhidas explicitamente
    comps: List[str]        # competições efetivamente aplicadas ao dataframe
    maps: List[str]
    side: str               # rótulo exibido: "Todos", "Ataque" ou "Defesa"
    role: Optional[str]     # None, "Attacker" ou "Defender"
    player: Optional[str] = None  # chave "equipe|puuid"; None = toda a equipe
    puuid: Optional[str] = None
    nick: Optional[str] = None


def _ordered(df: pd.DataFrame, column: str) -> list:
    """Valores na ordem cronológica da primeira partida em que aparecem."""
    return df.groupby(column)["match_date"].min().sort_values().index.tolist()


def render_sidebar(df_all: pd.DataFrame, teams: pd.DataFrame, players: pd.DataFrame, names: dict) -> Filters:
    with st.sidebar:
        st.markdown("## Lion Insight")
        st.caption("Raio-X tático pós-partida de VALORANT")

        st.markdown("### 1. Quem analisar")
        team_list = teams.index.tolist()
        default_team = st.query_params.get("team", team_list[0])
        team = st.selectbox(
            "Time",
            team_list,
            index=team_list.index(default_team) if default_team in team_list else 0,
            format_func=lambda s: f"{team_name(s)} · {int(teams.loc[s, 'partidas'])} partidas",
        )

        player = None
        if not players.empty:
            team_players = players[players["team"] == team].copy()
            roster = (team_players.groupby(["player", "puuid"])["match_id"].nunique()
                      .sort_values(ascending=False).reset_index())
            opts = [None] + roster["player"].tolist()
            n_by = dict(zip(roster["player"], roster["match_id"]))
            nick_by = dict(zip(roster["player"], roster["puuid"].map(names).fillna("?")))
            agent_by = {}
            if "agent" in team_players.columns:
                for pl, g in team_players.groupby("player"):
                    vals = g["agent"].dropna().astype(str).value_counts()
                    agent_by[pl] = vals.index[0] if len(vals) else None
            player = st.selectbox(
                "Jogador",
                opts,
                key=f"player_{team}",
                format_func=lambda p: (
                    "Toda a equipe" if p is None else
                    f"{nick_by[p]} · {agent_by.get(p) or 'agente não identificado'} · {n_by[p]} partidas"
                ),
            )

        st.markdown("### 2. Contexto da análise")
        st.caption("Deixe os filtros vazios para analisar **toda a base disponível**.")

        group_order = _ordered(df_all, "competition_group")
        groups = st.multiselect("Campeonato / circuito", group_order, placeholder="Toda a base", format_func=competition_name)
        scope = df_all[df_all["competition_group"].isin(groups)] if groups else df_all

        comp_order = _ordered(scope, "competition")
        stages = st.multiselect("Etapa", comp_order, placeholder="Todas do contexto", format_func=competition_name)
        # Se o usuário escolheu um campeonato mas nenhuma etapa, todas as etapas daquele campeonato entram no recorte.
        comps = stages if stages else (comp_order if groups else [])

        map_scope = scope[scope["competition"].isin(stages)] if stages else scope
        map_order = map_scope["map_name"].value_counts().index.tolist()
        maps = st.multiselect("Mapa", map_order, placeholder="Todos")
        side = st.radio("Lado", ["Todos", "Ataque", "Defesa"], horizontal=True)

        with st.expander("Como funciona a referência?", expanded=False):
            st.markdown(
                "O time é comparado com **todos os outros times que permanecem no mesmo recorte**. "
                "Sem filtros, a referência usa a base completa. Ao escolher campeonato, etapa, mapa ou lado, "
                "o mesmo filtro é aplicado ao time e à referência."
            )
        st.caption("Dados de desempenho: somente partidas fornecidas pela organização. Análise exclusivamente pós-partida.")

    puuid = player.split("|", 1)[1] if player else None
    return Filters(
        team=team, groups=groups, stages=stages, comps=comps, maps=maps, side=side, role=ROLE_EN[side],
        player=player, puuid=puuid, nick=names.get(puuid) if puuid else None,
    )
