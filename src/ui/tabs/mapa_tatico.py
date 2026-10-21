"""Aba Mapa tático: onde o time morre, abate, abre o round e planta — desenhado com as coordenadas da própria base.

Não usa imagem de mapa: a silhueta são as posições de todos os jogadores no momento dos abates.
Selecionar pontos (clique, caixa ou laço) lista os rounds correspondentes.
"""
import pandas as pd
import streamlit as st

from src.analytics.objectives import plant_sites
from src.ui.charts import MAP_CONFIG, colors, sites_figure, tactical_map
from src.ui.formatting import ROLE_PT, pct, team_name

LAYERS = ["Mortes do time", "Abates do time", "Primeiro duelo", "Plants (ataque)", "Plants sofridos (defesa)"]
ROUND_COLS = ["match_id", "round_num", "match_date", "opponent", "round_label", "role", "won"]


def _hover(df: pd.DataFrame, what) -> list:
    when = pd.to_datetime(df["match_date"]).dt.strftime("%d/%m/%Y")
    return [f"<b>{w}</b><br>{d} · vs {team_name(o)} · round {r} · {ROLE_PT[ro]} · {'venceu' if won else 'perdeu'}"
            for w, d, o, r, ro, won in zip(what, when, df["opponent"], df["round_label"], df["role"], df["won"])]


def _secs(ms) -> list:
    return [f"{int(v) // 1000}s" if pd.notna(v) else "—" for v in ms]


def _layers(layer: str, ev: pd.DataFrame, tr: pd.DataFrame, team: str, puuid=None):
    """Retorna (camadas para o gráfico, DataFrame de cada camada com uma coluna 'detalhe').
    puuid: restringe ao jogador (mortes dele, abates dele, duelos de abertura dele, plants feitos por ele)."""
    C = colors()
    out = []

    def add(name, df, x, y, color, what, symbol="circle"):
        df = df.assign(detalhe=list(what))
        df = df[df[x].notna()]
        out.append((dict(name=f"{name} ({len(df)})", x=df[x], y=df[y], color=color, symbol=symbol,
                         hover=_hover(df, df["detalhe"])), df))

    if layer == "Mortes do time":
        d = ev[ev["victim_puuid"] == puuid] if puuid else ev[ev["victim_team"] == team]
        traded = d["death_was_traded"]
        # último vivo do time: não havia quem trocasse (fora de "Mortes trocadas"); cinza = fora da conta
        last = ~traded & (d["victim_allies_alive"] == 0) if "victim_allies_alive" in d else traded & False
        isolated = ~traded & ~last & d["isolated"]
        for name, m, color in [("Trocada", traded, C["s1"]), ("Isolada, sem troca", isolated, C["s2"]),
                               ("Sem troca", ~traded & ~isolated & ~last, C["s3"]),
                               ("Sem aliado vivo", last, C["ref"])]:
            sub = d[m]
            add(name, sub, "victim_x", "victim_y", color,
                [f"Morte {name.lower()} aos {s}" for s in _secs(sub["time_in_round_ms"])])
    elif layer == "Abates do time":
        a = ev[ev["killer_puuid"] == puuid] if puuid else ev[ev["killer_team"] == team]
        for name, m, color in [("Abate de troca", a["is_trade_kill"], C["s1"]), ("Outros abates", ~a["is_trade_kill"], C["s2"])]:
            sub = a[m]
            add(name, sub, "killer_x", "killer_y", color,
                [f"{name} aos {s} (posição de quem abateu)" for s in _secs(sub["time_in_round_ms"])])
    elif layer == "Primeiro duelo":
        f = ev[ev["is_first_kill"]]
        if puuid:
            f = f[(f["killer_puuid"] == puuid) | (f["victim_puuid"] == puuid)]
        for name, m, color in [("Primeiro abate do time", f["killer_team"] == team, C["s1"]),
                               ("Primeira morte do time", f["victim_team"] == team, C["s2"])]:
            sub = f[m]
            add(name, sub, "victim_x", "victim_y", color,
                [f"{name} aos {s} (posição de quem caiu)" for s in _secs(sub["time_in_round_ms"])])
    else:
        role = "Attacker" if layer == "Plants (ataque)" else "Defender"
        p = tr[(tr["role"] == role) & tr["bomb_planted"].astype(bool)]
        if puuid and role == "Attacker":
            p = p[p["planter_puuid"] == puuid]
        for site, color in zip(sorted(p["plant_site"].dropna().unique()), [C["s1"], C["s2"], C["s3"]]):
            for won, symbol, res in [(True, "circle", "vencido"), (False, "x", "perdido")]:
                sub = p[(p["plant_site"] == site) & (p["won"] == won)]
                add(f"Site {site} · round {res}", sub, "plant_x", "plant_y", color,
                    [f"Plant no site {site} aos {s} · round {res}" for s in _secs(sub["plant_time_ms"])], symbol)
    return out


