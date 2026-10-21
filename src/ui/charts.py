"""Gráficos Plotly da aplicação."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


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
