"""Casos pequenos e previsiveis para o tipo de abate + conferencia com a base real."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "ingestion"))
import numpy as np, pandas as pd
from build_features import kill_kind
from src.analytics import kill_types as K


def test_classificacao():
    assert kill_kind("Weapon", "1BAA85B4-4C70-1284-64BB-6481DFC3BB4E") == "arma"
    assert kill_kind("Ability", "Ultimate") == "ultimate"
    assert kill_kind("Ability", "Ability1") == kill_kind("Ability", "GrenadeAbility") == "habilidade"
    assert kill_kind("Melee", "2F59173C-4BED-B6C3-2191-DEA9B58BE9C7") == "faca"
    assert kill_kind("Fall", None) == kill_kind("Crush", None) == "outro"
    assert K.describe("habilidade", "GrenadeAbility") == "Habilidade de granada"
    assert K.describe("arma", "1BAA85B4") == "Arma"
    assert K.describe("arma", "1BAA85B4", "Ghost") == "Ghost"
    assert K.describe("ultimate", "95336AE4", "Overdrive") == "Overdrive (ultimate)"
    assert K.describe("habilidade", "856D9A7E", "Headhunter") == "Headhunter (habilidade)"
    # habilidade que a base registra como arma (Headhunter do Chamber) e corrigida pela tabela de referencia
    ref = {"856D9A7E-4B06-DC37-15DC-9D809C37CB90": "habilidade", "9C82E19D-4575-0200-1A81-3EACF00CF872": "arma"}
    assert kill_kind("Weapon", "856d9a7e-4b06-dc37-15dc-9d809c37cb90", ref) == "habilidade"
    assert kill_kind("Weapon", "9C82E19D-4575-0200-1A81-3EACF00CF872", ref) == "arma"


def test_breakdown():
    kills = pd.DataFrame({"killer_team": ["a", "a", "a", "b"], "kill_kind": ["arma", "arma", "ultimate", "habilidade"]})
    deaths = pd.DataFrame({"victim_team": ["a", "b"], "kill_kind": ["habilidade", "arma"]})
    bd = K.breakdown(kills, deaths, kills["killer_team"] == "a", deaths["victim_team"] == "a").set_index("kind")
    assert bd.loc["arma", "kills"] == 2 and abs(bd.loc["arma", "kills_share"] - 2 / 3) < 1e-12
    assert bd.loc["ultimate", "kills"] == 1 and bd.loc["habilidade", "ref_kills_share"] == 1.0
    assert bd.loc["habilidade", "deaths_share"] == 1.0 and bd.loc["arma", "ref_deaths_share"] == 1.0
    assert bd.attrs["n_kills"] == 3 and bd.attrs["n_deaths"] == 1
    vazio = K.breakdown(kills.iloc[:0], deaths.iloc[:0], kills.iloc[:0]["killer_team"] == "a",
                        deaths.iloc[:0]["victim_team"] == "a")
    assert np.isnan(vazio.loc[0, "kills_share"])   # amostra vazia = ausencia de dado, nao zero


def test_base_real():
    ke = pd.read_csv(ROOT / "data" / "processed" / "kill_events.csv")
    fk = pd.read_csv(ROOT / "data" / "processed" / "fact_kill.csv", low_memory=False)
    ek = fk[fk["death_type"] == "enemy_kill"]
    assert len(ke) == len(ek)
    # 730 abates registrados como Weapon sao habilidades (481 Headhunter) e ultimates (42 Tour de Force + 207 Overdrive)
    item = ek["damage_item"].str.upper()
    hh = item == "856D9A7E-4B06-DC37-15DC-9D809C37CB90"
    ult = item.isin(["39099FB5-4293-DEF4-1E09-2E9080CE7456", "95336AE4-45D4-1032-CFAF-6BAD01910607"])
    assert (ke["kill_kind"] == "arma").sum() == ((ek["damage_type"] == "Weapon") & ~hh & ~ult).sum()
    assert (ke["kill_kind"] == "habilidade").sum() == ((ek["damage_type"] == "Ability") & (ek["damage_item"] != "Ultimate")).sum() + hh.sum()
    assert (ke["kill_kind"] == "ultimate").sum() == ((ek["damage_type"] == "Ability") & (ek["damage_item"] == "Ultimate")).sum() + ult.sum()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK   ", name)
