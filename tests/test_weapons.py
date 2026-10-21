"""Casos pequenos e previsiveis para as armas + conferencia com a base real."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.analytics import weapons as W


def test_abates_e_mortes_por_arma():
    kills = pd.DataFrame({"killer_team": ["a", "a", "a", "b", "b"], "kill_kind": ["arma", "arma", "habilidade", "arma", "arma"],
                          "weapon": ["Vandal", "Operator", "Headhunter", "Vandal", "Vandal"]})
    deaths = pd.DataFrame({"victim_team": ["a", "b"], "kill_kind": ["arma", "arma"], "weapon": ["Vandal", "Operator"]})
    bd = W.kill_breakdown(kills, deaths, kills["killer_team"] == "a", deaths["victim_team"] == "a").set_index("weapon")
    assert bd.loc["Headhunter", "kills"] == 1              # habilidade que funciona como arma aparece pelo nome
    assert bd.loc["Vandal", "kills"] == 1 and abs(bd.loc["Vandal", "kills_share"] - 1 / 3) < 1e-12
    assert bd.loc["Vandal", "ref_kills_share"] == 1.0
    assert bd.loc["Operator", "ref_kills_share"] == 0.0 and bd.loc["Vandal", "deaths_share"] == 1.0
    assert bd.attrs["n_kills"] == 3 and bd.attrs["n_deaths"] == 1
    sem_nome = kills.assign(weapon=[None, "Vandal", None, "Vandal", "Vandal"])   # habilidade comum: sem nome, fora
    assert W.kill_breakdown(sem_nome, deaths, sem_nome["killer_team"] == "a", deaths["victim_team"] == "a").attrs["n_kills"] == 1


def test_rendimento_com_a_arma_do_round():
    pr = pd.DataFrame({"team": ["a", "a", "a", "b", "b"], "weapon": ["Vandal", "Vandal", "Sheriff", "Vandal", None],
                       "kills_enemy": [2, 0, 1, 1, 3], "deaths_enemy": [0, 1, 1, 0, 0], "won": [True, False, False, True, True]})
    wr = W.weapon_rounds(pr, pr["team"] == "a").set_index("weapon")
    assert wr.loc["Vandal", "rounds"] == 2 and wr.loc["Vandal", "kpr"] == 1.0
    assert wr.loc["Vandal", "survival"] == 0.5 and wr.loc["Vandal", "win"] == 0.5
    assert wr.loc["Vandal", "kpr_ref"] == 1.0 and wr.loc["Vandal", "win_ref"] == 1.0   # referencia: mesma arma, outros
    assert np.isnan(wr.loc["Sheriff", "kpr_ref"])                                       # ninguem mais usou: sem referencia
    assert len(wr) == 2                                                                 # round sem arma registrada fica fora


def test_base_real():
    ref = pd.read_csv(ROOT / "data" / "reference" / "armas.csv")
    ke = pd.read_csv(ROOT / "data" / "processed" / "kill_events.csv")
    pr = pd.read_csv(ROOT / "data" / "processed" / "player_round.csv", low_memory=False)
    assert ref["item_id"].is_unique
    # todo codigo de arma presente na base tem nome
    items = set(ke.loc[ke["damage_type"].isin(["Weapon", "Melee"]), "damage_item"].dropna().str.upper())
    assert items <= set(ref["item_id"])
    assert set(pr["weapon_id"].dropna().str.upper()) <= set(ref["item_id"])
    # as 3 armas de habilidade inferidas sairam de "arma"
    inferred = ref[ref["fonte"] == "inferido"]
    assert set(inferred["nome"]) == {"Headhunter", "Tour de Force", "Overdrive"}
    hit = ke[ke["damage_item"].str.upper().isin(inferred["item_id"])]
    assert len(hit) == 730 and not (hit["kill_kind"] == "arma").any()
    assert (hit.loc[hit["weapon"] == "Headhunter", "kill_kind"] == "habilidade").all()
    assert (hit.loc[hit["weapon"] != "Headhunter", "kill_kind"] == "ultimate").all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK   ", name)
