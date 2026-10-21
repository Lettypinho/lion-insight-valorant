"""Aba Jogadores: elenco do time, destaques de cada jogador e a análise do jogador escolhido na barra lateral.

Referência de um jogador = todos os outros jogadores do recorte (mesmos filtros de competição, mapa e lado).
Métricas de perfil (ex.: participação no duelo de abertura) dependem da função do jogador: viram "perfil",
nunca ponto forte ou de atenção.
"""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.analytics import kill_types as K
from src.analytics import players as P
from src.analytics import weapons as W
from src.ui.charts import comparison_figure
from src.ui.components import evidence_table, insight_card, pct_bar, show_kind_table, show_metrics_table
from src.ui.sidebar import Filters


def _labels(res: pd.DataFrame, qualities) -> str:
    return ", ".join(res.loc[res["quality"].isin(qualities), "label"]) or "—"


def _roster(df_p: pd.DataFrame, f: Filters, names: dict, by_player: dict):
    ro = P.roster(df_p, f.team)
    st.dataframe(pd.DataFrame({
        "Jogador": ro["puuid"].map(names).fillna("?"),
        "Partidas": ro["partidas"], "Rounds": ro["rounds"], "Abates": ro["abates"], "Mortes": ro["mortes"],
        "K/D": ro["kd"].round(2), "Dano por round": ro["adr"].round(0),
        "Primeiros abates": ro["primeiros_abates"], "Primeiras mortes": ro["primeiras_mortes"],
        "Vitória no duelo de abertura": ro["open_win"] * 100,
        "Abates com habilidade": ro["abates_habilidade"], "Mortes por habilidade": ro["mortes_habilidade"],
        "Pontos fortes confirmados": [_labels(by_player[p][0], ["ponto_forte"]) for p in ro["player"]],
        "Pontos de atenção confirmados": [_labels(by_player[p][0], ["ponto_de_atencao"]) for p in ro["player"]],
        "Perfil": [_labels(by_player[p][0], ["perfil_acima", "perfil_abaixo"]) for p in ro["player"]],
    }), hide_index=True, width="stretch", column_config={
        "Vitória no duelo de abertura": pct_bar("Vitória no duelo de abertura", "Primeiros abates / (primeiros abates + primeiras mortes)"),
        "Dano por round": st.column_config.NumberColumn("Dano por round", help="Dano causado / rounds jogados"),
    })
    st.caption("Contagens consideram só abates sobre inimigos. Os pontos confirmados comparam cada jogador com todos os "
               "outros jogadores do recorte e seguem o mesmo critério estatístico das equipes.")


def _kinds(kills: pd.DataFrame, deaths: pd.DataFrame, f: Filters):
    """Como mata e como morre: do jogador escolhido ou, sem jogador, do time."""
    if f.puuid:
        bd = K.breakdown(kills, deaths, (kills["killer_puuid"] == f.puuid) & (kills["killer_team"] == f.team),
                         (deaths["victim_puuid"] == f.puuid) & (deaths["victim_team"] == f.team))
        st.markdown(f"**Como {f.nick} mata e como morre**")
        show_kind_table(bd, "do jogador")
    else:
        bd = K.breakdown(kills, deaths, kills["killer_team"] == f.team, deaths["victim_team"] == f.team)
        st.markdown("**Como o time mata e como morre**")
        show_kind_table(bd, "do time")


def _weapons(kills: pd.DataFrame, deaths: pd.DataFrame, df_p: pd.DataFrame, f: Filters, ref: pd.DataFrame):
    """Com qual arma mata e morre, e o rendimento com a arma principal do round: do jogador ou, sem jogador, do time."""
    if f.puuid:
        mk = (kills["killer_puuid"] == f.puuid) & (kills["killer_team"] == f.team)
        md = (deaths["victim_puuid"] == f.puuid) & (deaths["victim_team"] == f.team)
        mine, who, unit = df_p["player"] == f.player, "do jogador", "rounds"
        st.markdown(f"**Armas de {f.nick}**")
    else:
        mk, md = kills["killer_team"] == f.team, deaths["victim_team"] == f.team
        mine, who, unit = df_p["team"] == f.team, "do time", "rounds-jogador"
        st.markdown("**Armas do time**")

    def cat(s):
        return s.map(ref["categoria"]).fillna("—")

    view = st.segmented_control("Ver", ["Com qual arma mata e morre", "Rendimento com a arma do round"],
                                default="Com qual arma mata e morre", key="weapon_view", label_visibility="collapsed")
    if view == "Rendimento com a arma do round":
        wr = W.weapon_rounds(df_p, mine)
        st.dataframe(pd.DataFrame({
            "Arma": wr["weapon"], "Categoria": cat(wr["weapon"]), unit.capitalize(): wr["rounds"],
            "Abates por round": wr["kpr"].round(2), "Referência (abates por round)": wr["kpr_ref"].round(2),
            "Sobrevivência": wr["survival"] * 100, "Referência (sobrevivência)": wr["survival_ref"] * 100,
            "Vitória do round": wr["win"] * 100, "Referência (vitória)": wr["win_ref"] * 100,
            "Amostra": ["pequena" if n < M.MIN_N else "" for n in wr["rounds"]],
        }), hide_index=True, width="stretch", column_config={
            c: pct_bar(c) for c in ["Sobrevivência", "Referência (sobrevivência)", "Vitória do round", "Referência (vitória)"]})
        st.caption(f"Arma principal de cada round ({unit}). Referência: os outros, no mesmo recorte, **com a mesma arma**. "
                   f"Menos de {M.MIN_N} {unit} = amostra pequena. A vitória do round depende muito da economia (fuzil "
                   "costuma vir com compra cheia): o número descreve, não diz que a arma ganha rounds.")
    else:
        bd = W.kill_breakdown(kills, deaths, mk, md)
        st.dataframe(pd.DataFrame({
            "Arma": bd["weapon"], "Categoria": cat(bd["weapon"]),
            f"Abates {who}": bd["kills"], "% dos abates": bd["kills_share"] * 100,
            "Referência (abates)": bd["ref_kills_share"] * 100,
            f"Mortes {who}": bd["deaths"], "% das mortes": bd["deaths_share"] * 100,
            "Referência (mortes)": bd["ref_deaths_share"] * 100,
        }), hide_index=True, width="stretch", column_config={
            c: pct_bar(c) for c in ["% dos abates", "Referência (abates)", "% das mortes", "Referência (mortes)"]})
        st.caption(f"{bd.attrs['n_kills']} abates e {bd.attrs['n_deaths']} mortes com item identificado no recorte: armas, faca "
                   "e as habilidades que funcionam como arma (Headhunter e Tour de Force do Chamber, Overdrive da Neon). "
                   "As demais habilidades não têm nome na base e aparecem só na tabela de tipo de abate, acima. "
                   "Referência: todos os outros, nas mesmas condições.")


