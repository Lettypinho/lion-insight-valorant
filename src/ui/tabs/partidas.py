"""Aba Partidas e rounds: profundidade depois do panorama — uma partida, sua linha do tempo e cada round.

A referência de uma partida são os outros times NO MESMO MAPA (ver src.analytics.matches): dentro da partida
o único outro time é o adversário, que não serve de referência.
"""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.analytics.matches import match_frame, team_matches
from src.ui.charts import colors, tactical_map, timeline_figure
from src.ui.components import show_metrics_table
from src.ui.formatting import ROLE_PT, pct, team_name
from src.ui.sidebar import Filters

RESULT_PT = {"Elimination": "Eliminação", "Defuse": "Spike desarmado", "Detonate": "Spike detonado"}
ECON_PT = {"pistol": "pistol", "vantagem": "vantagem econômica", "desvantagem": "desvantagem econômica",
           "parelha": "economia parelha", "indefinida": "economia indefinida"}


def _result(code) -> str:
    return RESULT_PT.get(code, "Tempo esgotado") if pd.notna(code) else "Tempo esgotado"


def _clock(ms) -> str:
    s = int(ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


def _match_label(m) -> str:
    d = pd.to_datetime(m.match_date).strftime("%d/%m/%Y")
    return f"{d} · {m.map_name} · vs {team_name(m.opponent)} · {m.won} x {m.lost} ({m.result})"


def _round_hover(rr: pd.DataFrame) -> list:
    out = []
    for r in rr.itertuples():
        fk = "fez o 1º abate" if r.first_kill else "sofreu o 1º abate" if r.first_death else "sem abates"
        spike = f"plant no site {r.plant_site}" if r.bomb_planted else "sem plant"
        out.append(f"<b>Round {r.round_label}</b> · {ROLE_PT[r.role]} · {'venceu' if r.won else 'perdeu'}<br>"
                   f"{_result(r.result_code)} · {fk} · {spike}<br>{ECON_PT.get(r.econ_state, r.econ_state)}")
    return out


def _round_detail(r, ev: pd.DataFrame, sil: pd.DataFrame, view: dict, team: str):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resultado", "Venceu" if r.won else "Perdeu", _result(r.result_code), delta_color="off")
    c2.metric("Lado", ROLE_PT[r.role])
    c3.metric("Economia", ECON_PT.get(r.econ_state, r.econ_state).capitalize(),
              f"{int(r.team_loadout):,} x {int(r.opp_loadout):,} em equipamento".replace(",", "."), delta_color="off",
              help="Soma do valor de equipamento (loadout) do time e do adversário no round.")
    c4.metric("Spike", f"Site {r.plant_site}" if r.bomb_planted else "Não plantado",
              f"plantado aos {_clock(r.plant_time_ms)}" if r.bomb_planted and pd.notna(r.plant_time_ms) else None, delta_color="off")

    kills = ev.sort_values("seq_in_round")
    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Sequência de abates**")
        if kills.empty:
            st.caption("Nenhum abate entre jogadores neste round.")
        else:
            notes = []
            for k in kills.itertuples():
                n = []
                if k.is_first_kill: n.append("primeiro abate")
                if k.is_trade_kill: n.append("abate de troca")
                if k.death_was_traded: n.append("morte trocada")
                if k.isolated: n.append("vítima isolada")
                notes.append(", ".join(n) or "—")
            st.dataframe(pd.DataFrame({
                "#": kills["seq_in_round"], "Tempo": [_clock(t) for t in kills["time_in_round_ms"]],
                "Quem abateu": kills["killer_team"].map(team_name), "Quem morreu": kills["victim_team"].map(team_name),
                "Observação": notes}), hide_index=True, width="stretch", height=min(420, 38 + 35 * len(kills)))
    with right:
        C = colors()
        layers = []
        for name, m, color in [("Mortes do time", kills["victim_team"] == team, C["s2"]),
                               ("Mortes do adversário", kills["victim_team"] != team, C["s1"])]:
            k = kills[m & kills["victim_x"].notna()]
            layers.append(dict(name=name, x=k["victim_x"], y=k["victim_y"], color=color, labels=k["seq_in_round"].astype(str),
                               hover=[f"#{s} · {_clock(t)} · {team_name(v)} morreu" for s, t, v in
                                      zip(k["seq_in_round"], k["time_in_round_ms"], k["victim_team"])]))
        if r.bomb_planted and pd.notna(r.plant_x):
            layers.append(dict(name=f"Plant (site {r.plant_site})", x=[r.plant_x], y=[r.plant_y], color=C["s3"],
                               symbol="diamond", size=14, hover=[f"Plant no site {r.plant_site}"]))
        st.plotly_chart(tactical_map(sil, layers, view, height=460), width="stretch", theme=None,
                        config={"displayModeBar": False}, key=f"round_map_{r.match_id}_{r.round_num}")
        st.caption("Números = ordem dos abates. Posição de quem morreu.")


def render(df_all: pd.DataFrame, df_f: pd.DataFrame, f: Filters, events: pd.DataFrame, sil: pd.DataFrame, views: dict):
    team = f.team
    # placar e lista de partidas sem o filtro de lado, para refletir a partida inteira
    matches = team_matches(M.apply_filters(df_all, f.comps or None, f.maps or None, None), team)
    if matches.empty:
        st.info("Nenhuma partida do time com os filtros escolhidos.")
        return
    labels = {m.match_id: _match_label(m) for m in matches.itertuples()}
    mid = st.selectbox(f"Partida ({len(matches)})", matches["match_id"].tolist(), format_func=labels.get, key=f"pr_match_{team}_{hash(tuple(matches.match_id))}")
    m = matches.set_index("match_id").loc[mid]

    rr = df_all[(df_all["match_id"] == mid) & (df_all["team"] == team)].sort_values("round_num").copy()
    att, dfn = rr[rr["role"] == "Attacker"], rr[rr["role"] == "Defender"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Placar", f"{m.won} x {m.lost}", {"V": "vitória", "D": "derrota", "E": "empate"}[m.result], delta_color="off")
    c2.metric("No ataque", f"{int(att['won'].sum())} de {len(att)}", pct(att["won"].mean()) if len(att) else None, delta_color="off")
    c3.metric("Na defesa", f"{int(dfn['won'].sum())} de {len(dfn)}", pct(dfn["won"].mean()) if len(dfn) else None, delta_color="off")
    c4.metric("Primeiros abates", f"{int(rr['first_kill'].sum())} de {int(rr['has_fk'].sum())}",
              pct(rr["first_kill"].sum() / rr["has_fk"].sum()) if rr["has_fk"].sum() else None, delta_color="off")

    # linha do tempo: clicar em um round o seleciona
    rr["role_pt"] = rr["role"].map(ROLE_PT)
    rr["hover"] = _round_hover(rr)
    rounds = rr["round_label"].tolist()
    key_round = f"pr_round_{mid}"
    st.markdown("**Linha do tempo** — A = ataque, D = defesa. Clique em um round para abri-lo.")
    ev_tl = st.plotly_chart(timeline_figure(rr, st.session_state.get(key_round)), width="stretch", theme=None,
                            on_select="rerun", selection_mode="points", key=f"tl_{mid}", config={"displayModeBar": False})
    pts = ev_tl.selection.get("points", []) if ev_tl else []
    if pts and pts[0].get("x") != st.session_state.get(f"{key_round}_click"):
        st.session_state[f"{key_round}_click"] = pts[0].get("x")
        st.session_state[key_round] = int(pts[0]["x"])
    rnd = st.select_slider("Round", rounds, key=key_round)

    r = rr[rr["round_label"] == rnd].iloc[0]
    st.subheader(f"Round {rnd}")
    ev = events[(events["match_id"] == mid) & (events["round_num"] == r.round_num)] if not events.empty else events
    if sil.empty or events.empty or m.map_name not in views:
        st.info("Faltam os dados de posição. Gere-os com `python src/ingestion/build_features.py --processed data/processed`.")
    else:
        _round_detail(r, ev, sil[sil["map_name"] == m.map_name], views[m.map_name], team)

    with st.expander("Números da partida comparados com a referência"):
        st.caption(f"Referência: os outros times em {m.map_name}, com os filtros de competição e lado da barra lateral. "
                   "Uma partida descreve o que aconteceu, mas não confirma padrão.")
        mf = match_frame(df_f, team, mid, m.map_name)
        if mf[mf["team"] == team].empty:
            st.info("Sem rounds desta partida com o filtro de lado escolhido.")
        else:
            show_metrics_table(M.team_metrics(mf, team))
