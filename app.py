"""
Raio-X de time: como um time joga em relação à competição, com os rounds que provam.

Rodar (da raiz do projeto):   python -m streamlit run app.py
Dados: apenas data/processed/team_round.csv (gerado a partir dos JSONs fornecidos pela organização).
Tudo e pos-partida: nada aqui interfere em partidas em andamento.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.insights import engine as D  # noqa: E402
from src.analytics import metrics as M  # noqa: E402

DATA = Path(os.environ.get("TEAM_ROUND_CSV", ROOT / "data" / "processed" / "team_round.csv"))
ACRONYMS = {"a2e", "bbn", "caap", "ceub", "fatec", "fei", "gc", "gdu", "ibmec", "iff", "ime", "pg", "pucc",
            "pucgo", "uff", "ufg", "ufmg", "ufmt", "ufpb", "ufpr", "ufrj", "ufu", "umc", "uscs", "usp", "utfpr"}
ROLE_PT = {"Attacker": "Ataque", "Defender": "Defesa"}
ROLE_EN = {"Ataque": "Attacker", "Defesa": "Defender", "Todos": None}

st.set_page_config(page_title="Raio-X de time", layout="wide", initial_sidebar_state="auto")


# ------------------------------------------------------------------ utilidades
def team_name(slug: str) -> str:
    return " ".join(t.upper() if t in ACRONYMS else t.capitalize() for t in slug.split("_"))


def pct(v, d=0):
    return "—" if v is None or pd.isna(v) else f"{v * 100:.{d}f}".replace(".", ",") + "%"


def num(v, d=1, sign=False):
    s = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
    return s.replace(".", ",")


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    return M.load(DATA.parent) if DATA.name == "team_round.csv" else pd.read_csv(DATA)


@st.cache_data(show_spinner=False)
def compute(team, comps, maps, role):
    df = M.apply_filters(load_data(), list(comps) or None, list(maps) or None, role)
    res = M.team_metrics(df, team)
    return res, D.diagnose(res)


if not DATA.exists():
    st.error(f"Não encontrei {DATA}. Gere os dados antes: `python src/ingestion/build_features.py --processed data/processed`")
    st.stop()

# ------------------------------------------------------------------ estilo
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap');
/* fonte so nos textos: NAO usar seletor generico, senao quebra a fonte de icones do Streamlit */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp td, .stApp th, .stApp button, .stApp input, .stApp textarea,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDelta"],
[data-testid="stExpander"] summary p { font-family: 'Figtree', system-ui, sans-serif; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
h1 { font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.1rem; }
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; font-weight: 650; }
.sub { opacity: .72; font-size: .95rem; margin: 0 0 1.1rem 0; }
.chip { display:inline-flex; align-items:center; gap:.4rem; font-size:.78rem; font-weight:600;
        padding:.12rem .6rem; border-radius:999px; margin-bottom:.45rem;
        border:1px solid color-mix(in srgb, var(--c) 60%, transparent);
        background: color-mix(in srgb, var(--c) 13%, transparent); }
.chip i { color: var(--c); font-style: normal; font-weight:800; }
.ctitle { font-size:1.08rem; font-weight:650; margin:0 0 .15rem 0; }
.ctext  { margin:0 0 .6rem 0; line-height:1.45; }
.note   { opacity:.7; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

df_all = load_data()
teams = M.list_teams(df_all)

# ------------------------------------------------------------------ filtros
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
    role = ROLE_EN[side]
    st.caption("A referência é sempre formada pelos **outros times**, nas mesmas condições dos filtros acima.")
    st.caption("Dados: somente os JSONs fornecidos pela organização. Análise pós-partida.")

df_f = M.apply_filters(df_all, comps or None, maps or None, role)
mine = df_f[df_f["team"] == team]
if mine.empty:
    st.title(team_name(team))
    st.info("Esse time não tem rounds com os filtros escolhidos. Amplie a competição, o mapa ou o lado.")
    st.stop()

res, dg = compute(team, tuple(comps), tuple(maps), role)
n_rounds, n_matches = len(mine), mine["match_id"].nunique()

# ------------------------------------------------------------------ cabeçalho
st.title(team_name(team))
filt = " · ".join(x for x in [", ".join(comps) if comps else "todas as competições",
                              ", ".join(maps) if maps else "todos os mapas", side.lower() if role else ""] if x)
st.markdown(f'<p class="sub">{n_rounds} rounds em {n_matches} partidas · {filt}</p>', unsafe_allow_html=True)

ctx = M.apply_filters(df_all, comps or None, maps or None, None)  # contexto: sem filtro de lado
c1, c2, c3 = st.columns(3)
for col, (label, r) in zip((c1, c2, c3), [("Rounds vencidos", None), ("No ataque", "Attacker"), ("Na defesa", "Defender")]):
    a = ctx[ctx["team"] == team]; b = ctx[ctx["team"] != team]
    if r:
        a, b = a[a["role"] == r], b[b["role"] == r]
    if len(a):
        col.metric(label, pct(a["won"].mean()), f"{num((a['won'].mean() - b['won'].mean()) * 100, 1, True)} pp vs referência ({pct(b['won'].mean())})",
                   delta_color="off", help=f"{int(a['won'].sum())} de {len(a)} rounds. Contexto geral; não entra nos diagnósticos.")
if n_matches < M.MIN_MATCHES:
    st.warning(f"Só {n_matches} partida(s) com esses filtros: poucos dados para afirmar padrões. "
               "Os diagnósticos ficam desativados até haver amostra suficiente.")

tab_diag, tab_comp, tab_rounds, tab_met = st.tabs(["Diagnóstico", "Comparação com a competição", "Rounds de evidência", "Metodologia"])

QUAL = {"ponto_forte": ("Ponto forte", "✓", "#0ca30c"), "ponto_de_atencao": ("Ponto de atenção", "!", "#d03b3b"),
        "misto": ("Contraste", "⇄", "#2a78d6")}
R = res.set_index("key")


def evidence_table(key, quality):
    ev = D.evidence(df_f, team, key, quality)
    out = pd.DataFrame({
        "Data": pd.to_datetime(ev["match_date"]).dt.strftime("%d/%m/%Y"), "Competição": ev["competition"],
        "Mapa": ev["map_name"], "Adversário": ev["opponent"].map(team_name), "Round": ev["round_label"],
        "Lado": ev["role"].map(ROLE_PT), "Resultado": ev["resultado"], "O que aconteceu": ev["detalhe"]})
    return ev, out


def insight_card(i, key_prefix):
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
                    ev, out = evidence_table(nb["key"], q)
                    what = "em que isso deu errado" if q == "ponto_de_atencao" else "em que isso deu certo"
                    st.caption(f"{len(out)} rounds {what}. Métrica: {R.loc[nb['key']].what}.")
                    st.dataframe(out, hide_index=True, width="stretch", height=min(360, 38 + 35 * len(out)))


# ------------------------------------------------------------------ aba 1: diagnóstico
with tab_diag:
    ins = dg["insights"]
    if not ins:
        st.info("Nenhuma diferença confiável em relação à competição com esse recorte. "
                "Isso é um resultado: o time joga perto da média. Para achar padrões, amplie os filtros "
                "(mais competições ou mapas) ou escolha um time com mais partidas.")
    mixed = [i for i in ins if i["quality"] == "misto" or len(i["keys"]) > 1]
    rest = [i for i in ins if i not in mixed]
    if mixed:
        st.subheader("Padrões do time")
        for k, i in enumerate(mixed):
            insight_card(i, f"m{k}")
    good = [i for i in rest if i["quality"] == "ponto_forte"]
    bad = [i for i in rest if i["quality"] == "ponto_de_atencao"]
    if good or bad:
        left, right = st.columns(2)
        with left:
            st.subheader("O que está funcionando")
            if not good:
                st.caption("Nenhum ponto forte confiável isolado.")
            for k, i in enumerate(good):
                insight_card(i, f"g{k}")
        with right:
            st.subheader("O que precisa de atenção")
            if not bad:
                st.caption("Nenhum ponto de atenção confiável isolado.")
            for k, i in enumerate(bad):
                insight_card(i, f"b{k}")
    with st.expander("O que o sistema não conseguiu afirmar"):
        nt = dg["notes"]
        st.markdown("**Sem diferença confiável da referência:** " + (", ".join(nt["em_linha"]) or "—"))
        st.markdown("**Amostra insuficiente:** " + (", ".join(nt["insuficiente"]) or "—"))
        st.markdown("**Não se aplica ao recorte** (por exemplo, retake no filtro de ataque): " + (", ".join(nt["sem_dados"]) or "—"))
    st.caption("São indícios, não sentenças: com 11 comparações por time, algum resultado pode aparecer por acaso.")


# ------------------------------------------------------------------ aba 2: comparação
def comparison_figure(res):
    dark = is_dark()
    C = dict(text="#f0efec" if dark else "#0b0b0b", muted="#c3c2b7" if dark else "#52514e",
             grid="#2b2b29" if dark else "#e7e6e2", surface="#1a1a19" if dark else "#fcfcfb",
             team="#3987e5" if dark else "#2a78d6", ref="#a3a29a" if dark else "#73726d")
    ys, ticktext, tickvals, rows = 0, [], [], []
    last_group = None
    for _, r in res.iterrows():
        if r.group != last_group:
            ys += 1
            tickvals.append(ys); ticktext.append(f"<b>{r.group}</b>")
            last_group = r.group
        ys += 1
        label = r.label + (" (menor é melhor)" if not r.higher_better else "")
        tickvals.append(ys); ticktext.append(label)
        rows.append((ys, r))
    fig = go.Figure()
    ok = [(y, r) for y, r in rows if r.n > 0]
    # referência: traço cinza
    fig.add_trace(go.Scatter(
        x=[r.ref_rate * 100 for _, r in ok], y=[y for y, _ in ok], mode="markers", name="Referência (outros times)",
        marker=dict(symbol="line-ns", size=18, line=dict(width=3, color=C["ref"])),
        customdata=[[r.ref_n, r.label] for _, r in ok],
        hovertemplate="<b>%{customdata[1]}</b><br>Referência: %{x:.1f}%<br>%{customdata[0]} rounds/eventos<extra></extra>"))
    # time: ponto + intervalo; cheio = diferença confiável, vazado = sem diferença confiável
    reliable = [r.verdict in ("acima", "abaixo") for _, r in ok]
    lo = [(r.rate - r.ci_low) * 100 if pd.notna(r.ci_low) else 0 for _, r in ok]
    hi = [(r.ci_high - r.rate) * 100 if pd.notna(r.ci_high) else 0 for _, r in ok]
    fig.add_trace(go.Scatter(
        x=[r.rate * 100 for _, r in ok], y=[y for y, _ in ok], mode="markers", name="Time",
        error_x=dict(type="data", symmetric=False, array=hi, arrayminus=lo, thickness=2, width=0, color=C["team"]),
        marker=dict(size=12, color=[C["team"] if k else C["surface"] for k in reliable],
                    line=dict(width=2.5, color=[C["surface"] if k else C["team"] for k in reliable])),
        customdata=[[r.label, r.x, r.n, r.n_matches, (r.ci_low or 0) * 100, (r.ci_high or 0) * 100, r.verdict] for _, r in ok],
        hovertemplate=("<b>%{customdata[0]}</b><br>Time: %{x:.1f}% (%{customdata[1]} de %{customdata[2]}, "
                       "%{customdata[3]} partidas)<br>Intervalo de 95%%: %{customdata[4]:.1f}%% a %{customdata[5]:.1f}%%<extra></extra>")))
    sym = {"acima": "▲ acima", "abaixo": "▼ abaixo", "em_linha": "= em linha", "insuficiente": "poucos dados", "sem_dados": "não se aplica"}
    for y, r in rows:
        fig.add_annotation(x=1.01, xref="paper", y=y, yref="y", text=sym[r.verdict], showarrow=False, xanchor="left",
                           font=dict(size=12, color=C["text"] if r.verdict in ("acima", "abaixo") else C["muted"]))
    fig.update_layout(
        height=max(380, 36 * ys + 70), margin=dict(l=20, r=110, t=10, b=40), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Figtree, system-ui, sans-serif", size=13, color=C["text"]),
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(color=C["muted"])), hovermode="closest",
        xaxis=dict(range=[0, 100], ticksuffix="%", gridcolor=C["grid"], gridwidth=1, zeroline=False, tickfont=dict(color=C["muted"])),
        yaxis=dict(automargin=True, tickmode="array", tickvals=tickvals, ticktext=ticktext, autorange="reversed", showgrid=False,
                   zeroline=False, tickfont=dict(color=C["text"])))
    return fig


with tab_comp:
    st.markdown("**Cada linha compara o time com os outros times da competição.** "
                "O ponto é a taxa do time e a barra é o intervalo de confiança de 95%; o traço cinza é a referência.")
    st.plotly_chart(comparison_figure(res), width="stretch", theme=None, config={"displayModeBar": False})
    st.caption("Ponto cheio: diferença confiável. Ponto vazado: sem diferença confiável (ou poucos dados). "
               "O texto à direita repete isso sem depender de cor.")
    with st.expander("Ver como tabela"):
        t = res[res["n"] > 0].copy()
        tab = pd.DataFrame({
            "Métrica": t["label"], "Time": (t["rate"] * 100).round(1), "Referência": (t["ref_rate"] * 100).round(1),
            "Diferença (pp)": t["delta_pp"].round(1), "Intervalo 95%": [f"{num(a * 100)} a {num(b * 100)}" if pd.notna(a) else "—" for a, b in zip(t["ci_low"], t["ci_high"])],
            "n": t["n"], "Partidas": t["n_matches"],
            "Posição entre os times (percentil)": t["percentile"].round(0),
            "Leitura": t["verdict"].map({"acima": "acima", "abaixo": "abaixo", "em_linha": "em linha", "insuficiente": "poucos dados"})})
        st.dataframe(tab, hide_index=True, width="stretch")


# ------------------------------------------------------------------ aba 3: rounds
with tab_rounds:
    st.markdown("Escolha uma métrica e veja os rounds do time que a compõem, para conferir o que está por trás de cada número.")
    k1, k2 = st.columns([2, 1])
    key = k1.selectbox("Métrica", [m.key for m in M.METRICS], format_func=lambda k: M.BY_KEY[k].label)
    show = k2.radio("Mostrar", ["Todos", "Bons para o time", "Ruins para o time"], horizontal=True)
    ev, out = evidence_table(key, None)
    if show != "Todos":
        mask = ev["bom_para_o_time"] if show == "Bons para o time" else ~ev["bom_para_o_time"]
        ev, out = ev[mask], out[mask.to_numpy()]
    st.caption(f"{M.BY_KEY[key].what}. {len(out)} rounds.")
    if out.empty:
        st.info("Nenhum round para essa métrica com os filtros atuais.")
    else:
        st.dataframe(out, hide_index=True, width="stretch", height=420)
        st.download_button("Baixar esta lista (CSV)", out.to_csv(index=False).encode("utf-8"),
                           file_name=f"{team}_{key}.csv", mime="text/csv")


# ------------------------------------------------------------------ aba 4: metodologia
with tab_met:
    st.markdown(f"""
