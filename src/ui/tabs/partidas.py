"""Aba Partidas e rounds: profundidade depois do panorama — uma partida, sua linha do tempo e cada round.

A referência de uma partida são os outros times NO MESMO MAPA (ver src.analytics.matches): dentro da partida
o único outro time é o adversário, que não serve de referência.
"""
import numpy as np
import pandas as pd
import streamlit as st

from src.analytics import kill_types as K
from src.analytics import metrics as M
from src.analytics.matches import (DEATH_PT, classify_deaths, death_summary, match_frame, round_moments,
                                   spike_planted_at, team_matches)
from src.ui.charts import MAP_CONFIG, colors, tactical_map, timeline_figure
from src.ui.components import show_metrics_table
from src.ui.formatting import ROLE_PT, pct, team_name
from src.ui.sidebar import Filters

RESULT_PT = {"Elimination": "Eliminação", "Defuse": "Spike desarmado", "Detonate": "Spike detonado"}
ECON_PT = {"pistol": "pistol", "vantagem": "vantagem econômica", "desvantagem": "desvantagem econômica",
           "parelha": "economia parelha", "indefinida": "economia indefinida"}


def _result(code) -> str:
    return RESULT_PT.get(code, "Tempo esgotado") if pd.notna(code) else "Tempo esgotado"


def _clock(ms) -> str:
    """m:ss.d — com décimos, para a janela de 5 s da troca ser conferível na tela."""
    s, d = int(ms) // 1000, int(ms) % 1000 // 100
    return f"{s // 60}:{s % 60:02d}.{d}"


def _secs(ms) -> str:
    return f"{ms / 1000:.1f}".replace(".", ",") + " s"


def _match_label(m) -> str:
    d = pd.to_datetime(m.match_date).strftime("%d/%m/%Y")
    return f"{d} · {m.map_name} · vs {team_name(m.opponent)} · {m.won} x {m.lost} ({m.result})"


def _round_hover(rr: pd.DataFrame) -> list:
    out = []
    for r in rr.itertuples():
        fk = "fez o 1º abate" if r.first_kill else "sofreu o 1º abate" if r.first_death else "sem abates"
        spike = f"plant no site {r.plant_site}" if r.bomb_planted else "sem plant"
        deaths = (f"{int(r.deaths_enemy)} morte(s) do seu time, {int(r.deaths_traded)} trocada(s) de "
                  f"{int(r.deaths_tradeable)} com aliado vivo" if r.deaths_enemy else "nenhuma morte do seu time")
        out.append(f"<b>Round {r.round_label}</b> · {ROLE_PT[r.role]} · {'venceu' if r.won else 'perdeu'}<br>"
                   f"{_result(r.result_code)} · {fk} · {spike}<br>{deaths}<br>{ECON_PT.get(r.econ_state, r.econ_state)}")
    return out


AIM_LEN = 500  # comprimento do traço de mira, em unidades do jogo


def _who(names: dict, p, t) -> str:
    return f"{names.get(p, '?')} ({team_name(t)})"


def _death_text(k) -> str:
    """Classificação da morte por extenso (para a legenda do momento)."""
    if k.death_class == "trocada":
        return (f"morte trocada {_secs(k.trade_after_ms)} depois, no abate #{int(k.trade_seq)}"
                if pd.notna(k.trade_seq) else "morte trocada")
    if k.death_class == "sem_aliado":
        return "morte não trocada: era o último vivo do time"
    if k.death_class == "nao_trocada":
        return f"morte não trocada, com {int(k.victim_allies_alive)} aliado(s) vivo(s)"
    return ""


