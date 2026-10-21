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


def match_frame(df: pd.DataFrame, team: str, match_id: str, map_name: str) -> pd.DataFrame:
    """Linhas do time nesta partida + linhas dos outros times no mesmo mapa (a referencia).
    Passe o resultado para metrics.team_metrics."""
    same_map = df[df["map_name"] == map_name]
    return same_map[(same_map["team"] != team) | (same_map["match_id"] == match_id)]
