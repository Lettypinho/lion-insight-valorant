"""Gráficos Plotly da aplicação."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.map_view import inside, to_view


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def colors() -> dict:
    """Tokens de cor por tema. s1..s3 = 3 primeiras cores categóricas (validadas para distinção em todos os pares)."""
    dark = is_dark()
    return dict(text="#f0efec" if dark else "#0b0b0b", muted="#c3c2b7" if dark else "#52514e",
                grid="#2b2b29" if dark else "#e7e6e2", surface="#1a1a19" if dark else "#fcfcfb",
                team="#3987e5" if dark else "#2a78d6", ref="#a3a29a" if dark else "#73726d",
                silhouette="#3a3a37" if dark else "#d9d8d3",
                s1="#3987e5" if dark else "#2a78d6", s2="#d95926" if dark else "#eb6834", s3="#199e70" if dark else "#1baf7a",
                # seu time x adversário, como no jogo (aliado azul, inimigo vermelho); também vencido x perdido na linha do
                # tempo. Par validado para daltonismo (ΔE 21,6 claro / 19,2 escuro). Vermelho = sempre negativo para o time.
                ally="#3987e5" if dark else "#2a78d6", enemy="#e66767" if dark else "#e34948")


FONT = dict(family="Figtree, system-ui, sans-serif", size=13)

# mapas: roda do mouse dá zoom, arrastar move (ou seleciona, no mapa tático), duplo clique volta ao enquadramento inicial
MAP_CONFIG = {"scrollZoom": True, "displaylogo": False, "doubleClick": "reset",
              "modeBarButtonsToRemove": ["toImage", "autoScale2d", "select2d"]}


def tactical_map(sil: pd.DataFrame, layers: list, view: dict, height=620, lines=None, focus=None,
                 dragmode="lasso", uirevision=None):
    """Mapa desenhado pelas próprias coordenadas da base (sem imagem externa).
    sil: colunas x, y (silhueta). layers: dicts com name, x, y, color, symbol, hover (lista de textos)
    e, opcionalmente, labels (texto curto escrito ao lado de cada ponto). x/y em coordenadas do jogo.
    view: orientação e enquadramento do mapa (src/ui/map_view.py).
    lines: dicts com x, y (listas com None separando segmentos), color, dash, width - desenhadas sob os pontos.
    focus: pontos (x, y) do jogo para enquadrar de perto (ex.: matador, vítima e spike); None = mapa inteiro.
    uirevision: mantém o zoom do usuário entre atualizações enquanto o valor não mudar.
    O traço 0 é a silhueta; sem `lines`, o traço k (k >= 1) é layers[k - 1], com os pontos na mesma ordem recebida."""
    C = colors()
    su, sw = to_view(sil["x"], sil["y"], view["k"])
    keep = inside(view, su, sw)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=su[keep], y=sw[keep], mode="markers", name="Mapa (posições de todos os jogadores)",
                               # mapas pouco jogados têm silhueta rala: ponto maior para o desenho continuar legível
                               marker=dict(size=3 if keep.sum() >= 10000 else 4 if keep.sum() >= 4000 else 6,
                                           color=C["silhouette"]), hoverinfo="skip", showlegend=False))
    for ln in lines or []:
        u, w = to_view([float("nan") if v is None else v for v in ln["x"]],
                       [float("nan") if v is None else v for v in ln["y"]], view["k"])
        # Scattergl (não Scatter): traços SVG ficam por baixo da camada WebGL da silhueta e apareceriam apagados
        fig.add_trace(go.Scattergl(x=u, y=w, mode="lines", name=ln.get("name", ""), showlegend=ln.get("legend", False),
                                 hoverinfo="skip", connectgaps=False,
                                 line=dict(color=ln["color"], width=ln.get("width", 2), dash=ln.get("dash", "solid"))))
    for ly in layers:
        u, w = to_view(ly["x"], ly["y"], view["k"])
        fig.add_trace(go.Scattergl(
            x=u, y=w, mode="markers+text" if ly.get("labels") is not None else "markers", name=ly["name"],
            hovertext=ly["hover"], text=ly.get("labels"), textposition="top center", textfont=dict(color=C["text"], size=12),
            hovertemplate="%{hovertext}<extra></extra>",
            marker=dict(size=ly.get("size", 9), color=ly["color"], symbol=ly.get("symbol", "circle"),
                        line=dict(width=ly.get("line_width", 1.5), color=ly.get("line_color", C["surface"])))))
    xrange, yrange = view["xrange"], view["yrange"]
    if focus:
        fu, fw = to_view([p[0] for p in focus], [p[1] for p in focus], view["k"])
        span = max(FOCUS_MIN_SPAN, fu.max() - fu.min(), fw.max() - fw.min()) * 1.35
        cu, cw = (fu.max() + fu.min()) / 2, (fw.max() + fw.min()) / 2
        xrange, yrange = [cu - span / 2, cu + span / 2], [cw - span / 2, cw + span / 2]
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(**FONT, color=C["text"]), dragmode=dragmode, hovermode="closest", uirevision=uirevision,
        legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", font=dict(color=C["muted"])),
        xaxis=dict(visible=False, range=xrange, constrain="domain"),
        yaxis=dict(visible=False, range=yrange, scaleanchor="x", scaleratio=1, constrain="domain"))
    return fig


FOCUS_MIN_SPAN = 3000  # menor área (unidades do jogo) ao aproximar no lance


def sites_figure(ps: pd.DataFrame, value: str, ref_value: str, title: str):
    """Barras por site: time x referência (outros times no mesmo mapa). value/ref_value são taxas 0..1."""
    C = colors()
    fig = go.Figure()
    for name, col, n_col, color in [("Time", value, "plants", C["team"]), ("Referência (outros times)", ref_value, "ref_plants", C["ref"])]:
        fig.add_trace(go.Bar(
            x=[f"Site {s}" for s in ps["site"]], y=ps[col] * 100, name=name, marker=dict(color=color, cornerradius=4),
            text=[f"{v * 100:.0f}%".replace(".", ",") if pd.notna(v) else "—" for v in ps[col]], textposition="outside",
            customdata=ps[n_col], hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.1f}}%<br>%{{customdata}} plants<extra></extra>"))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)), barmode="group", bargap=0.35, bargroupgap=0.08, height=300,
        margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(**FONT, color=C["text"]), legend=dict(orientation="h", y=-0.15, x=0, font=dict(color=C["muted"])),
        yaxis=dict(range=[0, 115], ticksuffix="%", gridcolor=C["grid"], zeroline=False, tickfont=dict(color=C["muted"])),
        xaxis=dict(tickfont=dict(color=C["text"])))
    return fig


def timeline_figure(rounds: pd.DataFrame, selected=None):
    """Faixa com um bloco por round. rounds: round_label, won, role_pt, hover. selected = round_label destacado."""
    C = colors()
    fig = go.Figure()
    for won, name, color in [(True, "Round vencido", C["team"]), (False, "Round perdido", C["enemy"])]:
        r = rounds[rounds["won"] == won]
        fig.add_trace(go.Bar(
            x=r["round_label"], y=[1] * len(r), name=name, marker=dict(color=color, cornerradius=4,
            line=dict(width=[3 if x == selected else 0 for x in r["round_label"]], color=C["text"])),
            text=r["role_pt"].str[0], textposition="inside", insidetextanchor="middle",
            textfont=dict(color="#ffffff", size=11), customdata=r["hover"], hovertemplate="%{customdata}<extra></extra>"))
    fig.update_layout(
        barmode="overlay", bargap=0.12, height=130, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(**FONT, color=C["text"]), showlegend=True,
        legend=dict(orientation="h", y=-0.45, x=0, font=dict(color=C["muted"])),
        yaxis=dict(visible=False, range=[0, 1]),
        xaxis=dict(tickmode="linear", dtick=1, tickfont=dict(color=C["muted"], size=11), showgrid=False, fixedrange=True))
    return fig


def comparison_figure(res):
    C = colors()
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
