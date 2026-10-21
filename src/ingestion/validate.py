#!/usr/bin/env python3
"""
Valida as tabelas geradas por ingest.py contra os JSONs originais.
Relê os JSONs de forma independente e compara totais.

Uso: python src/ingestion/validate.py --input "<pasta com os .json>" --processed data/processed
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

import pandas as pd

fails = []


def check(name, ok, detail=""):
    print(("OK   " if ok else "FALHA"), name, detail)
    if not ok:
        fails.append(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--processed", required=True)
    a = ap.parse_args()
    P = Path(a.processed)
    t = {n: pd.read_csv(P / f"{n}.csv", low_memory=False) for n in
         ["dim_match", "fact_player_match", "fact_round", "fact_round_player", "fact_kill",
          "fact_kill_position", "fact_kill_assist", "dim_team", "dim_player", "fact_objective_position"]}

    files = sorted(Path(a.input).rglob("*.json"))
    raw_kills = Counter(); raw_deaths = Counter(); raw_assist = Counter()
    raw_pm = {}  # (match, puuid) -> (kills, deaths, assists)
    n_rounds = n_kills = n_pos_expected = n_obj_expected = 0
    actor_in_locs = actor_total = 0
    alive_ok = alive_bad = victim_in_locs = locs_total = 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        mid = d["matchInfo"]["matchId"]
        roster = {p["puuid"] for p in d["players"] if not p.get("isObserver") and p.get("stats")}
        for p in d["players"]:
            if p["puuid"] in roster:
                s = p["stats"]
                raw_pm[(mid, p["puuid"])] = (s["kills"], s["deaths"], s["assists"], s["roundsPlayed"])
        for rr in d["roundResults"]:
            n_rounds += 1
            for actor, key in (("bombPlanter", "plantPlayerLocations"), ("bombDefuser", "defusePlayerLocations")):
                locs = [l for l in (rr.get(key) or []) if l["puuid"] in roster]
                n_obj_expected += len(locs)
                if rr.get(actor):
                    actor_total += 1
                    actor_in_locs += any(l["puuid"] == rr[actor] for l in locs)
            ks = sorted([k for ps in rr["playerStats"] for k in ps["kills"]],
                        key=lambda k: k["timeSinceRoundStartMillis"])
            alive = len(roster)
            for k in ks:
                n_kills += 1
                locs = k.get("playerLocations") or []
                locs_total += 1
                if any(l["puuid"] == k["victim"] for l in locs):
                    victim_in_locs += 1
                # localizacoes = jogadores vivos ANTES da morte, MENOS a vitima
                if len(locs) == alive - 1:
                    alive_ok += 1
                else:
                    alive_bad += 1
                alive -= 1
                n_pos_expected += len(locs)
                raw_kills[(mid, k["killer"])] += 1
                raw_deaths[(mid, k["victim"])] += 1
                for x in k.get("assistants") or []:
                    raw_assist[(mid, x)] += 1

    dm, pm, fr, fk = t["dim_match"], t["fact_player_match"], t["fact_round"], t["fact_kill"]
    print(f"Partidas JSON: {len(files)} | dim_match: {len(dm)}")
    check("partidas: 1 linha por arquivo", len(dm) == len(files))
    check("match_id unico", dm["match_id"].is_unique)
    check("rounds: total bate", len(fr) == n_rounds, f"({len(fr)} vs {n_rounds})")
    check("kills: total bate", len(fk) == n_kills, f"({len(fk)} vs {n_kills})")
    check("posicoes de kill: total bate", len(t["fact_kill_position"]) == n_pos_expected)
    check("kill_id unico", fk["kill_id"].is_unique)
    op = t["fact_objective_position"]
    check("posicoes de plant/defuse: total bate", len(op) == n_obj_expected, f"({len(op)} vs {n_obj_expected})")
    print(f"quem plantou/desarmou aparece nas posicoes do evento: {actor_in_locs}/{actor_total}")
    n_ev = op.groupby(["match_id", "round_num", "event"]).size()
    check("plant/defuse: no maximo 10 jogadores por evento", (n_ev <= 10).all())
    check("plants com posicoes = rounds com plant", len(n_ev.xs("plant", level="event")) == int(fr["bomb_planted"].sum()))

    # kills/deaths/assists por jogador vs stats oficiais.
    # Regra descoberta e validada: kill = abate sobre inimigo (sem suicidio/teamkill);
    # death = qualquer morte EXCETO detonacao do spike.
    ek = fk[fk["death_type"] == "enemy_kill"]
    kc = ek.groupby(["match_id", "killer_puuid"]).size().to_dict()
    dc = fk[fk["death_type"] != "bomb_detonation"].groupby(["match_id", "victim_puuid"]).size().to_dict()
    bad_k = bad_d = bad_a = 0
    ac = t["fact_kill_assist"].merge(fk[["kill_id", "match_id"]], on="kill_id").groupby(["match_id", "puuid"]).size().to_dict()
    for key, (k, dth, ast, _) in raw_pm.items():
        bad_k += kc.get(key, 0) != k
        bad_d += dc.get(key, 0) != dth
        bad_a += ac.get(key, 0) != ast
    n = len(raw_pm)
    check("kills por jogador = stats.kills", bad_k == 0, f"({bad_k} divergencias de {n})")
    check("mortes por jogador = stats.deaths (tolerancia 0,1%)", bad_d <= n * 0.001, f"({bad_d} divergencias de {n})")
    check("assistencias por jogador = stats.assists (tolerancia 0,5%)", bad_a <= n * 0.005, f"({bad_a} divergencias de {n})")
    # fact_round_player deve repetir os mesmos totais
    rp = t["fact_round_player"].groupby(["match_id", "puuid"])[["kills", "deaths"]].sum()
    pmi = pm.set_index(["match_id", "puuid"])
    check("fact_round_player soma = stats (kills)", (rp["kills"].reindex(pmi.index) == pmi["kills"]).all())
    check("fact_round_player soma = stats (deaths, tol. 0,1%)", (rp["deaths"].reindex(pmi.index) != pmi["deaths"]).sum() <= n * 0.001)
    print("death_type:", fk["death_type"].value_counts().to_dict())
    fkr = fk.groupby(["match_id", "round_num"])["is_first_kill"].sum()
    check("no maximo 1 primeiro abate por round", (fkr <= 1).all())

    # roster
    per = pm.groupby("match_id").size()
    check("10 jogadores por partida (sem observadores)", (per == 10).all())
    sides = pm.groupby(["match_id", "side"]).size()
    check("5 jogadores por lado", (sides == 5).all())
    check("nenhum time sem nome", dm["red_team"].notna().all() and dm["blue_team"].notna().all())
    check("times distintos dentro da partida", (dm["red_team"] != dm["blue_team"]).all())

    # placar: rounds ganhos (calculado a partir de fact_round) = roundsWon
    won = fr.groupby(["match_id", "winning_side"]).size().unstack(fill_value=0)
    j = dm.set_index("match_id").join(won)
    check("rounds ganhos (fact_round) = placar da partida",
          ((j["Red"] == j["red_rounds"]) & (j["Blue"] == j["blue_rounds"])).all())
    check("rounds jogados = red+blue", (dm["rounds_played"] == dm["red_rounds"] + dm["blue_rounds"]).all())
    # lado: attacker/defender sempre definidos, e opostos
    check("atacante/defensor definidos em todos os rounds", fr["attacker_side"].notna().all() and
          (fr["attacker_side"] != fr["defender_side"]).all())
    # lados: em partidas que chegam ao 2o tempo, o ataque troca no round 12 e fica fixo em cada metade
    long_ids = dm[dm["rounds_played"] >= 24]["match_id"]
    h = fr[fr["match_id"].isin(long_ids) & (fr["half"] != "OT")].groupby(["match_id", "half"])["attacker_side"].nunique()
    h1 = fr[fr["match_id"].isin(long_ids) & (fr["half"] == "H1")].groupby("match_id")["attacker_side"].first()
    h2 = fr[fr["match_id"].isin(long_ids) & (fr["half"] == "H2")].groupby("match_id")["attacker_side"].first()
    check("lado fixo por metade e troca no intervalo", (h == 1).all() and (h1 != h2).all(),
          f"({len(long_ids)} partidas com 2o tempo)")

    # data do arquivo vs inicio da partida (fuso de Sao Paulo)
    st = pd.to_datetime(dm["start_brt"]).dt.strftime("%Y-%m-%d")
    mism = (st != dm["match_date"]).sum()
    check("data do arquivo = data de inicio (BRT)", mism == 0, f"({mism} divergentes)")

    # semantica de playerLocations
    print(f"\nplayerLocations = (vivos antes da morte - 1) em {alive_ok}/{alive_ok+alive_bad} kills "
          f"({alive_ok/(alive_ok+alive_bad):.1%}); inclui a vitima em {victim_in_locs}/{locs_total}")
    check("playerLocations = vivos - vitima em >= 98% das kills", alive_ok / (alive_ok + alive_bad) >= 0.98)

    # qualidade das metricas derivadas
    print("\n--- qualidade das colunas derivadas ---")
    print("kills sem killer:", int(fk["killer_puuid"].isna().sum()))
    nulls = fk["victim_nearest_ally_dist"].isna()
    print("victim_nearest_ally_dist nulos:", int(nulls.sum()), "| desses, sem aliado vivo:",
          int((nulls & (fk["victim_allies_alive_n"] == 0)).sum()))
    print("mapa interno -> nome (deve ser 1 para 1):")
    mp = dm.groupby("map_internal")["map_name"].agg(lambda s: sorted(set(s)))
    for k, v in mp.items():
        print("   ", k, "->", v)
    check("mapa interno 1:1 com nome do arquivo", all(len(v) == 1 for v in mp))
    print("\nTimes com nome parecido (conferir se nao sao o mesmo time):")
    names = sorted(t["dim_team"]["team_name"])
    for i, n in enumerate(names):
        for o in names[i + 1:]:
            if o.startswith(n + "_") or n.startswith(o + "_"):
                print("   ", n, "~", o)
    reg_counts = dm["is_overtime"].value_counts().to_dict()
    print("\nPartidas com prorrogacao:", reg_counts)

    print("\nRESULTADO:", "TUDO OK" if not fails else f"{len(fails)} falha(s): {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
