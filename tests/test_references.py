"""Confere os catálogos locais usados apenas para traduzir IDs estáticos do jogo."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_todos_os_agentes_da_base_tem_nome_e_funcao():
    used = set(pd.read_csv(ROOT / "data" / "processed" / "fact_player_match.csv", usecols=["agent_id"])
               ["agent_id"].dropna().astype(str).str.lower())
    ref = pd.read_csv(ROOT / "data" / "reference" / "agentes.csv")
    ref["agent_id"] = ref["agent_id"].astype(str).str.lower()
    assert ref["agent_id"].is_unique
    assert used <= set(ref["agent_id"])
    hit = ref[ref["agent_id"].isin(used)]
    assert hit[["nome", "funcao"]].notna().all().all()


def test_todas_as_armaduras_da_base_tem_nome():
    used = set(pd.read_csv(ROOT / "data" / "processed" / "fact_round_player.csv", usecols=["armor_id"])
               ["armor_id"].dropna().astype(str).str.upper())
    ref = pd.read_csv(ROOT / "data" / "reference" / "armaduras.csv")
    ref["armor_id"] = ref["armor_id"].astype(str).str.upper()
    assert ref["armor_id"].is_unique
    assert used <= set(ref["armor_id"])
    assert ref.loc[ref["armor_id"].isin(used), "nome"].notna().all()
