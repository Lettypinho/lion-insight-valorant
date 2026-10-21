"""Aba 3: rounds de evidência por métrica, com download em CSV."""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.ui.components import evidence_table


def render(df_f: pd.DataFrame, team: str):
    st.markdown("Escolha uma métrica e veja os rounds do time que a compõem, para conferir o que está por trás de cada número.")
    k1, k2 = st.columns([2, 1])
    key = k1.selectbox("Métrica", [m.key for m in M.METRICS], format_func=lambda k: M.BY_KEY[k].label)
    show = k2.radio("Mostrar", ["Todos", "Bons para o time", "Ruins para o time"], horizontal=True)
    ev, out = evidence_table(df_f, team, key, None)
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
