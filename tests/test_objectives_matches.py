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


def test_classificacao_das_mortes():
    from types import SimpleNamespace as R
    from src.analytics.matches import classify_deaths, death_summary
    # p1 (time a) morre trocada; p2 (a, plantador) morre 3 s apos o plant sem troca; p3 (a) era o ultimo vivo
    kills = pd.DataFrame({
        "seq_in_round": [1, 2, 3, 4], "time_in_round_ms": [10000, 12000, 63000, 70000],
        "victim_puuid": ["p1", "x1", "p2", "p3"], "victim_team": ["a", "b", "a", "a"],
        "death_was_traded": [True, False, False, False], "is_trade_kill": [False, True, False, False],
        "isolated": [False, False, True, False], "victim_allies_alive": [4, 3, 1, 0],
        "killer_puuid": ["x1", "p9", "x2", "x3"], "killer_team": ["b", "a", "b", "b"]})
    r = R(bomb_planted=True, plant_time_ms=60000, planter_puuid="p2")
    k = classify_deaths(kills, r)
    assert k["death_class"].tolist() == ["trocada", "nao_trocada", "nao_trocada", "sem_aliado"]
    assert k["planter_punished"].tolist() == [False, False, True, False]
    assert k.loc[0, "trade_seq"] == 2 and k.loc[0, "trade_after_ms"] == 2000 and k.loc[1, "avenged_seq"] == 1
    assert k["trade_seq"].iloc[1:].isna().all()
    s = death_summary(k, "a")
    assert (s["deaths"], s["traded"], s["untraded"], s["last_alive"], s["isolated"]) == (3, 1, 1, 1, 1)
    assert (s["kills"], s["trade_kills"]) == (1, 1)
    # sem posicoes registradas: nao classifica (nao vira "nao trocada" por falta de dado)
    sem = classify_deaths(kills.assign(victim_allies_alive=np.nan, death_was_traded=False), r)
    assert (sem["death_class"] == "indefinida").all()


def test_classificacao_das_mortes_base_real():
    from src.analytics.matches import classify_deaths
    ke = pd.read_csv(ROOT / "data" / "processed" / "kill_events.csv")
    tr = M.load(ROOT / "data" / "processed").drop_duplicates(["match_id", "round_num"]).set_index(["match_id", "round_num"])
    # planter punido por round bate com a coluna de team_round
    punished = 0
    for (mid, rn), k in ke[ke["match_id"].isin(tr.index.get_level_values(0).unique()[:60])].groupby(["match_id", "round_num"]):
        punished += classify_deaths(k, tr.loc[(mid, rn)])["planter_punished"].any() != bool(tr.loc[(mid, rn), "planter_punished"])
    assert punished == 0
    # "sem aliado vivo" so ocorre quando nao ha ninguem do time vivo: e a ultima morte do time no round
    k = ke.sort_values(["match_id", "round_num", "seq_in_round"])
    last = k.groupby(["match_id", "round_num", "victim_team"])["seq_in_round"].transform("max") == k["seq_in_round"]
    zero = (k["victim_allies_alive"] == 0) & ~k["death_was_traded"]
    assert (zero & ~last).mean() < 0.005
    # o abate que vingou foi achado para toda morte trocada, sempre em ate 5 s
    sample = ke[ke["match_id"].isin(ke["match_id"].unique()[:40])]
    c = pd.concat([classify_deaths(g, tr.loc[i]) for i, g in sample.groupby(["match_id", "round_num"])])
    assert c.loc[c["death_was_traded"], "trade_seq"].notna().all() and (c["trade_after_ms"].dropna() <= 5000).all()
    assert c.loc[c["is_trade_kill"], "avenged_seq"].notna().all()


def test_trava_de_eventos_raros():
    lo, hi = M._wilson(0, 28)
    assert lo == 0 and hi > 0.10          # 0 de 28 e compativel com uma taxa de ~5%: nao pode ser confirmado
    assert np.isnan(M._wilson(0, 0)[0])
    df = M.load(ROOT / "data" / "processed")
    for team in ["ufg_eagles_blue", "azure_bears_golden"]:
        res = M.team_metrics(df, team)
        ok = res[res["verdict"].isin(["acima", "abaixo"])]
        for r in ok.itertuples():
            w_lo, w_hi = M._wilson(r.x, r.n)
            assert not (w_lo <= r.ref_rate <= w_hi), (team, r.key)
    r = M.team_metrics(df, "ufg_eagles_blue").set_index("key").loc["plant_punish"]
    assert r.x == 0 and r.verdict == "em_linha"   # caso que motivou a trava


def test_plant_sem_cobertura_bate_com_a_contagem_direta():
    df = M.load(ROOT / "data" / "processed")
    att = df[(df["role"] == "Attacker") & df["bomb_planted"]]
    dfn = df[(df["role"] == "Defender") & df["bomb_planted"]]
    assert att["planter_punished"].sum() == dfn["planter_punished"].sum() == 217
    assert (att["won"][att["planter_punished"]].mean() < 0.3) and (att["won"][~att["planter_punished"]].mean() > 0.7)


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