**De onde vêm os números.** Apenas dos arquivos JSON de partidas fornecidos pela organização do Hackathon: nenhuma API, coleta ou
dado externo. A análise é toda pós-partida.

**Como lemos um round.** Para cada time em cada round registramos quem fez o primeiro abate, quantas mortes foram trocadas em até 5 s,
quantas mortes aconteceram longe dos aliados (aliado vivo mais próximo a mais de 3000 unidades do jogo), a economia relativa ao
adversário (vantagem: loadout ≥ 1,25× o do adversário; desvantagem: ≤ 0,80×) e o que aconteceu com o spike.

**A referência.** É a taxa de todos os *outros* times, nas mesmas condições (competição, mapa e lado). O time nunca é comparado com ele mesmo.

**Quando o sistema afirma algo.** Cada partida conta como uma unidade, porque rounds da mesma partida não são independentes.
Só dizemos "acima" ou "abaixo" quando a diferença supera a incerteza do time *e* da referência, vale pelo menos
{M.MIN_DELTA_PP:.0f} pontos percentuais e há ao menos {M.MIN_N} rounds ou eventos em {M.MIN_MATCHES} partidas.
Testamos o método com times sorteados ao acaso, sem diferença real: o falso alerta ficou entre 4% e 7% (esperado: 5%).

**O que ainda pode enganar.**
- São 11 comparações por time, então cerca de 0,6 alerta por acaso é esperado. Leia como indício.
- Um time muito forte tende a ficar acima da referência em quase tudo. Os contrastes dentro do próprio time costumam ser mais úteis.
- A referência mistura adversários de níveis diferentes e não corrige a força do adversário em cada partida.
- Só temos posições no momento de kills, plant e defuse, não o trajeto completo, e nenhuma informação de habilidades usadas por round.
""")
    st.markdown("**As 11 métricas**")
    st.dataframe(pd.DataFrame({"Grupo": [m.group for m in M.METRICS], "Métrica": [m.label for m in M.METRICS],
                               "O que mede": [m.what for m in M.METRICS],
                               "Melhor quando": ["maior" if m.higher_better else "menor" for m in M.METRICS]}),
                 hide_index=True, width="stretch")
