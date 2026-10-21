"""
Metricas, referencia da competicao e intervalos de confianca.

Toda metrica e uma razao  x / n  calculada sobre a tabela team_round
(uma linha por time em cada round). Isso permite:
  * a taxa do time            = soma(x) / soma(n) nas linhas do time
  * a referencia              = soma(x) / soma(n) nas linhas de TODOS OS OUTROS times
                                (mesmos filtros de competicao, mapa e lado)
  * um intervalo de confianca = tratando cada PARTIDA como uma unidade (rounds da mesma
                                partida nao sao independentes): estimador de razao com
                                distribuicao t, que fica mais largo quando ha poucas partidas
  * um veredito               = so afirma "acima/abaixo" se o intervalo do time
                                a diferenca para a referencia supera a incerteza (do time E da
                                referencia), vale pelo menos MIN_DELTA_PP pontos percentuais e
                                ha amostra suficiente.
Aviso: sao 11 comparacoes por time a 95%; alguma diferenca pode aparecer por acaso.
Por isso o app mostra sempre o intervalo e o n, e chama os resultados de "indicios".
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd

# quantil 97,5% da t de Student por graus de liberdade (1..30); acima disso aproxima
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048,
        29: 2.045, 30: 2.042}


def t975(df_):
    return T975.get(df_, 2.02 if df_ < 60 else 2.0 if df_ < 120 else 1.96)

MIN_N = 15           # minimo de rounds/eventos para opinar
MIN_MATCHES = 3      # minimo de partidas com a situacao
MIN_DELTA_PP = 3.0   # efeito minimo (pontos percentuais) para chamar de diferenca: evita rotular ruido


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    what: str                         # frase curta: o que a taxa mede
    x: Callable[[pd.DataFrame], pd.Series]
    n: Callable[[pd.DataFrame], pd.Series]
    higher_better: bool = True
    unit: str = "rounds"              # "rounds" ou "mortes" (para exibir o n)
    group: str = ""
    neutral: bool = False             # depende da funcao/estilo: diferenca vira "perfil", nao ponto forte/atencao


def _b(s):  # bool -> int
    return s.astype(int)


METRICS = [
    Metric("fk_rate", "Primeiro abate (taxa)",
           "% dos rounds em que o time faz o primeiro abate",
           lambda d: _b(d.first_kill), lambda d: _b(d.has_fk), group="Abertura do round"),
    Metric("fk_conv", "Conversão após first kill",
           "% de rounds vencidos quando o time faz o primeiro abate",
           lambda d: _b(d.first_kill & d.won), lambda d: _b(d.first_kill), group="Abertura do round"),
    Metric("fd_recovery", "Recuperação após first death",
           "% de rounds vencidos mesmo sofrendo o primeiro abate",
           lambda d: _b(d.first_death & d.won), lambda d: _b(d.first_death), group="Abertura do round"),
    Metric("trade_rate", "Mortes trocadas",
           "% das mortes em que o time vinga o aliado em até 5 s",
           lambda d: d.deaths_traded, lambda d: d.deaths_enemy, unit="mortes", group="Jogo coletivo"),
    Metric("isolated_rate", "Mortes isoladas",
           "% das mortes com o aliado vivo mais próximo muito longe",
           lambda d: d.isolated_deaths, lambda d: d.deaths_with_dist, higher_better=False, unit="mortes",
           group="Jogo coletivo"),
    Metric("pistol_win", "Rounds de pistola",
           "% de pistol rounds vencidos",
           lambda d: _b(d.is_pistol & d.won), lambda d: _b(d.is_pistol), group="Economia"),
    Metric("econ_adv_conv", "Conversão de vantagem econômica",
           "% de rounds vencidos quando o time gasta bem mais que o adversário",
           lambda d: _b((d.econ_state == "vantagem") & d.won), lambda d: _b(d.econ_state == "vantagem"),
           group="Economia"),
    Metric("econ_disadv_win", "Vitórias em desvantagem econômica",
           "% de rounds vencidos gastando bem menos que o adversário",
           lambda d: _b((d.econ_state == "desvantagem") & d.won), lambda d: _b(d.econ_state == "desvantagem"),
           group="Economia"),
    Metric("plant_rate", "Plant (ataque)",
           "% dos rounds de ataque em que o spike é plantado",
           lambda d: _b((d.role == "Attacker") & d.bomb_planted), lambda d: _b(d.role == "Attacker"),
           group="Ataque e defesa"),
    Metric("post_plant_win", "Pós-plant (ataque)",
           "% de rounds vencidos depois de plantar",
           lambda d: _b((d.role == "Attacker") & d.bomb_planted & d.won),
           lambda d: _b((d.role == "Attacker") & d.bomb_planted), group="Ataque e defesa"),
    Metric("retake_win", "Retake (defesa)",
           "% de rounds vencidos pela defesa depois que o spike é plantado",
           lambda d: _b((d.role == "Defender") & d.bomb_planted & d.won),
           lambda d: _b((d.role == "Defender") & d.bomb_planted), group="Ataque e defesa"),
]
BY_KEY = {m.key: m for m in METRICS}


# ---------------------------------------------------------------- dados
def load(processed_dir="data/processed") -> pd.DataFrame:
    return pd.read_csv(Path(processed_dir) / "team_round.csv", low_memory=False)


def apply_filters(df, competitions: Optional[Sequence[str]] = None,
                  maps: Optional[Sequence[str]] = None, role: Optional[str] = None):
    """role: None (todos), 'Attacker' ou 'Defender'."""
    if competitions:
        df = df[df["competition"].isin(competitions)]
    if maps:
        df = df[df["map_name"].isin(maps)]
    if role:
        df = df[df["role"] == role]
    return df


def list_teams(df, min_rounds=0) -> pd.DataFrame:
    g = df.groupby("team").agg(rounds=("round_num", "size"), partidas=("match_id", "nunique"))
    return g[g["rounds"] >= min_rounds].sort_values("rounds", ascending=False)


# ---------------------------------------------------------------- calculo
def _per_match(df, m: Metric):
    t = pd.DataFrame({"match_id": df["match_id"], "x": m.x(df), "n": m.n(df)})
    return t.groupby("match_id")[["x", "n"]].sum()


def _ratio_se(pm: pd.DataFrame):
    """Taxa soma(x)/soma(n) e erro-padrao tratando cada partida como uma unidade
    (estimador de razao). Retorna (taxa, erro_padrao, partidas_usadas)."""
    pm = pm[pm["n"] > 0]
    k = len(pm)
    if k == 0:
        return np.nan, np.nan, 0
    X, N = pm["x"].to_numpy(float), pm["n"].to_numpy(float)
    r = X.sum() / N.sum()
    if k < 2:
        return r, np.nan, k
    e = X - r * N
    var = k / (k - 1) * (e ** 2).sum() / N.sum() ** 2
    return r, float(np.sqrt(var)), k


def team_metrics(df: pd.DataFrame, team: str, min_n=MIN_N, min_matches=MIN_MATCHES,
                 min_delta_pp=MIN_DELTA_PP, metrics: Sequence[Metric] = None, key_col: str = "team") -> pd.DataFrame:
    """`df` ja deve vir filtrado (competicao/mapa/lado). Referencia = todos os outros times de `df`.
    `metrics`/`key_col` permitem a mesma analise para outra unidade (ex.: jogador, em players.py)."""
    mine, ref = df[df[key_col] == team], df[df[key_col] != team]
    rows = []
    for m in (METRICS if metrics is None else metrics):
        pm = _per_match(mine, m)
        x, n = int(pm["x"].sum()), int(pm["n"].sum())
        rate, se, k = _ratio_se(pm)
        pr = _per_match(ref, m)
        ref_rate, ref_se, _ = _ratio_se(pr)
        rn = int(pr["n"].sum())
        crit = t975(k - 1) if k >= 2 else np.nan
        lo = max(0.0, rate - crit * se) if n and not np.isnan(se) else np.nan
        hi = min(1.0, rate + crit * se) if n and not np.isnan(se) else np.nan

        # posicao entre os times com amostra suficiente (percentil)
        per_team = ref.assign(_x=m.x(ref), _n=m.n(ref)).groupby(key_col)[["_x", "_n"]].sum()
        per_team = per_team[per_team["_n"] >= min_n]
        rates = (per_team["_x"] / per_team["_n"]).to_numpy()
        pct = float((rates < rate).mean() * 100) if n and len(rates) else np.nan
        if n and len(rates) and not m.higher_better:
            pct = 100 - pct

        diff = rate - ref_rate if n else np.nan
        if n == 0:
            verdict, gap = "sem_dados", 0.0
        elif n < min_n or k < min_matches or np.isnan(se):
            verdict, gap = "insuficiente", 0.0
        else:
            margin = crit * float(np.sqrt(se ** 2 + (0.0 if np.isnan(ref_se) else ref_se) ** 2))
            gap = abs(diff) - margin
            if gap > 0 and abs(diff) * 100 >= min_delta_pp:
                verdict = "acima" if diff > 0 else "abaixo"
            else:
                verdict, gap = "em_linha", 0.0
        if verdict in ("acima", "abaixo") and m.neutral:
            quality = f"perfil_{verdict}"
        elif verdict in ("acima", "abaixo"):
            good = (verdict == "acima") == m.higher_better
            quality = "ponto_forte" if good else "ponto_de_atencao"
        else:
            quality = verdict
        rows.append(dict(key=m.key, group=m.group, label=m.label, what=m.what, unit=m.unit,
                         x=x, n=n, n_matches=k, rate=rate, ref_rate=ref_rate, ref_n=rn,
                         delta_pp=diff * 100 if n else np.nan, ci_low=lo, ci_high=hi,
                         percentile=pct, n_teams_ref=len(rates), verdict=verdict, quality=quality,
                         gap=gap, higher_better=m.higher_better, neutral=m.neutral))
    return pd.DataFrame(rows)


def team_metrics_by_map(df: pd.DataFrame, team: str) -> list:
    """Uma analise por mapa jogado pelo time. `df` ja deve vir filtrado (competicao/mapa/lado).
    Em cada mapa a referencia e formada pelos outros times NO MESMO mapa.
    Retorna lista de dicts (map_name, n_matches, rounds, rounds_won, res), do mapa mais jogado ao menos jogado."""
    mine = df[df["team"] == team]
    out = []
    for mp, g in mine.groupby("map_name"):
        out.append(dict(map_name=mp, n_matches=int(g["match_id"].nunique()), rounds=len(g),
                        rounds_won=int(g["won"].sum()), res=team_metrics(df[df["map_name"] == mp], team)))
    return sorted(out, key=lambda r: (-r["n_matches"], -r["rounds"], r["map_name"]))
