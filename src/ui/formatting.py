"""Formatação de textos e números para exibição (sem dependência do Streamlit)."""
import pandas as pd

ACRONYMS = {"a2e", "bbn", "caap", "ceub", "fatec", "fei", "gc", "gdu", "ibmec", "iff", "ime", "pg", "pucc",
            "pucgo", "uff", "ufg", "ufmg", "ufmt", "ufpb", "ufpr", "ufrj", "ufu", "umc", "uscs", "usp", "utfpr"}
ROLE_PT = {"Attacker": "Ataque", "Defender": "Defesa"}
ROLE_EN = {"Ataque": "Attacker", "Defesa": "Defender", "Todos": None}


def team_name(slug: str) -> str:
    return " ".join(t.upper() if t in ACRONYMS else t.capitalize() for t in slug.split("_"))


def pct(v, d=0):
    return "—" if v is None or pd.isna(v) else f"{v * 100:.{d}f}".replace(".", ",") + "%"


def num(v, d=1, sign=False):
    s = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
    return s.replace(".", ",")


def competition_name(value: str) -> str:
    """Deixa códigos/nomes de competição mais amigáveis sem alterar o valor usado nos filtros."""
    if value is None or pd.isna(value):
        return "—"
    s = str(value)
    s = s.replace("UNIVAVA", "UNIVAVÁ").replace("Classificatoria", "Classificatória")
    return s
