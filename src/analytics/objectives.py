"""
Objetivo (spike) por site.

Mesma regra de `post_plant_win` em metrics.py (rounds de ataque com plant), apenas aberta por site.
Referencia = todos os OUTROS times de `df` (use `df` ja filtrado por mapa: sites so se comparam no mesmo mapa).
"""
import numpy as np
import pandas as pd


def plant_sites(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Uma linha por site com: plants, fatia dos plants, vitorias pos-plant e taxa - do time e da referencia."""
    att = df[(df["role"] == "Attacker") & df["bomb_planted"].astype(bool) & df["plant_site"].notna()]
    mine, ref = att[att["team"] == team], att[att["team"] != team]
    sites = sorted(set(att["plant_site"]))
    rows = []
    for s in sites:
        m, r = mine[mine["plant_site"] == s], ref[ref["plant_site"] == s]
        rows.append(dict(
            site=s,
            plants=len(m), share=len(m) / len(mine) if len(mine) else np.nan,
            wins=int(m["won"].sum()), win_rate=m["won"].mean() if len(m) else np.nan,
            ref_plants=len(r), ref_share=len(r) / len(ref) if len(ref) else np.nan,
            ref_wins=int(r["won"].sum()), ref_win_rate=r["won"].mean() if len(r) else np.nan,
        ))
    return pd.DataFrame(rows, columns=["site", "plants", "share", "wins", "win_rate",
                                       "ref_plants", "ref_share", "ref_wins", "ref_win_rate"])
