"""
Raio-X de time: como um time joga em relação à competição, com os rounds que provam.

Rodar (da raiz do projeto):   python -m streamlit run app.py
Dados: apenas data/processed/team_round.csv (gerado a partir dos JSONs fornecidos pela organização).
Tudo e pos-partida: nada aqui interfere em partidas em andamento.

Este arquivo so orquestra a pagina; cada parte da interface fica em src/ui/.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.analytics import metrics as M  # noqa: E402
from src.ui import components, data, styles  # noqa: E402
from src.ui.formatting import team_name  # noqa: E402
from src.ui.sidebar import render_sidebar  # noqa: E402
from src.ui.tabs import comparacao, diagnostico, mapa_tatico, metodologia, partidas, rounds  # noqa: E402

st.set_page_config(page_title="Raio-X de time", layout="wide", initial_sidebar_state="auto")
data.ensure_data()
styles.apply_styles()

df_all = data.load_data()
f = render_sidebar(df_all, M.list_teams(df_all))

df_f = M.apply_filters(df_all, f.comps or None, f.maps or None, f.role)
mine = df_f[df_f["team"] == f.team]
if mine.empty:
    st.title(team_name(f.team))
    st.info("Esse time não tem rounds com os filtros escolhidos. Amplie a competição, o mapa ou o lado.")
    st.stop()

res, dg = data.compute(f.team, tuple(f.comps), tuple(f.maps), f.role)
R = res.set_index("key")
by_map = data.compute_by_map(f.team, tuple(f.comps), tuple(f.maps), f.role)

components.header(df_all, mine, f)

tab_diag, tab_map, tab_match, tab_comp, tab_rounds, tab_met = st.tabs(
    ["Diagnóstico", "Mapa tático", "Partidas e rounds", "Comparação com a competição", "Rounds de evidência", "Metodologia"])
with tab_diag:
    diagnostico.render(dg, R, res, df_f, f.team, by_map)
with tab_map:
    mapa_tatico.render(df_f, f.team, data.load_events(), data.load_silhouette(), data.load_map_views())
with tab_match:
    partidas.render(df_all, df_f, f, data.load_events(), data.load_silhouette(), data.load_map_views())
with tab_comp:
    comparacao.render(res)
with tab_rounds:
    rounds.render(df_f, f.team)
with tab_met:
    metodologia.render()
