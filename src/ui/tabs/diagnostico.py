"""Aba 1: diagnóstico — pontos fortes, pontos de atenção e o que não foi possível afirmar."""
import pandas as pd
import streamlit as st

from src.ui.components import insight_card


def render(dg: dict, R: pd.DataFrame, df_f: pd.DataFrame, team: str):
    ins = dg["insights"]
    if not ins:
        st.info("Nenhuma diferença confiável em relação à competição com esse recorte. "
                "Isso é um resultado: o time joga perto da média. Para achar padrões, amplie os filtros "
                "(mais competições ou mapas) ou escolha um time com mais partidas.")
    mixed = [i for i in ins if i["quality"] == "misto" or len(i["keys"]) > 1]
    rest = [i for i in ins if i not in mixed]
    if mixed:
        st.subheader("Padrões do time")
        for i in mixed:
            insight_card(i, R, df_f, team)
    good = [i for i in rest if i["quality"] == "ponto_forte"]
    bad = [i for i in rest if i["quality"] == "ponto_de_atencao"]
    if good or bad:
        left, right = st.columns(2)
        with left:
            st.subheader("O que está funcionando")
            if not good:
                st.caption("Nenhum ponto forte confiável isolado.")
            for i in good:
                insight_card(i, R, df_f, team)
        with right:
            st.subheader("O que precisa de atenção")
            if not bad:
                st.caption("Nenhum ponto de atenção confiável isolado.")
            for i in bad:
                insight_card(i, R, df_f, team)
    with st.expander("O que o sistema não conseguiu afirmar"):
        nt = dg["notes"]
        st.markdown("**Sem diferença confiável da referência:** " + (", ".join(nt["em_linha"]) or "—"))
        st.markdown("**Amostra insuficiente:** " + (", ".join(nt["insuficiente"]) or "—"))
        st.markdown("**Não se aplica ao recorte** (por exemplo, retake no filtro de ataque): " + (", ".join(nt["sem_dados"]) or "—"))
    st.caption("São indícios, não sentenças: com 11 comparações por time, algum resultado pode aparecer por acaso.")
