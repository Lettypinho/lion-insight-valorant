#!/usr/bin/env python3
"""
Gera, a partir das tabelas de data/processed:
  * `team_round.csv`     UMA linha por (partida, round, time) - base das metricas;
  * `player_round.csv`   UMA linha por (partida, round, jogador) - metricas e insights por jogador;
  * `kill_events.csv`    um abate sobre inimigo por linha, com posicoes - mapa tatico e detalhe de round;
  * `map_silhouette.csv` amostra das posicoes de todos os jogadores por mapa - desenha o mapa sem imagem externa.

Le apenas as tabelas de data/processed (saida do ingest.py). Nenhum dado externo.
As metricas em si (taxas, referencia, diagnosticos) ficam em src/analytics/metrics.py:
aqui so guardamos os fatos de cada round, de forma que qualquer metrica vire
uma soma/contagem simples.

Uso:
    python src/ingestion/build_features.py --processed data/processed
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ISOLATED_DIST = 3000        # morte "isolada": aliado vivo mais proximo a mais de 3000 unidades do jogo
ECON_ADV_RATIO = 1.25       # loadout do time >= 1,25x o do adversario  -> vantagem economica
ECON_DISADV_RATIO = 0.80    # loadout do time <= 0,80x o do adversario  -> desvantagem economica
SILHOUETTE_PER_MAP = 20000  # pontos por mapa na silhueta (amostra fixa, seed 0)
PLANT_COVER_MS = 5000       # plantador abatido ate 5 s depois do plant, sem troca -> plant sem cobertura


def side_rows(fr: pd.DataFrame, role: str) -> pd.DataFrame:
    me, opp = ("attacker", "defender") if role == "Attacker" else ("defender", "attacker")
    return pd.DataFrame({
        "match_id": fr["match_id"], "round_num": fr["round_num"], "half": fr["half"],
        "is_pistol": fr["is_pistol_round"], "role": role,
        "side": fr[f"{me}_side"], "team": fr[f"{me}_team"], "opponent": fr[f"{opp}_team"],
        "won": fr["winning_side"] == fr[f"{me}_side"],
        "team_loadout": fr[f"{me}_loadout_total"], "opp_loadout": fr[f"{opp}_loadout_total"],
        "bomb_planted": fr["bomb_planted"].astype(bool), "plant_site": fr["plant_site"],
        "plant_time_ms": fr["plant_time_ms"], "plant_x": fr["plant_x"], "plant_y": fr["plant_y"], "planter_puuid": fr["planter_puuid"],
        "defuser_puuid": fr["defuser_puuid"], "defuse_time_ms": fr["defuse_time_ms"],
        "result_code": fr["result_code"],
    })


def build(processed: Path) -> pd.DataFrame:
    dm = pd.read_csv(processed / "dim_match.csv")
    fr = pd.read_csv(processed / "fact_round.csv")
    fk = pd.read_csv(processed / "fact_kill.csv", low_memory=False)

    # so abates sobre inimigo entram nas metricas de first kill / trade / isolamento
    ek = fk[fk["death_type"] == "enemy_kill"].copy()
    has_dist = ek["victim_nearest_ally_dist"].notna()
    ek["isolated"] = has_dist & (ek["victim_nearest_ally_dist"] > ISOLATED_DIST)
    ek["has_dist"] = has_dist

    deaths = (ek.groupby(["match_id", "round_num", "victim_side"])
                .agg(deaths_enemy=("kill_id", "size"), deaths_traded=("death_was_traded", "sum"),
                     isolated_deaths=("isolated", "sum"), deaths_with_dist=("has_dist", "sum"))
                .reset_index().rename(columns={"victim_side": "side"}))
    kills = (ek.groupby(["match_id", "round_num", "killer_side"])
               .agg(kills_enemy=("kill_id", "size"), trade_kills=("is_trade_kill", "sum"))
               .reset_index().rename(columns={"killer_side": "side"}))
    first = (ek[ek["is_first_kill"]][["match_id", "round_num", "killer_side", "time_in_round_ms"]]
             .rename(columns={"killer_side": "fk_side", "time_in_round_ms": "fk_time_ms"}))

    # plantador abatido por inimigo ate PLANT_COVER_MS depois do plant, sem a morte ser trocada (fato do round)
    pk = ek.merge(fr[["match_id", "round_num", "planter_puuid", "plant_time_ms"]], on=["match_id", "round_num"])
    dt = pk["time_in_round_ms"] - pk["plant_time_ms"]
    pk = pk[(pk["victim_puuid"] == pk["planter_puuid"]) & (dt >= 0) & (dt <= PLANT_COVER_MS) & ~pk["death_was_traded"]]
    punished = pk[["match_id", "round_num"]].drop_duplicates().assign(planter_punished=True)

    tr = pd.concat([side_rows(fr, "Attacker"), side_rows(fr, "Defender")], ignore_index=True)
    tr = (tr.merge(deaths, on=["match_id", "round_num", "side"], how="left")
            .merge(kills, on=["match_id", "round_num", "side"], how="left")
            .merge(first, on=["match_id", "round_num"], how="left")
            .merge(punished, on=["match_id", "round_num"], how="left"))
    tr["planter_punished"] = tr["planter_punished"].fillna(False).astype(bool)
    for c in ["deaths_enemy", "deaths_traded", "isolated_deaths", "deaths_with_dist", "kills_enemy", "trade_kills"]:
        tr[c] = tr[c].fillna(0).astype(int)

    tr["has_fk"] = tr["fk_side"].notna()
    tr["first_kill"] = tr["fk_side"] == tr["side"]
    tr["first_death"] = tr["has_fk"] & ~tr["first_kill"]

    # economia relativa ao adversario (pistol separado: todos comecam iguais)
    tr["econ_ratio"] = (tr["team_loadout"] / tr["opp_loadout"]).replace([np.inf, -np.inf], np.nan)
    tr["econ_state"] = np.select(
        [tr["is_pistol"], tr["econ_ratio"] >= ECON_ADV_RATIO, tr["econ_ratio"] <= ECON_DISADV_RATIO],
        ["pistol", "vantagem", "desvantagem"], default="parelha")
    tr.loc[tr["econ_ratio"].isna() & ~tr["is_pistol"], "econ_state"] = "indefinida"

    meta = dm[["match_id", "competition", "competition_group", "map_name", "match_date", "game_no", "series_game"]]
    tr = tr.merge(meta, on="match_id", how="left")
    tr["round_label"] = tr["round_num"] + 1
    return tr.sort_values(["match_date", "match_id", "round_num", "role"]).reset_index(drop=True)


def build_kill_events(processed: Path) -> pd.DataFrame:
    dm = pd.read_csv(processed / "dim_match.csv", usecols=["match_id", "map_name"])
    fk = pd.read_csv(processed / "fact_kill.csv", low_memory=False)
    ek = fk[fk["death_type"] == "enemy_kill"].copy()
    ek["isolated"] = ek["victim_nearest_ally_dist"].notna() & (ek["victim_nearest_ally_dist"] > ISOLATED_DIST)
    cols = ["kill_id", "match_id", "round_num", "seq_in_round", "time_in_round_ms", "killer_puuid", "victim_puuid",
            "killer_team", "victim_team",
            "victim_x", "victim_y", "killer_x", "killer_y", "is_first_kill", "death_was_traded", "is_trade_kill", "isolated"]
    return ek[cols].merge(dm, on="match_id", how="left")


def build_player_round(processed: Path, tr: pd.DataFrame) -> pd.DataFrame:
    """UMA linha por (partida, round, jogador). Mesmas regras de team_round, vistas pelo jogador:
    so abates sobre inimigo contam; first kill/death sao do jogador; contexto do round vem de team_round."""
    rp = pd.read_csv(processed / "fact_round_player.csv",
                     usecols=["match_id", "round_num", "puuid", "team_name", "damage_dealt"])
    fk = pd.read_csv(processed / "fact_kill.csv", low_memory=False)
    ek = fk[fk["death_type"] == "enemy_kill"].copy()
    has_dist = ek["victim_nearest_ally_dist"].notna()
    ek["isolated"] = has_dist & (ek["victim_nearest_ally_dist"] > ISOLATED_DIST)
    ek["has_dist"] = has_dist
    deaths = (ek.groupby(["match_id", "round_num", "victim_puuid"])
                .agg(deaths_enemy=("kill_id", "size"), deaths_traded=("death_was_traded", "sum"),
                     isolated_deaths=("isolated", "sum"), deaths_with_dist=("has_dist", "sum"),
                     first_death=("is_first_kill", "any"))
                .reset_index().rename(columns={"victim_puuid": "puuid"}))
    kills = (ek.groupby(["match_id", "round_num", "killer_puuid"])
               .agg(kills_enemy=("kill_id", "size"), trade_kills=("is_trade_kill", "sum"),
                    first_kill=("is_first_kill", "any"))
               .reset_index().rename(columns={"killer_puuid": "puuid"}))
    pr = (rp.rename(columns={"team_name": "team"})
            .merge(deaths, on=["match_id", "round_num", "puuid"], how="left")
            .merge(kills, on=["match_id", "round_num", "puuid"], how="left"))
    for c in ["deaths_enemy", "deaths_traded", "isolated_deaths", "deaths_with_dist", "kills_enemy", "trade_kills"]:
        pr[c] = pr[c].fillna(0).astype(int)
    for c in ["first_kill", "first_death"]:
        pr[c] = pr[c].fillna(False).astype(bool)
    ctx = tr[["match_id", "round_num", "team", "opponent", "role", "half", "won", "is_pistol", "has_fk",
              "competition", "competition_group", "map_name", "match_date", "game_no", "series_game", "round_label"]]
    pr = pr.merge(ctx, on=["match_id", "round_num", "team"], how="left")
    return pr.sort_values(["match_date", "match_id", "round_num", "team", "puuid"]).reset_index(drop=True)


def check_player_round(pr: pd.DataFrame, tr: pd.DataFrame) -> bool:
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(("OK   " if cond else "FALHA"), name, detail)

    g = pr.groupby(["match_id", "round_num", "team"])
    t = tr.set_index(["match_id", "round_num", "team"])
    chk("player_round: 5 jogadores por time e round", (g.size() == 5).all())
    chk("player_round: contexto de round preenchido", pr["won"].notna().all() and pr["role"].notna().all())
    chk("player_round: abates somam team_round", (g["kills_enemy"].sum().reindex(t.index) == t["kills_enemy"]).all())
    chk("player_round: mortes trocadas somam team_round", (g["deaths_traded"].sum().reindex(t.index) == t["deaths_traded"]).all())
    chk("player_round: first kill do time = algum jogador", (g["first_kill"].any().reindex(t.index) == t["first_kill"]).all())
    return ok


def build_silhouette(processed: Path) -> pd.DataFrame:
    dm = pd.read_csv(processed / "dim_match.csv", usecols=["match_id", "map_name"])
    pos = pd.read_csv(processed / "fact_kill_position.csv", usecols=["kill_id", "x", "y"])
    pos["match_id"] = pos["kill_id"].str.split(":").str[0]
    pos = pos.merge(dm, on="match_id")[["map_name", "x", "y"]]
    out = pos.sample(frac=1, random_state=0).groupby("map_name").head(SILHOUETTE_PER_MAP)
    return out.round().astype({"x": int, "y": int}).sort_values(["map_name", "x", "y"]).reset_index(drop=True)


def check(tr: pd.DataFrame, processed: Path):
    fr = pd.read_csv(processed / "fact_round.csv")
    fk = pd.read_csv(processed / "fact_kill.csv", low_memory=False)
    ek = fk[fk["death_type"] == "enemy_kill"]
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(("OK   " if cond else "FALHA"), name, detail)

    chk("2 linhas por round", len(tr) == 2 * len(fr), f"({len(tr)} vs {2 * len(fr)})")
    g = tr.groupby(["match_id", "round_num"])
    chk("exatamente 1 time vence cada round", (g["won"].sum() == 1).all())
    chk("first kill: no maximo 1 time por round", (g["first_kill"].sum() <= 1).all())
    chk("first_kill + first_death = rounds com abate", (tr["first_kill"] | tr["first_death"]).sum() == tr["has_fk"].sum())
    chk("abates somam o total de enemy_kill", tr["kills_enemy"].sum() == len(ek), f"({tr['kills_enemy'].sum()} vs {len(ek)})")
    chk("mortes somam o total de enemy_kill", tr["deaths_enemy"].sum() == len(ek))
    chk("trades <= mortes", (tr["deaths_traded"] <= tr["deaths_enemy"]).all())
    chk("isoladas <= mortes com distancia", (tr["isolated_deaths"] <= tr["deaths_with_dist"]).all())
    chk("papel Attacker/Defender: 1 de cada por round",
        (g["role"].apply(lambda s: set(s) == {"Attacker", "Defender"})).all())
    chk("plantador punido so em rounds com plant", (~tr["planter_punished"] | tr["bomb_planted"]).all())
    chk("plantador punido igual para os dois lados do round", (g["planter_punished"].nunique() == 1).all())
    chk("nenhum time sem nome", tr["team"].notna().all() and tr["opponent"].notna().all())
    chk("pistol = 2 por partida com 24+ rounds ou 1 caso contrario",
        tr[tr["is_pistol"]].groupby("match_id")["round_num"].nunique().between(1, 2).all())
    print("\nestados de economia:", tr["econ_state"].value_counts().to_dict())
    print("times:", tr["team"].nunique(), "| partidas:", tr["match_id"].nunique())
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed", default="data/processed")
    a = ap.parse_args()
    p = Path(a.processed)
    tr = build(p)
    ok = check(tr, p)
    tr.to_csv(p / "team_round.csv", index=False)
    print(f"\nteam_round.csv: {len(tr):,d} linhas ->", p / "team_round.csv")
    pr = build_player_round(p, tr)
    ok &= check_player_round(pr, tr)
    pr.to_csv(p / "player_round.csv", index=False)
    print(f"player_round.csv: {len(pr):,d} linhas ->", p / "player_round.csv")
    ke = build_kill_events(p)
    ke.to_csv(p / "kill_events.csv", index=False)
    print(f"kill_events.csv: {len(ke):,d} linhas ->", p / "kill_events.csv")
    sil = build_silhouette(p)
    sil.to_csv(p / "map_silhouette.csv", index=False)
    print(f"map_silhouette.csv: {len(sil):,d} linhas ->", p / "map_silhouette.csv")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
