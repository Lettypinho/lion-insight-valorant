"""Comparação do time com a referência formada pelos outros times do recorte atual."""
import pandas as pd
import streamlit as st

from src.ui.charts import comparison_figure
from src.ui.formatting import num


def render(res: pd.DataFrame):
    st.subheader("Time x referência")
    st.info(
        "**Como ler:** o time é comparado com os outros times que passaram pelos mesmos filtros da barra lateral. "
        "Sem filtros de campeonato/etapa, a referência usa a base completa."
    )
    st.markdown(
        "No gráfico, o **ponto** é a taxa do time, a **barra horizontal** mostra a incerteza (intervalo de 95%) "
        "e o **traço cinza** é a referência."
    )
    st.plotly_chart(comparison_figure(res), width="stretch", theme=None, config={"displayModeBar": False})
    st.caption(
        "Ponto cheio: diferença considerada confiável pelos critérios do projeto. "
        "Ponto vazado: diferença não confirmada ou amostra pequena. O texto à direita repete a leitura sem depender de cor."
    )
    with st.expander("Ver números detalhados"):
        t = res[res["n"] > 0].copy()
        tab = pd.DataFrame({
            "Métrica": t["label"],
            "O que mede": t["what"],
            "Time": (t["rate"] * 100).round(1),
            "Referência": (t["ref_rate"] * 100).round(1),
            "Diferença (p.p.)": t["delta_pp"].round(1),
            "Intervalo 95%": [f"{num(a * 100)} a {num(b * 100)}" if pd.notna(a) else "—" for a, b in zip(t["ci_low"], t["ci_high"])],
            "Amostra": t["n"],
            "Partidas": t["n_matches"],
            "Percentil": t["percentile"].round(0),
            "Leitura": t["verdict"].map({
                "acima": "acima da referência",
                "abaixo": "abaixo da referência",
                "em_linha": "sem diferença confiável",
                "insuficiente": "amostra pequena",
                "sem_dados": "sem dados",
            }),
        })
        st.dataframe(tab, hide_index=True, width="stretch")
        st.caption("p.p. = pontos percentuais. Percentil indica a posição relativa do time entre as equipes comparáveis.")
