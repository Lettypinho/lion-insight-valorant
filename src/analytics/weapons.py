"""
Armas: com qual arma o time (ou jogador) mata e morre, e como rende com a arma principal do round.

Nomes vêm de data/reference/armas.csv (ver build_features.py), já gravados em kill_events.weapon e player_round.weapon.
Arma principal do round = fact_round_player.weapon_id (em 91% dos abates com arma é a arma do abate).
Referência = todos os outros (times ou jogadores) do mesmo recorte COM A MESMA ARMA: compara Operator com Operator.
A vitória do round com uma arma depende muito da economia (quem tem fuzil costuma estar com a compra cheia):
é um número descritivo, não diz que a arma ganha rounds.
"""
from pathlib import Path

import numpy as np
import pandas as pd


def load_reference(root: Path) -> pd.DataFrame:
    """nome -> categoria, preco (para ordenar e rotular as tabelas). Vazio se o arquivo não existir."""
    p = Path(root) / "reference" / "armas.csv"
    if not p.exists():
        return pd.DataFrame(columns=["categoria", "preco"])
    return pd.read_csv(p, dtype={"preco": "Int64"}).drop_duplicates("nome").set_index("nome")[["categoria", "preco"]]


def _share(s: pd.Series, total: int) -> pd.Series:
    return s / total if total else s * np.nan


def kill_breakdown(kills: pd.DataFrame, deaths: pd.DataFrame, mine_kills, mine_deaths) -> pd.DataFrame:
    """Abates e mortes por item com nome: armas, faca e as habilidades que funcionam como arma (Headhunter,
    Tour de Force, Overdrive). Da unidade e da referência (todos os outros). As demais habilidades não têm nome na base
    e ficam na tabela de tipo de abate."""
    k, d = kills["weapon"].notna(), deaths["weapon"].notna()
    mk, rk = kills[k & mine_kills], kills[k & ~mine_kills]
    md, rd = deaths[d & mine_deaths], deaths[d & ~mine_deaths]
    names = sorted(set(mk["weapon"].dropna()) | set(md["weapon"].dropna()))
    out = pd.DataFrame({"weapon": names})
    for col, mine, ref in [("kills", mk, rk), ("deaths", md, rd)]:
        c, rc = mine["weapon"].value_counts(), ref["weapon"].value_counts()
        out[col] = out["weapon"].map(c).fillna(0).astype(int)
        out[f"{col}_share"] = _share(out[col], len(mine))
        out[f"ref_{col}_share"] = _share(out["weapon"].map(rc).fillna(0), len(ref))
    out.attrs.update(n_kills=len(mk), n_deaths=len(md))
    return out.sort_values(["kills", "deaths"], ascending=False).reset_index(drop=True)


def _per_weapon(pr: pd.DataFrame) -> pd.DataFrame:
    return pr.groupby("weapon").agg(rounds=("won", "size"), kills=("kills_enemy", "sum"),
                                    survived=("deaths_enemy", lambda s: int((s == 0).sum())), won=("won", "sum"))


def weapon_rounds(pr: pd.DataFrame, mine) -> pd.DataFrame:
    """Rendimento com a arma principal do round. pr: player_round (já filtrado); mine: máscara da unidade.
    Por arma: rounds (rodadas-jogador), abates por round, sobrevivência e vitória do round, da unidade e da referência."""
    pr = pr[pr["weapon"].notna()]
    m, r = _per_weapon(pr[mine.reindex(pr.index)]), _per_weapon(pr[~mine.reindex(pr.index)])
    out = m.join(r, rsuffix="_ref", how="left").fillna({"rounds_ref": 0, "kills_ref": 0, "survived_ref": 0, "won_ref": 0})
    for c in ["rounds_ref", "kills_ref", "survived_ref", "won_ref"]:
        out[c] = out[c].astype(int)
    out["kpr"], out["kpr_ref"] = out["kills"] / out["rounds"], out["kills_ref"] / out["rounds_ref"].replace(0, np.nan)
    out["survival"], out["survival_ref"] = out["survived"] / out["rounds"], out["survived_ref"] / out["rounds_ref"].replace(0, np.nan)
    out["win"], out["win_ref"] = out["won"] / out["rounds"], out["won_ref"] / out["rounds_ref"].replace(0, np.nan)
    return out.reset_index().sort_values("rounds", ascending=False).reset_index(drop=True)
