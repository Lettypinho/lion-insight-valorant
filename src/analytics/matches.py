"""
Recortes de uma partida do time.

Uma partida isolada nao pode usar a referencia "outros times do recorte": dentro dela o unico outro time
e o adversario. Por isso a referencia de uma partida e formada pelos outros times NO MESMO MAPA,
com os demais filtros (competicao, lado) ja aplicados em `df`.
"""
import pandas as pd


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


def match_frame(df: pd.DataFrame, team: str, match_id: str, map_name: str) -> pd.DataFrame:
    """Linhas do time nesta partida + linhas dos outros times no mesmo mapa (a referencia).
    Passe o resultado para metrics.team_metrics."""
    same_map = df[df["map_name"] == map_name]
    return same_map[(same_map["team"] != team) | (same_map["match_id"] == match_id)]
