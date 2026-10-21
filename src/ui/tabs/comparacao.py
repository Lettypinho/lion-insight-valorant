"""Aba 2: comparação do time com a referência da competição."""
import pandas as pd
import streamlit as st

from src.ui.charts import comparison_figure
from src.ui.formatting import num


def render(res: pd.DataFrame):
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