def _selected_rounds(event, frames: list) -> pd.DataFrame:
    rows = []
    for pt in (event.selection.get("points", []) if event else []):
        k = pt.get("curve_number", 0) - 1  # traço 0 é a silhueta
        i = pt.get("point_index", pt.get("point_number"))
        if 0 <= k < len(frames) and i is not None and i < len(frames[k]):
            rows.append(frames[k].iloc[i])
    if not rows:
        return pd.DataFrame()
    s = pd.DataFrame(rows).sort_values(["match_date", "match_id", "round_num"])
    return pd.DataFrame({
        "Data": pd.to_datetime(s["match_date"]).dt.strftime("%d/%m/%Y"), "Adversário": s["opponent"].map(team_name),
        "Round": s["round_label"], "Lado": s["role"].map(ROLE_PT), "Resultado": s["won"].map({True: "Venceu", False: "Perdeu"}),
        "O que aconteceu": s["detalhe"]})


def _sites(df_map: pd.DataFrame, team: str, mp: str):
    st.markdown(f"**Plants por site em {mp}**")
    ps = plant_sites(df_map, team)
    if ps.empty or ps["plants"].sum() == 0:
        st.info("O time não plantou neste recorte (o filtro de lado em defesa remove os rounds de ataque).")
        return
    c1, c2 = st.columns(2)
    c1.plotly_chart(sites_figure(ps, "share", "ref_share", "Onde o time planta (% dos plants)"),
                    width="stretch", theme=None, config={"displayModeBar": False})
    c2.plotly_chart(sites_figure(ps, "win_rate", "ref_win_rate", "Rounds vencidos depois de plantar"),
                    width="stretch", theme=None, config={"displayModeBar": False})
    st.dataframe(pd.DataFrame({
        "Site": ps["site"],
        "Plants do time": [f"{p} ({pct(s)})" for p, s in zip(ps["plants"], ps["share"])],
        "Vencidos após plant": [f"{w} de {p} ({pct(r)})" if p else "—" for w, p, r in zip(ps["wins"], ps["plants"], ps["win_rate"])],
        "Referência: plants": [f"{p} ({pct(s)})" for p, s in zip(ps["ref_plants"], ps["ref_share"])],
        "Referência: vencidos após plant": [f"{w} de {p} ({pct(r)})" for w, p, r in zip(ps["ref_wins"], ps["ref_plants"], ps["ref_win_rate"])],
    }), hide_index=True, width="stretch")
    st.caption(f"Referência: os outros times em {mp}, com os mesmos filtros. Mesma regra da métrica pós-plant, aberta por site.")


def render(df_f: pd.DataFrame, team: str, events: pd.DataFrame, sil: pd.DataFrame, views: dict, puuid=None, nick=None):
    if events.empty or sil.empty or not views:
        st.info("Faltam os dados de posição. Gere-os com `python src/ingestion/build_features.py --processed data/processed`.")
        return
    mine = df_f[df_f["team"] == team]
    played = mine.groupby("map_name")["match_id"].nunique().sort_values(ascending=False)
    c1, c2 = st.columns([1, 1])
    mp = c1.segmented_control("Mapa", played.index.tolist(), default=played.index[0], key=f"tm_map_{team}_{hash(tuple(played.index))}",
                              format_func=lambda m: f"{m} ({played[m]})") or played.index[0]
    layer = c2.segmented_control("Camada", LAYERS, default=LAYERS[0], key="tm_layer") or LAYERS[0]

    tr = mine[mine["map_name"] == mp]
    ev = events[events["map_name"] == mp].merge(tr[ROUND_COLS], on=["match_id", "round_num"])
    built = _layers(layer, ev, tr, team, puuid)
    if puuid:
        team_layer = " Em plants sofridos na defesa, a camada é da equipe." if layer == "Plants sofridos (defesa)" else ""
        st.info(f"Mostrando apenas **{nick}**.{team_layer} Escolha “Toda a equipe” na barra lateral para ver o time inteiro.")
    n_matches = tr["match_id"].nunique()
    st.caption(f"{n_matches} partida(s) e {len(tr)} rounds do time em {mp}, com os filtros da barra lateral. "
               "O mapa é desenhado pelas posições de todos os jogadores registradas na base. "
               "Clique, arraste uma caixa ou desenhe um laço para listar os rounds dos pontos. "
               "Roda do mouse dá zoom; duplo clique volta ao mapa inteiro.")
    event = st.plotly_chart(tactical_map(sil[sil["map_name"] == mp], [b[0] for b in built], views[mp]), width="stretch",
                            theme=None, on_select="rerun", selection_mode=("points", "box", "lasso"),
                            key=f"tm_chart_{mp}_{layer}", config=MAP_CONFIG)
    sel = _selected_rounds(event, [b[1] for b in built])
    if sel.empty:
        st.caption("Nenhum ponto selecionado.")
    else:
        st.markdown(f"**{len(sel)} ponto(s) selecionado(s)**")
        st.dataframe(sel, hide_index=True, width="stretch", height=min(360, 38 + 35 * len(sel)))

    st.divider()
    _sites(df_f[df_f["map_name"] == mp], team, mp)