def _player(df_p: pd.DataFrame, f: Filters, res: pd.DataFrame, dg: dict):
    mine = df_p[df_p["player"] == f.player]
    R = res.set_index("key")
    n_matches = mine["match_id"].nunique()
    st.subheader(f.nick or "Jogador")
    st.caption(f"{n_matches} partida(s) e {len(mine)} rounds pela equipe neste recorte. "
               "Referência: todos os outros jogadores, com os mesmos filtros.")
    if n_matches < M.MIN_MATCHES:
        st.warning(f"Amostra pequena: {n_matches} partida(s). Os números descrevem o que aconteceu, mas não confirmam padrão.")
    ins = dg["insights"]
    good = [i for i in ins if i["quality"] == "ponto_forte"]
    bad = [i for i in ins if i["quality"] == "ponto_de_atencao"]
    prof = [i for i in ins if i["quality"] == "perfil"]
    if not ins and n_matches >= M.MIN_MATCHES:
        st.info("Nenhuma diferença confirmada em relação aos outros jogadores neste recorte.")
    if good or bad:
        left, right = st.columns(2)
        with left:
            st.markdown("**O que está funcionando**")
            if not good:
                st.caption("Nenhum ponto forte confirmado.")
            for i in good:
                insight_card(i, R, df_p, f.player, "player")
        with right:
            st.markdown("**O que precisa de atenção**")
            if not bad:
                st.caption("Nenhum ponto de atenção confirmado.")
            for i in bad:
                insight_card(i, R, df_p, f.player, "player")
    if prof:
        st.markdown("**Perfil** — depende da função do jogador; não é bom nem ruim por si só")
        cols = st.columns(len(prof))
        for col, i in zip(cols, prof):
            with col:
                insight_card(i, R, df_p, f.player, "player")

    st.markdown("**Todos os números do jogador** — do melhor para o pior em relação à referência")
    show_metrics_table(res)
    with st.expander("Ver como gráfico"):
        st.plotly_chart(comparison_figure(res), width="stretch", theme=None, config={"displayModeBar": False})
    with st.expander("Ver os rounds de uma métrica"):
        available = res.loc[res["n"] > 0, "key"].tolist()
        if available:
            key = st.selectbox("Métrica", available, format_func=lambda k: P.BY_KEY[k].label, key=f"pev_{f.player}")
            _, out = evidence_table(df_p, f.player, key, None, "player")
            st.caption(f"{P.BY_KEY[key].what}. {len(out)} rounds.")
            st.dataframe(out, hide_index=True, width="stretch", height=min(360, 38 + 35 * len(out)))


def render(players: pd.DataFrame, f: Filters, names: dict, by_player: dict, events: pd.DataFrame, df_f: pd.DataFrame,
           weapon_ref: pd.DataFrame):
    """events: kill_events; df_f: team_round com os filtros da barra lateral (define o recorte dos abates);
    weapon_ref: categoria e preço de cada arma."""
    if players.empty:
        st.info("Faltam os dados por jogador. Gere-os com `python src/ingestion/build_features.py --processed data/processed`.")
        return
    df_p = M.apply_filters(players, f.comps or None, f.maps or None, f.role)
    if df_p[df_p["team"] == f.team].empty:
        st.info("Nenhum round do time com os filtros escolhidos.")
        return
    st.subheader("Elenco")
    _roster(df_p, f, names, by_player)
    if not events.empty and "kill_kind" in events.columns:
        # abates feitos no recorte (lado de quem abateu) e mortes sofridas (lado de quem morreu)
        kills, deaths = K.in_scope(events, df_f, "killer"), K.in_scope(events, df_f, "victim")
        _kinds(kills, deaths, f)
        if "weapon" in events.columns and "weapon" in df_p.columns:
            _weapons(kills, deaths, df_p, f, weapon_ref)
    if f.player and f.player in by_player:
        st.divider()
        _player(df_p, f, *by_player[f.player])
    else:
        st.info("Escolha um jogador na barra lateral para ver os insights dele, o mapa tático e as partidas filtrados por ele.")
