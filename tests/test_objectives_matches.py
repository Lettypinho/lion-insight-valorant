"""Casos pequenos e previsiveis para plants por site, recortes de partida e analise por mapa."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.analytics import metrics as M
from src.analytics.matches import match_frame, team_matches
from src.analytics.objectives import plant_sites


def _row(team, match, rnd, role, won, planted=False, site=None, mp="Ascent", date="2026-06-01", opp="x"):
    return dict(team=team, opponent=opp, match_id=match, round_num=rnd, role=role, won=won, bomb_planted=planted,
                plant_site=site, map_name=mp, match_date=date, competition="C")


def test_plant_sites():
    df = pd.DataFrame([
        _row("a", "m1", 0, "Attacker", True, True, "A"),
        _row("a", "m1", 1, "Attacker", False, True, "A"),
        _row("a", "m1", 2, "Attacker", True, True, "B"),
        _row("a", "m1", 3, "Attacker", False),              # sem plant: fora
        _row("a", "m1", 4, "Defender", False, True, "A"),   # defesa: fora
        _row("b", "m2", 0, "Attacker", True, True, "B"),
        _row("b", "m2", 1, "Attacker", False, True, "B"),
    ])
    ps = plant_sites(df, "a").set_index("site")
    assert (ps.loc["A", "plants"], ps.loc["A", "wins"]) == (2, 1)
    assert abs(ps.loc["A", "share"] - 2 / 3) < 1e-12 and ps.loc["A", "win_rate"] == 0.5
    assert (ps.loc["B", "plants"], ps.loc["B", "wins"]) == (1, 1)
    assert ps.loc["A", "ref_plants"] == 0 and np.isnan(ps.loc["A", "ref_win_rate"])  # amostra vazia = ausencia de dado
    assert (ps.loc["B", "ref_plants"], ps.loc["B", "ref_wins"], ps.loc["B", "ref_share"]) == (2, 1, 1.0)
    assert plant_sites(df[df["role"] == "Defender"], "a").empty


def test_team_matches_placar():
    df = pd.DataFrame([_row("a", "m1", i, "Attacker", i < 3) for i in range(5)] +
                      [_row("a", "m2", i, "Defender", i < 1, date="2026-06-02") for i in range(2)])
    t = team_matches(df, "a").set_index("match_id")
    assert (t.loc["m1", "won"], t.loc["m1", "lost"], t.loc["m1", "result"]) == (3, 2, "V")
    assert (t.loc["m2", "won"], t.loc["m2", "lost"], t.loc["m2", "result"]) == (1, 1, "E")
    assert list(t.index) == ["m2", "m1"]  # mais recente primeiro


def test_match_frame_referencia_no_mesmo_mapa():
    df = pd.DataFrame([
        _row("a", "m1", 0, "Attacker", True), _row("b", "m1", 0, "Defender", False),   # partida analisada
        _row("a", "m2", 0, "Attacker", True),                                          # outra partida do time: fora
        _row("c", "m3", 0, "Attacker", False),                                         # outro time, mesmo mapa: referencia
        _row("d", "m4", 0, "Attacker", True, mp="Lotus"),                              # outro mapa: fora
    ])
    mf = match_frame(df, "a", "m1", "Ascent")
    assert sorted(zip(mf["team"], mf["match_id"])) == [("a", "m1"), ("b", "m1"), ("c", "m3")]


def test_spike_so_aparece_depois_do_plant():
    from types import SimpleNamespace as R
    from src.analytics.matches import spike_planted_at
    r = R(bomb_planted=True, plant_time_ms=50000)
    assert not spike_planted_at(r, 49999)
    assert spike_planted_at(r, 50000) and spike_planted_at(r, 70000)
    assert not spike_planted_at(R(bomb_planted=False, plant_time_ms=np.nan), 99999)


def test_momentos_do_round_em_ordem():
    from types import SimpleNamespace as R
    from src.analytics.matches import round_moments
    kills = pd.DataFrame({"seq_in_round": [1, 2, 3], "time_in_round_ms": [20000, 50000, 80000]})
    r = R(bomb_planted=True, plant_time_ms=50000, defuse_time_ms=90000)
    assert [m["id"] for m in round_moments(kills, r)] == ["k1", "plant", "k2", "k3", "defuse"]  # empate: plant antes
    r2 = R(bomb_planted=False, plant_time_ms=np.nan, defuse_time_ms=np.nan)
    assert [m["id"] for m in round_moments(kills, r2)] == ["k1", "k2", "k3"]
    assert round_moments(kills.iloc[:0], r2) == []


def test_team_metrics_by_map_usa_mesmo_mapa():
    df = M.load(ROOT / "data" / "processed")
    team = "ufmt_turuna"
    by_map = M.team_metrics_by_map(df, team)
    mine = df[df["team"] == team]
    assert sum(m["rounds"] for m in by_map) == len(mine)
    lotus = next(m for m in by_map if m["map_name"] == "Lotus")
    direct = M.team_metrics(df[df["map_name"] == "Lotus"], team)
    pd.testing.assert_frame_equal(lotus["res"], direct)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK   ", name)
