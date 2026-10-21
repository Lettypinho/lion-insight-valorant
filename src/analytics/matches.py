"""
Recortes de uma partida do time.

Uma partida isolada nao pode usar a referencia "outros times do recorte": dentro dela o unico outro time
e o adversario. Por isso a referencia de uma partida e formada pelos outros times NO MESMO MAPA,
com os demais filtros (competicao, lado) ja aplicados em `df`.
"""
import numpy as np
import pandas as pd

TRADE_WINDOW_MS = 5000  # mesma janela do trade (ingest.py) e do plant sem cobertura (build_features.py)

DEATH_PT = {"trocada": "Trocada", "nao_trocada": "Não trocada", "sem_aliado": "Sem aliado vivo",
            "indefinida": "—"}


def team_matches(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Partidas do time em `df`, da mais recente para a mais antiga, com placar a partir dos rounds do time.
    `df` deve vir sem filtro de lado para o placar ser o da partida inteira."""
    mine = df[df["team"] == team]
    g = mine.groupby("match_id").agg(match_date=("match_date", "first"), map_name=("map_name", "first"),
                                     competition=("competition", "first"), opponent=("opponent", "first"),
                                     rounds=("won", "size"), won=("won", "sum"))
    g["lost"] = g["rounds"] - g["won"]
    g["result"] = g.apply(lambda r: "V" if r.won > r.lost else "D" if r.won < r.lost else "E", axis=1)
    return g.sort_values(["match_date", "match_id"], ascending=[False, True]).reset_index()


def spike_planted_at(r, t_ms) -> bool:
    """O spike ja estava plantado no instante `t_ms` do round? (mesmo relogio dos abates: validado em dataset.md)."""
    return bool(r.bomb_planted) and pd.notna(r.plant_time_ms) and r.plant_time_ms <= t_ms


def round_moments(kills: pd.DataFrame, r) -> list:
    """Momentos do round em ordem cronologica: abates, plant e defuse.
    Cada item: dict(id, kind ('kill'|'plant'|'defuse'), time_ms, seq). id: 'k<seq>', 'plant' ou 'defuse'."""
    out = [dict(id=f"k{int(k.seq_in_round)}", kind="kill", time_ms=k.time_in_round_ms, seq=int(k.seq_in_round))
           for k in kills.itertuples()]
    if bool(r.bomb_planted) and pd.notna(r.plant_time_ms):
        out.append(dict(id="plant", kind="plant", time_ms=r.plant_time_ms, seq=None))
    if pd.notna(getattr(r, "defuse_time_ms", None)):
        out.append(dict(id="defuse", kind="defuse", time_ms=r.defuse_time_ms, seq=None))
    order = {"plant": 0, "kill": 1, "defuse": 2}  # empate de horario: plant antes do abate, defuse depois
    return sorted(out, key=lambda m: (m["time_ms"], order[m["kind"]], m["seq"] or 0))


def classify_deaths(kills: pd.DataFrame, r) -> pd.DataFrame:
    """Classifica cada morte de um round (kill_events), do ponto de vista de quem morreu.
    death_class: trocada | nao_trocada (havia aliado vivo e ninguem vingou em 5 s) | sem_aliado (ultimo vivo:
    nao havia quem trocasse) | indefinida (sem posicoes). planter_punished: o plantador morreu em ate 5 s apos
    o plant e a morte nao foi trocada (mesma regra de metricas.md 9.1).
    trade_seq / trade_after_ms: # do abate que vingou a morte e quanto tempo depois (mesma regra do ingest.py);
    avenged_seq: no abate de troca, # da morte que ele vingou."""
    k = kills.copy()
    k["trade_seq"], k["trade_after_ms"], k["avenged_seq"] = np.nan, np.nan, np.nan
    if {"killer_puuid", "killer_team"} <= set(k.columns):
        p = k[["seq_in_round", "time_in_round_ms", "killer_puuid", "victim_team"]].merge(
            k[["seq_in_round", "time_in_round_ms", "victim_puuid", "killer_team"]], how="cross", suffixes=("", "_b"))
        dt = p["time_in_round_ms_b"] - p["time_in_round_ms"]
        p = p[(p["victim_puuid"] == p["killer_puuid"]) & (p["killer_team"] == p["victim_team"])
              & (dt >= 0) & (dt <= TRADE_WINDOW_MS) & (p["seq_in_round_b"] != p["seq_in_round"])]
        p = p.assign(dt=dt).sort_values("dt")
        first = p.drop_duplicates("seq_in_round").set_index("seq_in_round")
        k["trade_seq"] = k["seq_in_round"].map(first["seq_in_round_b"])
        k["trade_after_ms"] = k["seq_in_round"].map(first["dt"])
        k["avenged_seq"] = k["seq_in_round"].map(p.drop_duplicates("seq_in_round_b").set_index("seq_in_round_b")["seq_in_round"])
    alive = k["victim_allies_alive"] if "victim_allies_alive" in k else pd.Series(np.nan, index=k.index)
    k["death_class"] = np.select(
        [k["death_was_traded"].astype(bool), alive == 0, alive > 0],
        ["trocada", "sem_aliado", "nao_trocada"], "indefinida")
    lag = k["time_in_round_ms"] - (r.plant_time_ms if bool(r.bomb_planted) and pd.notna(r.plant_time_ms) else np.nan)
    k["planter_punished"] = ((k["victim_puuid"] == r.planter_puuid) & (lag >= 0) & (lag <= TRADE_WINDOW_MS)
                             & ~k["death_was_traded"].astype(bool))
    return k


def death_summary(k: pd.DataFrame, team: str) -> dict:
    """Contagens do round para o time (k = saida de classify_deaths)."""
    mine, opp = k[k["victim_team"] == team], k[k["victim_team"] != team]
    return dict(deaths=len(mine), traded=int((mine["death_class"] == "trocada").sum()),
                untraded=int((mine["death_class"] == "nao_trocada").sum()),
                last_alive=int((mine["death_class"] == "sem_aliado").sum()),
                isolated=int(mine["isolated"].sum()), kills=len(opp),
                trade_kills=int(opp["is_trade_kill"].sum()))


def match_frame(df: pd.DataFrame, team: str, match_id: str, map_name: str) -> pd.DataFrame:
    """Linhas do time nesta partida + linhas dos outros times no mesmo mapa (a referencia).
    Passe o resultado para metrics.team_metrics."""
    same_map = df[df["map_name"] == map_name]
    return same_map[(same_map["team"] != team) | (same_map["match_id"] == match_id)]