def _kill_feed(kills: pd.DataFrame, names: dict, puuid, team: str, key: str):
    """Tabela da sequência de abates; retorna o # do abate clicado (ou None). kills = saída de classify_deaths."""
    notes = []
    for k in kills.itertuples():
        n = []
        if k.is_first_kill: n.append("primeiro abate do round")
        if k.is_trade_kill: n.append(f"abate de troca (vingou o #{int(k.avenged_seq)})" if pd.notna(k.avenged_seq) else "abate de troca")
        if k.isolated: n.append("vítima isolada")
        if k.planter_punished: n.append("plantador punido")
        notes.append(", ".join(n) or "—")
    feed = pd.DataFrame({
        "#": kills["seq_in_round"].to_numpy(), "Tempo": [_clock(t) for t in kills["time_in_round_ms"]],
        "Quem abateu": [_who(names, p, t) for p, t in zip(kills["killer_puuid"], kills["killer_team"])],
        "Quem morreu": [_who(names, p, t) for p, t in zip(kills["victim_puuid"], kills["victim_team"])],
        "Como": [K.describe(k, i) for k, i in zip(kills["kill_kind"], kills["damage_item"])],
        "Morte": [f"Trocada em {_secs(t)} (#{int(s)})" if c == "trocada" and pd.notna(s) else DEATH_PT[c]
                  for c, s, t in zip(kills["death_class"], kills["trade_seq"], kills["trade_after_ms"])],
        "Contexto": notes})
    mark = ((kills["killer_puuid"] == puuid) | (kills["victim_puuid"] == puuid)).to_numpy() if puuid else None
    # vermelho = ruim para o seu time: morte do seu time que não foi trocada havendo aliado vivo
    bad = ((kills["victim_team"] == team) & (kills["death_class"] == "nao_trocada")).to_numpy()
    hl = f"background-color: color-mix(in srgb, {colors()['team']} 22%, transparent)"
    red = f"background-color: color-mix(in srgb, {colors()['enemy']} 22%, transparent)"

    def style(row):
        base = hl if mark is not None and mark[row.name] else ""
        return [red if c == "Morte" and bad[row.name] else base for c in row.index]

    styled = feed.style.apply(style, axis=1)
    ev = st.dataframe(styled, hide_index=True, width="stretch", height=min(420, 38 + 35 * len(kills)),
                      on_select="rerun", selection_mode="single-row", key=key)
    st.caption("Morte: **trocada** = um aliado abateu quem matou em até 5 s; **não trocada** = havia aliado vivo e "
               "ninguém vingou (em vermelho quando é do seu time); **sem aliado vivo** = era o último do time, não havia "
               "quem trocasse." + (f" Linhas destacadas: abates e mortes de {names.get(puuid, 'jogador')}." if puuid else ""))
    rows = ev.selection.get("rows", []) if ev else []
    return int(feed["#"].iloc[rows[0]]) if rows else None


def _round_overview(r, kills: pd.DataFrame, sil: pd.DataFrame, view: dict, team: str, names: dict):
    C = colors()
    layers = []
    for name, m, color in [("Mortes do seu time", kills["victim_team"] == team, C["ally"]),
                           ("Mortes do adversário", kills["victim_team"] != team, C["enemy"])]:
        k = kills[m & kills["victim_x"].notna()]
        layers.append(dict(name=name, x=k["victim_x"], y=k["victim_y"], color=color, symbol="x", size=13,
                           labels=k["seq_in_round"].astype(str),
                           hover=[f"#{s} · {_clock(t)} · {_who(names, v, vt)} abatido por {names.get(kp, '?')} "
                                  f"({K.describe(kk, ki).lower()})"
                                  for s, t, v, vt, kp, kk, ki in zip(k["seq_in_round"], k["time_in_round_ms"], k["victim_puuid"],
                                                                     k["victim_team"], k["killer_puuid"], k["kill_kind"],
                                                                     k["damage_item"])]))
    if r.bomb_planted and pd.notna(r.plant_x):
        layers.append(dict(name=f"Spike (site {r.plant_site})", x=[r.plant_x], y=[r.plant_y], color=C["s3"],
                           symbol="diamond", size=14, hover=[f"Plant no site {r.plant_site} aos {_clock(r.plant_time_ms)}"]))
    st.plotly_chart(tactical_map(sil, layers, view, height=460, dragmode="pan", uirevision=f"ov_{r.match_id}_{r.round_num}"),
                    width="stretch", theme=None, config=MAP_CONFIG, key=f"round_map_{r.match_id}_{r.round_num}")
    st.caption("✕ = onde cada jogador morreu; o número é a ordem do abate. Azul: seu time · vermelho: adversário. "
               "Roda do mouse dá zoom; duplo clique volta ao mapa inteiro.")


