"""Casos pequenos e previsiveis para as metricas por jogador + conferencia com a base real."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.analytics import metrics as M
from src.analytics import players as P


def _r(player, match, rnd, won=False, fk=False, fd=False, has_fk=True, kills=0, deaths=0, traded=0, iso=0, trade_kills=0):
    return dict(player=player, team=player.split("|")[0], match_id=match, round_num=rnd, won=won, first_kill=fk,
                first_death=fd, has_fk=has_fk, kills_enemy=kills, deaths_enemy=deaths, deaths_traded=traded,
                isolated_deaths=iso, deaths_with_dist=deaths, trade_kills=trade_kills)


def test_metricas_de_um_jogador():
    a = "t|a"
    df = pd.DataFrame([
        _r(a, "m1", 0, won=True, fk=True, kills=2, trade_kills=1),
        _r(a, "m1", 1, won=False, fd=True, deaths=1, traded=1),
        _r(a, "m1", 2, won=True, kills=1),
        _r(a, "m1", 3, has_fk=False, deaths=1, iso=1),
        _r("u|b", "m2", 0, won=True, fk=True, kills=1),
    ])
    res = P.player_metrics(df, a).set_index("key")
    got = {k: (res.loc[k, "x"], res.loc[k, "n"]) for k in res.index}
    assert got["p_open_part"] == (2, 3)    # fez ou sofreu o 1o abate / rounds com abate
    assert got["p_open_win"] == (1, 2)     # fez o 1o abate / duelos de abertura
    assert got["p_fk_conv"] == (1, 1)
    assert got["p_survival"] == (2, 4)     # rounds sem morrer / rounds
    assert got["p_trade_rate"] == (1, 2)
    assert got["p_isolated"] == (1, 2)
    assert got["p_trade_kills"] == (1, 3)
    # referencia = o outro jogador
    assert res.loc["p_open_win", "ref_rate"] == 1.0 and np.isnan(res.loc["p_trade_rate", "ref_rate"])


def test_amostra_vazia_e_perfil_neutro():
    df = pd.DataFrame([_r("t|a", "m1", 0, has_fk=False), _r("u|b", "m2", 0, fk=True)])
    res = P.player_metrics(df, "t|a").set_index("key")
    assert res.loc["p_open_win", "verdict"] == "sem_dados" and np.isnan(res.loc["p_open_win", "rate"])
    assert bool(res.loc["p_open_part", "neutral"]) and bool(res.loc["p_trade_kills", "neutral"])
    assert not bool(res.loc["p_survival", "neutral"])


def test_base_real_soma_do_elenco_bate_com_a_equipe():
    pr = P.load(ROOT / "data" / "processed")
    tr = M.load(ROOT / "data" / "processed")
    team = "ufmt_turuna"
    ro = P.roster(pr, team)
    t = tr[tr["team"] == team]
    assert ro["abates"].sum() == t["kills_enemy"].sum()
    assert ro["mortes"].sum() == t["deaths_enemy"].sum()
    assert ro["primeiros_abates"].sum() == t["first_kill"].sum()
    assert ro["rounds"].sum() == 5 * len(t)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK   ", name)
