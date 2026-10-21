"""Acesso aos dados pela interface, com cache do Streamlit."""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.insights import engine as D

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("TEAM_ROUND_CSV", ROOT / "data" / "processed" / "team_round.csv"))


def ensure_data():
    if not DATA.exists():
        st.error(f"Não encontrei {DATA}. Gere os dados antes: `python src/ingestion/build_features.py --processed data/processed`")
        st.stop()


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    return M.load(DATA.parent) if DATA.name == "team_round.csv" else pd.read_csv(DATA)


@st.cache_data(show_spinner=False)
def compute(team, comps, maps, role):
    df = M.apply_filters(load_data(), list(comps) or None, list(maps) or None, role)
    res = M.team_metrics(df, team)
    return res, D.diagnose(res)