def _aim_lines(sub: pd.DataFrame):
    xs, ys = [], []
    for row in sub.itertuples():
        xs += [row.x, row.x + AIM_LEN * np.cos(row.view_radians), None]
        ys += [row.y, row.y + AIM_LEN * np.sin(row.view_radians), None]
    return xs, ys


ACTION = {"kill": "abateu", "plant": "plantou", "defuse": "desarmou"}


def _snapshot(kind: str, actor, pos: pd.DataFrame, team_of: dict, sil: pd.DataFrame, view: dict, team: str,
              names: dict, puuid, chart_key: str, zoom_key, victim=None, spike=None, close_up=False):
    """Foto de um instante do round: todos os vivos com nick e mira, quem agiu (abateu/plantou/desarmou),
    a vítima (num abate) e o spike (se já estava plantado). victim/spike: dicts com x, y (+ puuid / site)."""
    C = colors()

    def color(p):
        return C["ally"] if team_of.get(p) == team else C["enemy"]

    def side(p):
        return "seu time" if team_of.get(p) == team else "adversário"

    alive = pos.assign(mine=pos["puuid"].map(team_of) == team)
    others = alive[alive["puuid"] != actor]
    who = alive[alive["puuid"] == actor]

    lines = []
    for mine in (True, False):
        xs, ys = _aim_lines(alive[alive["mine"] == mine])
        lines.append(dict(x=xs, y=ys, color=C["ally"] if mine else C["enemy"], width=2))
    if victim and len(who):
        lines.append(dict(x=[who["x"].iloc[0], victim["x"]], y=[who["y"].iloc[0], victim["y"]],
                          color=color(actor), width=2.5, dash="dash"))

    # no plant/defuse o jogador está em cima do spike: um só ícone (◆ com o nick, borda na cor do time dele)
    on_spike = kind in ("plant", "defuse") and spike is not None
    layers = []
    if spike and on_spike:
        layers.append(dict(name=f"Spike (site {spike['site']}) · quem {ACTION[kind]}", x=[spike["x"]], y=[spike["y"]],
                           color=C["s3"], symbol="diamond", size=20, line_width=3, line_color=color(actor),
                           labels=[names.get(actor, "?")],
                           hover=[f"{names.get(actor, '?')} ({side(actor)}) {ACTION[kind]} o spike no site {spike['site']}"]))
    elif spike:
        layers.append(dict(name=f"Spike plantado (site {spike['site']})", x=[spike["x"]], y=[spike["y"]], color=C["s3"],
                           symbol="diamond", size=16, line_width=2, line_color=C["surface"],
                           hover=[f"Spike plantado no site {spike['site']}"]))
    for mine, name in [(True, "Seu time · vivo"), (False, "Adversário · vivo")]:
        sub = others[others["mine"] == mine]
        layers.append(dict(name=f"{name} ({len(sub)})", x=sub["x"], y=sub["y"], color=C["ally"] if mine else C["enemy"],
                           size=11, labels=sub["puuid"].map(names).fillna("?"),
                           hover=[f"{names.get(p, '?')} ({side(p)}) · vivo" for p in sub["puuid"]]))
    if len(who) and not on_spike:
        layers.append(dict(name=f"Quem {ACTION[kind]}", x=who["x"], y=who["y"], color=color(actor), size=17,
                           line_width=3, line_color=C["text"], labels=[names.get(actor, "?")],
                           hover=[f"{names.get(actor, '?')} ({side(actor)}) · {ACTION[kind]}"]))
    if victim:
        layers.append(dict(name="Quem morreu", x=[victim["x"]], y=[victim["y"]], color=color(victim["puuid"]), symbol="x",
                           size=19, labels=[names.get(victim["puuid"], "?")],
                           hover=[f"{names.get(victim['puuid'], '?')} ({side(victim['puuid'])}) · morreu"]))
    if puuid:
        sel = alive[alive["puuid"] == puuid]
        pts = list(zip(sel["x"], sel["y"])) or ([(victim["x"], victim["y"])] if victim and victim["puuid"] == puuid else [])
        if pts:
            layers.append(dict(name="Jogador selecionado", x=[p[0] for p in pts], y=[p[1] for p in pts], color=C["text"],
                               symbol="circle-open", size=28, line_width=2, line_color=C["text"], hover=[names.get(puuid, "?")]))

    focus = None
    if close_up:
        focus = [(x, y) for x, y in zip(who["x"], who["y"])]
        focus += [(victim["x"], victim["y"])] if victim else []
        focus += [(spike["x"], spike["y"])] if spike else []
    st.plotly_chart(tactical_map(sil, layers, view, height=540, lines=lines, focus=focus or None, dragmode="pan",
                                 uirevision=zoom_key),
                    width="stretch", theme=None, config=MAP_CONFIG, key=chart_key)
    n_mine, n_opp = int(alive["mine"].sum()), int((~alive["mine"]).sum())
    when = "Depois do abate" if kind == "kill" else "No momento do plant" if kind == "plant" else "No momento do defuse"
    st.caption(f"{when}: **{n_mine} vivo(s) no seu time** (azul) e **{n_opp} no adversário** (vermelho). "
               + (f"◆ = spike, com o nick de quem {ACTION[kind]} (borda na cor do time dele)" if on_spike else
                  f"Círculo com anel = quem {ACTION[kind]}"
                  + ("; linha tracejada = até quem morreu" if victim else "") + ("; ◆ = spike" if spike else ""))
               + "; traço curto = para onde cada jogador mirava. Roda do mouse dá zoom; duplo clique volta ao enquadramento. "
               "As posições só existem nos instantes de abates, plant e defuse (não é um replay contínuo).")


