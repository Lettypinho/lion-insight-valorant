#!/usr/bin/env python3
"""
Transforma os JSONs de partidas de VALORANT (fornecidos pela organizacao do
Hackathon) em tabelas planas, em CSV, prontas para carregar em banco ou usar
em pandas/Streamlit.

Uso:
    python src/ingestion/ingest.py --input "<pasta com os .json>" --output data/processed

Regras de negocio importantes (o JSON NAO traz nome de time):
  * Nome dos times, competicao, data e mapa vem do NOME DO ARQUIVO.
  * Para saber qual time e Red e qual e Blue, cruzamos o placar do arquivo
    (ex.: "13_x_9") com `teams[].roundsWon` do JSON.
  * Lado (Attacker/Defender) por round vem de `winningTeam` + `winningTeamRole`
    (funciona tambem nas prorrogacoes, onde o lado troca a cada round).
  * Observadores (`isObserver`) ficam fora das tabelas de jogadores.

Nenhum dado externo e usado: tudo vem exclusivamente dos arquivos fornecidos.
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

TRADE_WINDOW_MS = 5000  # janela para considerar uma morte "trocada"
BRT = ZoneInfo("America/Sao_Paulo")
OTHER = {"Red": "Blue", "Blue": "Red"}

FILENAME_RE = re.compile(
    r"^(?P<comp>[A-Z0-9]+(?:_[A-Z0-9]+)*?)_(?P<num>\d+)(?P<series>[a-z]?)"
    r"_(?P<date>\d{2}-\d{2}-\d{2})_(?P<team_a>.+?)_(?P<score_a>\d+)_x_"
    r"(?P<score_b>\d+)_(?P<team_b>.+)_(?P<map>[a-z]+)\.json$"
)

COMPETITIONS = {
    "RUSHE": ("Rush Series", "Rush Series Esquenta"),
    "RUSH2": ("Rush Series", "Rush Series Esquenta 2"),
    "RUSH_INCLUSIVO": ("Rush Series", "Rush Series Inclusivo"),
    "UNIVAVA_G": ("UNIVAVA", "UNIVAVA Fase de Grupos"),
    "UNIVAVA_C1": ("UNIVAVA", "UNIVAVA Classificatoria 1"),
    "UNIVAVA_C2": ("UNIVAVA", "UNIVAVA Classificatoria 2"),
    "UNIVAVA_C3": ("UNIVAVA", "UNIVAVA Classificatoria 3"),
    "UNIVAVA_C4": ("UNIVAVA", "UNIVAVA Classificatoria 4"),
}


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nearest(point, others):
    """Menor distancia de `point` a uma lista de pontos (ou None)."""
    ds = [dist(point, o) for o in others]
    return round(min(ds), 1) if ds else None


def loc(d):
    return (d["x"], d["y"]) if d else None


def process(path, T, issues, seen_ids):
    m = FILENAME_RE.match(path.name)
    if not m:
        issues.append({"file": path.name, "issue": "nome de arquivo fora do padrao"})
        return
    d = json.loads(path.read_text(encoding="utf-8"))
    mi = d["matchInfo"]
    match_id = mi["matchId"]
    if match_id in seen_ids:
        issues.append({"file": path.name, "issue": "matchId duplicado - ignorado"})
        return
    seen_ids.add(match_id)

    # ---- times: cruza placar do arquivo com roundsWon ------------------
    rounds_won = {t["teamId"]: t["roundsWon"] for t in d["teams"]}
    sa, sb = int(m["score_a"]), int(m["score_b"])
    team_name = {}
    side_a = [s for s, w in rounds_won.items() if w == sa]
    if sa != sb and len(side_a) == 1 and sorted(rounds_won.values()) == sorted([sa, sb]):
        team_name[side_a[0]] = m["team_a"]
        team_name[OTHER[side_a[0]]] = m["team_b"]
    else:
        issues.append({"file": path.name, "issue": "placar do arquivo nao bate com roundsWon - times nao atribuidos"})

    # ---- elenco (sem observadores) -------------------------------------
    roster = {p["puuid"]: p for p in d["players"] if not p.get("isObserver") and p.get("stats")}
    n_obs = sum(1 for p in d["players"] if p.get("isObserver"))
    side_of = {u: p["teamId"] for u, p in roster.items()}

    comp_group, comp_label = COMPETITIONS.get(m["comp"], (m["comp"], m["comp"]))
    start_utc = datetime.fromtimestamp(mi["gameStartMillis"] / 1000, tz=timezone.utc)
    dd, mm, yy = m["date"].split("-")
    n_rounds = len(d["roundResults"])
    red_w, blue_w = rounds_won.get("Red"), rounds_won.get("Blue")
    winner_side = "Red" if red_w > blue_w else "Blue"

    T["dim_match"].append({
        "match_id": match_id,
        "source_file": path.name,
        "competition_code": m["comp"],
        "competition_group": comp_group,
        "competition": comp_label,
        "game_no": int(m["num"]),
        "series_game": m["series"] or None,
        "match_date": f"20{yy}-{mm}-{dd}",
        "start_utc": start_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "start_brt": start_utc.astimezone(BRT).strftime("%Y-%m-%d %H:%M:%S"),
        "map_internal": mi["mapId"].split("/")[-1],
        "map_name": m["map"].title(),
        "game_length_ms": mi["gameLengthMillis"],
        "rounds_played": n_rounds,
        "is_overtime": n_rounds > 24,
        "red_team": team_name.get("Red"),
        "blue_team": team_name.get("Blue"),
        "red_rounds": red_w,
        "blue_rounds": blue_w,
        "winner_side": winner_side,
        "winner_team": team_name.get(winner_side),
        "n_coaches": len(d.get("coaches") or []),
        "n_observers": n_obs,
        "game_version": mi["gameVersion"],
    })
    for c in d.get("coaches") or []:
        T["fact_match_coach"].append({
            "match_id": match_id, "puuid": c["puuid"], "side": c["teamId"],
            "team_name": team_name.get(c["teamId"]),
        })

    # ---- jogadores por partida -----------------------------------------
    for u, p in roster.items():
        st = p["stats"]
        ac = st.get("abilityCasts") or {}
        T["fact_player_match"].append({
            "match_id": match_id, "puuid": u, "game_name": p["gameName"], "tag_line": p["tagLine"],
            "side": p["teamId"], "team_name": team_name.get(p["teamId"]),
            "agent_id": p["characterId"], "party_id": p["partyId"],
            "score": st["score"], "rounds_played": st["roundsPlayed"],
            "kills": st["kills"], "deaths": st["deaths"], "assists": st["assists"],
            "casts_grenade": ac.get("grenadeCasts"), "casts_ability1": ac.get("ability1Casts"),
            "casts_ability2": ac.get("ability2Casts"), "casts_ultimate": ac.get("ultimateCasts"),
            "competitive_tier": p["competitiveTier"], "account_level": p["accountLevel"],
        })
        T["_players"].append((u, p["gameName"], p["tagLine"], mi["gameStartMillis"]))

    # ---- rounds ---------------------------------------------------------
    for rr in d["roundResults"]:
        rn = rr["roundNum"]
        win_side = rr["winningTeam"] if rr["winningTeam"] in OTHER else None
        role = rr["winningTeamRole"]
        att = (win_side if role == "Attacker" else OTHER[win_side]) if win_side else None
        dfn = OTHER[att] if att else None
        role_of = {att: "Attacker", dfn: "Defender"}

        ps_list = [ps for ps in rr["playerStats"] if ps["puuid"] in roster]
        kills = []  # (ordem original, kill)
        for ps in ps_list:
            for k in ps["kills"]:
                kills.append(k)
        kills.sort(key=lambda k: k["timeSinceRoundStartMillis"])  # sort estavel

        n_alive_start = {s: sum(1 for u in roster if side_of[u] == s) for s in ("Red", "Blue")}
        alive = dict(n_alive_start)

        kill_rows = []
        for seq, k in enumerate(kills, start=1):
            killer, victim = k.get("killer") or None, k["victim"]
            ks, vs = side_of.get(killer), side_of.get(victim)
            locs = {pl["puuid"]: (pl["location"]["x"], pl["location"]["y"], pl["viewRadians"])
                    for pl in (k.get("playerLocations") or [])}
            vloc = loc(k.get("victimLocation"))
            v_allies = [(x, y) for u, (x, y, _) in locs.items() if side_of.get(u) == vs and u != victim]
            kloc = locs.get(killer)
            kloc_xy = (kloc[0], kloc[1]) if kloc else None
            k_allies = [(x, y) for u, (x, y, _) in locs.items() if side_of.get(u) == ks and u != killer]
            fd = k.get("finishingDamage") or {}
            kid = f"{match_id}:{rn}:{seq}"
            row = {
                "kill_id": kid, "match_id": match_id, "round_num": rn, "seq_in_round": seq,
                "time_in_round_ms": k["timeSinceRoundStartMillis"],
                "time_in_game_ms": k["timeSinceGameStartMillis"],
                "killer_puuid": killer, "victim_puuid": victim,
                "killer_side": ks, "victim_side": vs,
                "killer_team": team_name.get(ks), "victim_team": team_name.get(vs),
                "death_type": (
                    "bomb_detonation" if fd.get("damageType") == "Bomb" else
                    "self_inflicted" if killer == victim else
                    "teamkill" if (ks and ks == vs) else "enemy_kill"),
                "is_first_kill": False,  # preenchido abaixo (primeiro abate sobre INIMIGO)
                "victim_x": vloc[0] if vloc else None, "victim_y": vloc[1] if vloc else None,
                "killer_x": kloc[0] if kloc else None, "killer_y": kloc[1] if kloc else None,
                "victim_allies_alive_n": alive.get(vs, 0) - 1 if vs else None,
                "killer_allies_alive_n": alive.get(ks, 0) - 1 if ks else None,
                "victim_nearest_ally_dist": nearest(vloc, v_allies) if vloc else None,
                "killer_nearest_ally_dist": nearest(kloc_xy, k_allies) if kloc_xy else None,
                "damage_type": fd.get("damageType"), "damage_item": fd.get("damageItem"),
                "is_secondary_fire": fd.get("isSecondaryFireMode"),
                "n_assists": len(k.get("assistants") or []),
                "is_trade_kill": False, "death_was_traded": False,
            }
            if vs:
                alive[vs] -= 1
            kill_rows.append(row)
            for a in k.get("assistants") or []:
                T["fact_kill_assist"].append({"kill_id": kid, "puuid": a.get("assistantPuuid", a) if isinstance(a, dict) else a})
            for u, (x, y, vr) in locs.items():
                T["fact_kill_position"].append({
                    "kill_id": kid, "puuid": u, "side": side_of.get(u),
                    "x": x, "y": y, "view_radians": round(vr, 4),
                })

        # primeiro abate = primeira morte causada por um INIMIGO (ignora suicidio/bomba/teamkill)
        first_enemy = next((r for r in kill_rows if r["death_type"] == "enemy_kill"), None)
        if first_enemy:
            first_enemy["is_first_kill"] = True

        # trocas (janela de TRADE_WINDOW_MS) - so entre abates sobre inimigo
        enemy_rows = [r for r in kill_rows if r["death_type"] == "enemy_kill"]
        for a in enemy_rows:
            for b in enemy_rows:
                if a is b:
                    continue
                dt = b["time_in_round_ms"] - a["time_in_round_ms"]
                # b vinga a morte causada por a: b mata quem matou o aliado, dentro da janela
                if 0 <= dt <= TRADE_WINDOW_MS and b["victim_puuid"] == a["killer_puuid"] \
                        and b["killer_side"] == a["victim_side"]:
                    a["death_was_traded"] = True
                    b["is_trade_kill"] = True
        T["fact_kill"].extend(kill_rows)

        # por jogador no round
        # kills/deaths seguem a regra do placar oficial (validado contra stats.*):
        #   kill  = abate sobre inimigo (exclui suicidio e teamkill)
        #   death = qualquer morte, EXCETO detonacao do spike
        per_player = defaultdict(lambda: {"kills": 0, "deaths": 0, "assists": 0, "first_death": False})
        for r in kill_rows:
            if r["death_type"] != "bomb_detonation":
                per_player[r["victim_puuid"]]["deaths"] += 1
            if r["death_type"] == "enemy_kill":
                per_player[r["killer_puuid"]]["kills"] += 1
            if r["is_first_kill"]:
                per_player[r["victim_puuid"]]["first_death"] = True
        for k in kills:
            for a in k.get("assistants") or []:
                au = a.get("assistantPuuid", a) if isinstance(a, dict) else a
                per_player[au]["assists"] += 1
        first_killer = first_enemy["killer_puuid"] if first_enemy else None

        loadout = {"Red": 0, "Blue": 0}
        spent = {"Red": 0, "Blue": 0}
        for ps in ps_list:
            u = ps["puuid"]
            ec = ps.get("economy") or {}
            dmg = ps.get("damage") or []
            s = side_of[u]
            loadout[s] += ec.get("loadoutValue") or 0
            spent[s] += ec.get("spent") or 0
            T["fact_round_player"].append({
                "match_id": match_id, "round_num": rn, "puuid": u, "side": s,
                "team_name": team_name.get(s), "role": role_of.get(s),
                "score": ps["score"], "kills": per_player[u]["kills"],
                "deaths": per_player[u]["deaths"], "assists": per_player[u]["assists"],
                "first_kill": u == first_killer, "first_death": per_player[u]["first_death"],
                "damage_dealt": sum(x["damage"] for x in dmg),
                "headshots": sum(x["headshots"] for x in dmg),
                "bodyshots": sum(x["bodyshots"] for x in dmg),
                "legshots": sum(x["legshots"] for x in dmg),
                "loadout_value": ec.get("loadoutValue"), "spent": ec.get("spent"),
                "remaining": ec.get("remaining"),
                "weapon_id": ec.get("weapon") or None, "armor_id": ec.get("armor") or None,
            })

        planted = rr["bombPlanter"] is not None
        defused = rr["bombDefuser"] is not None
        pl = rr.get("plantLocation") or {}
        T["fact_round"].append({
            "match_id": match_id, "round_num": rn,
            "half": "H1" if rn < 12 else "H2" if rn < 24 else "OT",
            "is_pistol_round": rn in (0, 12),
            "winning_side": win_side, "winning_team": team_name.get(win_side),
            "winning_role": role,
            "attacker_side": att, "attacker_team": team_name.get(att),
            "defender_side": dfn, "defender_team": team_name.get(dfn),
            "round_result": rr["roundResult"], "result_code": rr["roundResultCode"],
            "ceremony": rr["roundCeremony"],
            "bomb_planted": planted, "plant_site": rr["plantSite"] or None,
            "planter_puuid": rr["bombPlanter"], "defuser_puuid": rr["bombDefuser"],
            "plant_time_ms": rr["plantRoundTime"] if planted else None,
            "defuse_time_ms": rr["defuseRoundTime"] if defused else None,
            "plant_x": pl.get("x") if planted else None, "plant_y": pl.get("y") if planted else None,
            "attacker_loadout_total": loadout.get(att), "defender_loadout_total": loadout.get(dfn),
            "attacker_spent_total": spent.get(att), "defender_spent_total": spent.get(dfn),
            "n_kills": len(enemy_rows),
        })
        # posicao e mira de cada jogador vivo no instante do plant e do defuse
        for event, key, t_ms in (("plant", "plantPlayerLocations", rr["plantRoundTime"] if planted else None),
                                 ("defuse", "defusePlayerLocations", rr["defuseRoundTime"] if defused else None)):
            for loc_ in rr.get(key) or []:
                if loc_["puuid"] in roster:
                    T["fact_objective_position"].append({
                        "match_id": match_id, "round_num": rn, "event": event, "time_in_round_ms": t_ms,
                        "puuid": loc_["puuid"], "side": side_of[loc_["puuid"]],
                        "x": loc_["location"]["x"], "y": loc_["location"]["y"],
                        "view_radians": round(loc_["viewRadians"], 4),
                    })


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="pasta com os JSONs (busca recursiva)")
    ap.add_argument("--output", required=True, help="pasta de saida dos CSVs")
    args = ap.parse_args()

    files = sorted(Path(args.input).rglob("*.json"))
    if not files:
        sys.exit(f"Nenhum .json encontrado em {args.input}")
    T = defaultdict(list)
    issues, seen = [], set()
    for f in files:
        try:
            process(f, T, issues, seen)
        except Exception as e:  # um arquivo ruim nao derruba o resto
            issues.append({"file": f.name, "issue": f"erro ao processar: {type(e).__name__}: {e}"})

    # dimensoes derivadas
    players = pd.DataFrame(T.pop("_players"), columns=["puuid", "game_name", "tag_line", "ts"])
    players = players.sort_values("ts")
    n_names = players.groupby("puuid")["game_name"].nunique().rename("n_name_variants")
    dim_player = players.drop_duplicates("puuid", keep="last").drop(columns="ts").merge(n_names, on="puuid")
    dim_player = dim_player.rename(columns={"game_name": "latest_game_name", "tag_line": "latest_tag_line"})

    dm = pd.DataFrame(T["dim_match"])
    names = sorted(set(dm["red_team"].dropna()) | set(dm["blue_team"].dropna()))
    dim_team = pd.DataFrame({"team_name": names,
                             "team_display": [n.replace("_", " ").title() for n in names]})

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    tables = {k: pd.DataFrame(v) for k, v in T.items()}
    tables["dim_player"] = dim_player
    tables["dim_team"] = dim_team
    for name, df in tables.items():
        # inteiros com nulos viram float no pandas ("5356.0"); devolve para Int64 para o CSV sair limpo
        for c in df.select_dtypes("float").columns:
            nn = df[c].dropna()
            if len(nn) and (nn == nn.round()).all():
                df[c] = df[c].astype("Int64")
        df.to_csv(out / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name:20s} {len(df):>9,d} linhas")
    pd.DataFrame(issues, columns=["file", "issue"]).to_csv(out / "ingest_issues.csv", index=False)
    print(f"\n{len(files)} arquivos lidos, {len(seen)} partidas carregadas, {len(issues)} avisos.")
    for i in issues:
        print("  AVISO:", i["file"], "->", i["issue"])


if __name__ == "__main__":
    main()
