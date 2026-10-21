"""
Tipo de abate (como alguem matou / morreu), a partir de kill_events.csv (coluna kill_kind, ver build_features.py).

Unico dado legivel sobre o que causou o abate: armas aparecem so como UUID na base, sem nome.
Referencia = todos os outros (times ou jogadores) do mesmo recorte.
"""
import numpy as np
import pandas as pd

KINDS = ["arma", "habilidade", "ultimate", "faca", "outro"]
KIND_PT = {"arma": "Arma", "habilidade": "Habilidade", "ultimate": "Ultimate", "faca": "Faca",
           "outro": "Outro (queda, esmagamento)"}
ITEM_PT = {"Ability1": "habilidade 1", "Ability2": "habilidade 2", "GrenadeAbility": "habilidade de granada",
           "Ultimate": "ultimate"}


def describe(kind: str, item) -> str:
    """Texto curto do tipo de abate para a sequência de abates."""
    if kind in ("habilidade", "ultimate") and isinstance(item, str):
        return ITEM_PT.get(item, KIND_PT[kind]).capitalize()
    return KIND_PT.get(kind, kind)


def in_scope(events: pd.DataFrame, rounds: pd.DataFrame, side: str) -> pd.DataFrame:
    """Abates de `events` cujo (partida, round, time do `side`) esta em `rounds` (team_round ja filtrado).
    side='killer' para abates feitos, 'victim' para mortes sofridas - assim o filtro de lado vale para quem agiu."""
    keys = rounds[["match_id", "round_num", "team"]].drop_duplicates()
    return events.merge(keys.rename(columns={"team": f"{side}_team"}), on=["match_id", "round_num", f"{side}_team"])


def breakdown(kills: pd.DataFrame, deaths: pd.DataFrame, mine_kills, mine_deaths) -> pd.DataFrame:
    """Distribuição por tipo de abate: da unidade (time ou jogador) e da referência (todos os outros).
    kills/deaths: abates feitos/mortes sofridas no recorte; mine_*: máscara booleana de quem é da unidade."""
    rows = []
    mk, rk = kills[mine_kills], kills[~mine_kills]
    md, rd = deaths[mine_deaths], deaths[~mine_deaths]
    for k in KINDS:
        rows.append(dict(
            kind=k, label=KIND_PT[k],
            kills=int((mk["kill_kind"] == k).sum()), kills_share=(mk["kill_kind"] == k).mean() if len(mk) else np.nan,
            ref_kills_share=(rk["kill_kind"] == k).mean() if len(rk) else np.nan,
            deaths=int((md["kill_kind"] == k).sum()), deaths_share=(md["kill_kind"] == k).mean() if len(md) else np.nan,
            ref_deaths_share=(rd["kill_kind"] == k).mean() if len(rd) else np.nan,
        ))
    out = pd.DataFrame(rows)
    out.attrs.update(n_kills=len(mk), n_deaths=len(md))
    return out