def _round_detail(r, ev: pd.DataFrame, sil: pd.DataFrame, view: dict, team: str, names: dict, puuid,
                  pos_match: pd.DataFrame, obj_match: pd.DataFrame, team_of: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resultado", "Venceu" if r.won else "Perdeu", _result(r.result_code), delta_color="off")
    c2.metric("Lado", ROLE_PT[r.role])
    c3.metric("Economia", ECON_PT.get(r.econ_state, r.econ_state).capitalize(),
              f"{int(r.team_loadout):,} x {int(r.opp_loadout):,} em equipamento".replace(",", "."), delta_color="off",
              help="Soma do valor de equipamento (loadout) do time e do adversário no round.")
    c4.metric("Spike", f"Site {r.plant_site}" if r.bomb_planted else "Não plantado",
              f"plantado aos {_clock(r.plant_time_ms)}" if r.bomb_planted and pd.notna(r.plant_time_ms) else None, delta_color="off")

    kills = classify_deaths(ev.sort_values("seq_in_round").reset_index(drop=True), r)
    moments = round_moments(kills, r)
    if not moments:
        st.caption("Nenhum abate, plant ou defuse registrado neste round.")
        return
    base = f"{r.match_id}_{r.round_num}"
    clicked = None
    if not kills.empty:
        s = death_summary(kills, team)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mortes do seu time", s["deaths"])
        c2.metric("Trocadas", s["traded"])
        c3.metric("Não trocadas", s["untraded"], help="Havia aliado vivo e ninguém abateu quem matou em até 5 s.")
        c4.metric("Sem aliado vivo", s["last_alive"], help="Era o último vivo do time: não havia quem trocasse.")
        c5.metric("Abates de troca do seu time", f"{s['trade_kills']} de {s['kills']}",
                  help="Abates do seu time que vingaram um aliado em até 5 s / abates do seu time no round.")
        left, right = st.columns([1, 1])
        with left:
            st.markdown("**Sequência de abates** — clique em uma linha para ver o momento do abate")
            clicked = _kill_feed(kills, names, puuid, team, key=f"feed_{base}")
        with right:
            _round_overview(r, kills, sil, view, team, names)

    st.markdown("**Momentos do round** — abates, plant e defuse em ordem")
    by_id = {m["id"]: m for m in moments}
    mkey = f"moment_{base}"
    if clicked is not None and clicked != st.session_state.get(f"{mkey}_click"):
        st.session_state[f"{mkey}_click"] = clicked
        st.session_state[mkey] = f"k{clicked}"

    def label(i):
        m = by_id[i]
        tag = f"#{m['seq']}" if m["kind"] == "kill" else "Plant" if m["kind"] == "plant" else "Defuse"
        return f"{tag} · {_clock(m['time_ms'])}"

    c_sel, c_zoom = st.columns([4, 1])
    with c_sel:
        mid_ = st.select_slider("Momento", list(by_id), key=mkey, format_func=label) if len(by_id) > 1 else moments[0]["id"]
    close_up = c_zoom.toggle("Aproximar no lance", key="close_up",
                             help="Enquadra quem agiu, a vítima e o spike. Desligado, o zoom feito com o mouse é mantido entre momentos.")
    m = by_id[mid_]
    zoom_key = f"z_{base}_{mid_}" if close_up else f"z_{base}"
    spike = (dict(x=r.plant_x, y=r.plant_y, site=r.plant_site)
             if spike_planted_at(r, m["time_ms"]) and pd.notna(r.plant_x) else None)

    if m["kind"] == "kill":
        k = next(kills[kills["seq_in_round"] == m["seq"]].itertuples())
        extra = [_death_text(k)] + (["plantador punido"] if k.planter_punished else []) + (["spike já plantado"] if spike else [])
        st.markdown(f"#{m['seq']} aos {_clock(k.time_in_round_ms)}: **{_who(names, k.killer_puuid, k.killer_team)}** abateu "
                    f"**{_who(names, k.victim_puuid, k.victim_team)}** com **{K.describe(k.kill_kind, k.damage_item).lower()}**"
                    + "".join(f" · {e}" for e in extra if e))
        victim = dict(x=k.victim_x, y=k.victim_y, puuid=k.victim_puuid) if pd.notna(k.victim_x) else None
        _snapshot("kill", k.killer_puuid, pos_match[pos_match["kill_id"] == k.kill_id], team_of, sil, view, team, names,
                  puuid, f"snap_{base}", zoom_key, victim=victim, spike=spike, close_up=close_up)
    else:
        actor = r.planter_puuid if m["kind"] == "plant" else r.defuser_puuid
        verb = "plantou o spike no site " + str(r.plant_site) if m["kind"] == "plant" else "desarmou o spike"
        st.markdown(f"{label(mid_).split(' · ')[0]} aos {_clock(m['time_ms'])}: **{_who(names, actor, team_of.get(actor, ''))}** {verb}")
        pos = obj_match[(obj_match["round_num"] == r.round_num) & (obj_match["event"] == m["kind"])]
        _snapshot(m["kind"], actor, pos, team_of, sil, view, team, names, puuid, f"snap_{base}", zoom_key,
                  spike=spike if spike else (dict(x=r.plant_x, y=r.plant_y, site=r.plant_site) if pd.notna(r.plant_x) else None),
                  close_up=close_up)


def render(df_all: pd.DataFrame, df_f: pd.DataFrame, f: Filters, events: pd.DataFrame, sil: pd.DataFrame, views: dict,
           names: dict, players: pd.DataFrame, positions: pd.DataFrame, objectives: pd.DataFrame, player_matches=None):
    """player_matches: partidas do jogador escolhido (None = toda a equipe).
    players (player_round) diz a equipe de cada jogador na partida; positions = posições no instante de cada abate;
    objectives = posições no instante do plant e do defuse."""
    team = f.team
    # placar e lista de partidas sem o filtro de lado, para refletir a partida inteira
    matches = team_matches(M.apply_filters(df_all, f.comps or None, f.maps or None, None), team)
    if player_matches is not None:
        matches = matches[matches["match_id"].isin(player_matches)]
        st.caption(f"Partidas em que {f.nick} jogou pela equipe. As linhas dele ficam destacadas na sequência de abates.")
    if matches.empty:
        st.info("Nenhuma partida do time com os filtros escolhidos.")
        return
    labels = {m.match_id: _match_label(m) for m in matches.itertuples()}
    mid = st.selectbox(f"Partida ({len(matches)})", matches["match_id"].tolist(), format_func=labels.get, key=f"pr_match_{team}_{hash(tuple(matches.match_id))}")
    m = matches.set_index("match_id").loc[mid]

    rr = df_all[(df_all["match_id"] == mid) & (df_all["team"] == team)].sort_values("round_num").copy()
    att, dfn = rr[rr["role"] == "Attacker"], rr[rr["role"] == "Defender"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Placar", f"{m.won} x {m.lost}", {"V": "vitória", "D": "derrota", "E": "empate"}[m.result], delta_color="off")
    c2.metric("No ataque", f"{int(att['won'].sum())} de {len(att)}", pct(att["won"].mean()) if len(att) else None, delta_color="off")
    c3.metric("Na defesa", f"{int(dfn['won'].sum())} de {len(dfn)}", pct(dfn["won"].mean()) if len(dfn) else None, delta_color="off")
    c4.metric("Primeiros abates", f"{int(rr['first_kill'].sum())} de {int(rr['has_fk'].sum())}",
              pct(rr["first_kill"].sum() / rr["has_fk"].sum()) if rr["has_fk"].sum() else None, delta_color="off")
    d, t = int(rr["deaths_tradeable"].sum()), int(rr["deaths_traded"].sum())
    c5.metric("Mortes trocadas", f"{t} de {d}", pct(t / d) if d else None, delta_color="off",
              help="Mortes do seu time vingadas por um aliado em até 5 s / mortes do seu time com aliado vivo na partida. "
                   "A morte do último vivo fica de fora: não havia quem trocasse.")

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
    if sil.empty or events.empty or positions.empty or players.empty or m.map_name not in views:
        st.info("Faltam os dados de posição. Gere-os com `python src/ingestion/build_features.py --processed data/processed`.")
    else:
        pm = players[players["match_id"] == mid]
        team_of = dict(zip(pm["puuid"], pm["team"]))
        _round_detail(r, ev, sil[sil["map_name"] == m.map_name], views[m.map_name], team, names, f.puuid,
                      positions[positions["match_id"] == mid],
                      objectives[objectives["match_id"] == mid] if not objectives.empty else objectives, team_of)

    with st.expander("Números da partida comparados com a referência"):
        st.caption(f"Referência: os outros times em {m.map_name}, com os filtros de competição e lado da barra lateral. "
                   "Uma partida descreve o que aconteceu, mas não confirma padrão.")
        mf = match_frame(df_f, team, mid, m.map_name)
        if mf[mf["team"] == team].empty:
            st.info("Sem rounds desta partida com o filtro de lado escolhido.")
        else:
            show_metrics_table(M.team_metrics(mf, team))
