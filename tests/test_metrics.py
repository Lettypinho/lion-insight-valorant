"""Confere as metricas por um caminho INDEPENDENTE (direto de fact_kill / fact_round / dim_match)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.analytics import metrics as M

def main():
    P = ROOT / "data" / "processed"
    dm = pd.read_csv(P / "dim_match.csv"); fr = pd.read_csv(P / "fact_round.csv"); fk = pd.read_csv(P / "fact_kill.csv", low_memory=False)
    df = M.load(P)
    bad = 0
    for team in ["ufmt_turuna", "azure_bears_black", "inatel_gray", "usp_stars"]:
        mm = dm[(dm.red_team == team) | (dm.blue_team == team)].copy()
        mm["my_side"] = np.where(mm.red_team == team, "Red", "Blue")
        r = fr.merge(mm[["match_id", "my_side"]], on="match_id")
        r["won"] = r.winning_side == r.my_side
        r["role"] = np.where(r.attacker_side == r.my_side, "Attacker", "Defender")
        k = fk[fk.death_type == "enemy_kill"].merge(mm[["match_id", "my_side"]], on="match_id")
        first = k[k.is_first_kill][["match_id", "round_num", "killer_side"]]
        r = r.merge(first, on=["match_id", "round_num"], how="left")
        r["fk"] = r.killer_side == r.my_side; r["fd"] = r.killer_side.notna() & ~r.fk
        ref = {}
        ref["fk_rate"] = (r.fk.sum(), r.killer_side.notna().sum())
        ref["fk_conv"] = ((r.fk & r.won).sum(), r.fk.sum())
        ref["fd_recovery"] = ((r.fd & r.won).sum(), r.fd.sum())
        d = k[k.victim_side == k.my_side]
        ref["trade_rate"] = (d.death_was_traded.sum(), len(d))
        dd = d[d.victim_nearest_ally_dist.notna()]
        ref["isolated_rate"] = ((dd.victim_nearest_ally_dist > 3000).sum(), len(dd))
        ref["pistol_win"] = ((r.is_pistol_round & r.won).sum(), r.is_pistol_round.sum())
        ref["plant_rate"] = (((r.role == "Attacker") & r.bomb_planted).sum(), (r.role == "Attacker").sum())
        ref["post_plant_win"] = (((r.role == "Attacker") & r.bomb_planted & r.won).sum(), ((r.role == "Attacker") & r.bomb_planted).sum())
        ref["retake_win"] = (((r.role == "Defender") & r.bomb_planted & r.won).sum(), ((r.role == "Defender") & r.bomb_planted).sum())
        # plantador abatido ate 5 s depois do plant, sem troca (direto de fact_kill x fact_round)
        pk = fk[fk.death_type == "enemy_kill"].merge(r[["match_id", "round_num", "planter_puuid", "plant_time_ms"]],
                                                   on=["match_id", "round_num"])
        lag = pk.time_in_round_ms - pk.plant_time_ms
        hit = pk[(pk.victim_puuid == pk.planter_puuid) & (lag >= 0) & (lag <= 5000) & ~pk.death_was_traded]
        r = r.merge(hit[["match_id", "round_num"]].drop_duplicates().assign(pun=True), on=["match_id", "round_num"], how="left")
        r["pun"] = r["pun"].fillna(False).astype(bool)
        planted_att, planted_def = (r.role == "Attacker") & r.bomb_planted, (r.role == "Defender") & r.bomb_planted
        ref["plant_uncovered"] = ((planted_att & r.pun).sum(), planted_att.sum())
        ref["plant_punish"] = ((planted_def & r.pun).sum(), planted_def.sum())
        # tipo de abate: habilidade ou ultimate (direto de fact_kill.damage_type)
        ab = k.damage_type == "Ability"
        mine_k, mine_d = k.killer_side == k.my_side, k.victim_side == k.my_side
        ref["ability_kills"] = ((ab & mine_k).sum(), mine_k.sum())
        ref["ability_deaths"] = ((ab & mine_d).sum(), mine_d.sum())
        # economia
        me_l = np.where(r.role == "Attacker", r.attacker_loadout_total, r.defender_loadout_total)
        op_l = np.where(r.role == "Attacker", r.defender_loadout_total, r.attacker_loadout_total)
        ratio = me_l / op_l; np_ = ~r.is_pistol_round
        ref["econ_adv_conv"] = ((np_ & (ratio >= 1.25) & r.won).sum(), (np_ & (ratio >= 1.25)).sum())
        ref["econ_disadv_win"] = ((np_ & (ratio <= 0.8) & r.won).sum(), (np_ & (ratio <= 0.8)).sum())
        res = M.team_metrics(df, team).set_index("key")
        for key, (x, n) in ref.items():
            ok = (res.loc[key, "x"], res.loc[key, "n"]) == (int(x), int(n))
            bad += not ok
            if not ok: print("DIVERGE", team, key, (res.loc[key, "x"], res.loc[key, "n"]), "vs", (int(x), int(n)))
        print("OK   " if bad == 0 else "...  ", team, "-", len(ref), "metricas conferidas")
    # referencia = todos os outros times: confere uma metrica na mao
    t = "ufmt_turuna"; o = df[df.team != t]
    x = (o.first_kill & o.won).sum(); n = o.first_kill.sum()
    res = M.team_metrics(df, t).set_index("key")
    chk = abs(res.loc["fk_conv", "ref_rate"] - x / n) < 1e-12
    print("OK   " if chk else "FALHA", "referencia exclui o proprio time (fk_conv):", round(x / n, 4)); bad += not chk
    # IC deve conter a taxa; e filtros de lado devem separar ataque/defesa
    sub = M.apply_filters(df, role="Attacker"); r2 = M.team_metrics(sub, t).set_index("key")
    chk = (r2.loc["retake_win", "n"] == 0) and (r2.loc["post_plant_win", "n"] > 0)
    print("OK   " if chk else "FALHA", "filtro de lado: retake sem dados no ataque"); bad += not chk
    full = M.team_metrics(df, t)
    chk = ((full.ci_low <= full.rate + 1e-9) & (full.rate <= full.ci_high + 1e-9)).all(); print("OK   " if chk else "FALHA", "taxa dentro do IC"); bad += not chk
    print("RESULTADO:", "TUDO OK" if bad == 0 else f"{bad} falha(s)")
    return bad


def test_metricas_por_caminho_independente():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
