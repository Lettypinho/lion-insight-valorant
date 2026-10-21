"""Orientação e enquadramento dos mapas desenhados com as coordenadas da base.

* Orientação: gira cada mapa em passos de 90° (nunca espelha) para que os sites fiquem na horizontal,
  com o site A à direita ("C, B, A"). Calculada pela posição mediana dos plants de cada site.
* Enquadramento: a área do gráfico vem do miolo da silhueta (percentis 0,2% a 99,8%), porque há posições
  muito fora do mapa (ex.: x ~ -50.000 em Breeze e Haven) que espremeriam o desenho num canto.
"""
import numpy as np
import pandas as pd

Q_LOW, Q_HIGH, MARGIN = 0.002, 0.998, 0.04


def to_view(x, y, k: int):
    """Coordenadas do jogo -> coordenadas de exibição (u para a direita, w para cima), girando k x 90° anti-horário."""
    u, w = np.asarray(x, float), -np.asarray(y, float)
    for _ in range(k % 4):
        u, w = -w, u
    return u, w


def rotation_for(sites: pd.DataFrame) -> int:
    """sites: plant_site, plant_x, plant_y (medianas). Retorna k em 0..3."""
    s = sites.sort_values("plant_site")
    if len(s) < 2:
        return 0
    first, last = s.iloc[0], s.iloc[-1]
    for k in range(4):
        (ua, ul), (wa, wl) = to_view([first.plant_x, last.plant_x], [first.plant_y, last.plant_y], k)
        if abs(ua - ul) > abs(wa - wl) and ua > ul:
            return k
    return 0


def build_views(team_round: pd.DataFrame, silhouette: pd.DataFrame) -> dict:
    """{mapa: dict(k, xrange, yrange)}."""
    p = team_round[team_round["bomb_planted"].astype(bool) & team_round["plant_x"].notna()]
    med = p.groupby(["map_name", "plant_site"])[["plant_x", "plant_y"]].median().reset_index()
    views = {}
    for mp, g in silhouette.groupby("map_name"):
        k = rotation_for(med[med["map_name"] == mp])
        u, w = to_view(g["x"], g["y"], k)
        (u0, u1), (w0, w1) = np.quantile(u, [Q_LOW, Q_HIGH]), np.quantile(w, [Q_LOW, Q_HIGH])
        mu, mw = (u1 - u0) * MARGIN, (w1 - w0) * MARGIN
        views[mp] = dict(k=k, xrange=[u0 - mu, u1 + mu], yrange=[w0 - mw, w1 + mw])
    return views


def inside(view: dict, u, w):
    return (u >= view["xrange"][0]) & (u <= view["xrange"][1]) & (w >= view["yrange"][0]) & (w <= view["yrange"][1])
