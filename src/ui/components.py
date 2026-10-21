"""Componentes reutilizados pelas abas: cabeçalho, tabela de evidências e cartão de insight."""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.insights import engine as D
from src.ui.formatting import ROLE_PT, num, pct, team_name
from src.ui.sidebar import Filters

QUAL = {"ponto_forte": ("Ponto forte", "✓", "#0ca30c"), "ponto_de_atencao": ("Ponto de atenção", "!", "#d03b3b"),
        "misto": ("Contraste", "⇄", "#2a78d6")}


def header(df_all: pd.DataFrame, mine: pd.DataFrame, f: Filters):
    n_rounds, n_matches = len(mine), mine["match_id"].nunique()
    st.title(team_name(f.team))
    filt = " · ".join(x for x in [", ".join(f.comps) if f.comps else "todas as competições",
                                  ", ".join(f.maps) if f.maps else "todos os mapas", f.side.lower() if f.role else ""] if x)
    st.markdown(f'<p class="sub">{n_rounds} rounds em {n_matches} partidas · {filt}</p>', unsafe_allow_html=True)

    ctx = M.apply_filters(df_all, f.comps or None, f.maps or None, None)  # contexto: sem filtro de lado
    c1, c2, c3 = st.columns(3)
    for col, (label, r) in zip((c1, c2, c3), [("Rounds vencidos", None), ("No ataque", "Attacker"), ("Na defesa", "Defender")]):
        a = ctx[ctx["team"] == f.team]; b = ctx[ctx["team"] != f.team]
        if r:
            a, b = a[a["role"] == r], b[b["role"] == r]
        if len(a):
            col.metric(label, pct(a["won"].mean()), f"{num((a['won'].mean() - b['won'].mean()) * 100, 1, True)} pp vs referência ({pct(b['won'].mean())})",
                       delta_color="off", help=f"{int(a['won'].sum())} de {len(a)} rounds. Contexto geral; não entra nos diagnósticos.")
    if n_matches < M.MIN_MATCHES:
        st.warning(f"Só {n_matches} partida(s) com esses filtros: poucos dados para afirmar padrões. "
                   "Os diagnósticos ficam desativados até haver amostra suficiente.")


READING = {"ponto_forte": "Ponto forte (confirmado)", "ponto_de_atencao": "Ponto de atenção (confirmado)",
           "em_linha": "Sem diferença confiável", "insuficiente": "Amostra pequena: não confirmado"}


def metrics_table(res: pd.DataFrame) -> pd.DataFrame:
    """Todas as métricas com dados, da melhor para a pior em relação à referência.
    Descritiva: mostra o que aconteceu mesmo quando a amostra não permite confirmar um padrão."""
    t = res[res["n"] > 0].copy()
    t["_good"] = t["delta_pp"].where(t["higher_better"], -t["delta_pp"])  # > 0 = melhor que a referência
    t = t.sort_values("_good", ascending=False)
    return pd.DataFrame({
        "Métrica": t["label"] + t["higher_better"].map({True: "", False: " (menor é melhor)"}),
        "Time": t["rate"] * 100,
        "Referência": t["ref_rate"] * 100,
        "Diferença": [f"{num(v, 1, True)} pp" for v in t["delta_pp"]],
        "Frente à referência": ["▲ melhor" if g > 0 else "▼ pior" if g < 0 else "= igual" for g in t["_good"]],
        "Amostra": [f"{int(x)} de {int(n)} {u}" for x, n, u in zip(t["x"], t["n"], t["unit"])],
        "Partidas": t["n_matches"].astype(int),
        "Leitura": t["quality"].map(READING),
    })


def pct_bar(label: str, help=None):
    """Coluna de taxa (0 a 100) exibida como barra, sem perder o número."""
    return st.column_config.ProgressColumn(label, format="%.1f%%", min_value=0, max_value=100, help=help)


def show_metrics_table(res: pd.DataFrame):
    st.dataframe(metrics_table(res), hide_index=True, width="stretch", column_config={
        "Time": pct_bar("Time"), "Referência": pct_bar("Referência", "Outros times, nas mesmas condições")})


def evidence_table(df_f: pd.DataFrame, team: str, key: str, quality):
    ev = D.evidence(df_f, team, key, quality)
    out = pd.DataFrame({
        "Data": pd.to_datetime(ev["match_date"]).dt.strftime("%d/%m/%Y"), "Competição": ev["competition"],
        "Mapa": ev["map_name"], "Adversário": ev["opponent"].map(team_name), "Round": ev["round_label"],
        "Lado": ev["role"].map(ROLE_PT), "Resultado": ev["resultado"], "O que aconteceu": ev["detalhe"]})
    return ev, out


def insight_card(i: dict, R: pd.DataFrame, df_f: pd.DataFrame, team: str):
    """R = resultado de team_metrics indexado por `key`."""
    label, icon, color = QUAL[i["quality"]]
    with st.container(border=True):
        st.markdown(f'<span class="chip" style="--c:{color}"><i>{icon}</i>{label}</span>'
                    f'<p class="ctitle">{i["title"]}</p><p class="ctext">{i["text"]}</p>', unsafe_allow_html=True)
        cols = st.columns(len(i["numbers"]))
        for col, nb in zip(cols, i["numbers"]):
            r = R.loc[nb["key"]]
            col.metric(
                nb["label"], pct(r.rate, 1),
                delta=f"{num(r.delta_pp, 1, True)} pp vs referência ({pct(r.ref_rate, 1)})",
                delta_color="normal" if r.higher_better else "inverse",
                help=f"{int(r.x)} de {int(r.n)} {r.unit} em {int(r.n_matches)} partidas. "
                     f"Intervalo de 95%: {pct(r.ci_low, 1)} a {pct(r.ci_high, 1)}.",
                label_visibility="visible" if len(i["numbers"]) > 1 else "collapsed")
        with st.expander("Ver os rounds que sustentam isso"):
            tabs = st.tabs([n["label"] for n in i["numbers"]]) if len(i["numbers"]) > 1 else [st.container()]
            for tb, nb in zip(tabs, i["numbers"]):
                with tb:
                    q = R.loc[nb["key"]].quality
                    ev, out = evidence_table(df_f, team, nb["key"], q)
                    what = "em que isso deu errado" if q == "ponto_de_atencao" else "em que isso deu certo"
                    st.caption(f"{len(out)} rounds {what}. Métrica: {R.loc[nb['key']].what}.")
                    st.dataframe(out, hide_index=True, width="stretch", height=min(360, 38 + 35 * len(out)))
