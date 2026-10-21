"""Acesso aos dados pela interface, com cache do Streamlit."""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.insights import engine as D
from src.ui.map_view import build_views

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
def load_events() -> pd.DataFrame:
    """Abates sobre inimigo com posicoes (kill_events.csv). Vazio se o arquivo ainda nao foi gerado."""
    p = DATA.parent / "kill_events.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_silhouette() -> pd.DataFrame:
    """Amostra de posicoes de todos os jogadores por mapa (map_silhouette.csv). Vazio se nao existir."""
    p = DATA.parent / "map_silhouette.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_map_views() -> dict:
    """Orientação e enquadramento de cada mapa (ver src/ui/map_view.py)."""
    sil = load_silhouette()
    return build_views(load_data(), sil) if not sil.empty else {}


@st.cache_data(show_spinner=False)
def compute(team, comps, maps, role):
    df = M.apply_filters(load_data(), list(comps) or None, list(maps) or None, role)
    res = M.team_metrics(df, team)
    return res, D.diagnose(res)


@st.cache_data(show_spinner=False)
def compute_by_map(team, comps, maps, role):
    df = M.apply_filters(load_data(), list(comps) or None, list(maps) or None, role)
    return [dict(r, dg=D.diagnose(r["res"])) for r in M.team_metrics_by_map(df, team)]
