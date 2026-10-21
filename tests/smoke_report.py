"""Relatorio de teste no terminal. Uso: python tests/smoke_report.py [--team NOME] [--competition NOME] [--role Attacker|Defender]"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.analytics import metrics as M
from src.insights import engine as D

ap = argparse.ArgumentParser()
ap.add_argument("--team"); ap.add_argument("--competition", action="append"); ap.add_argument("--map", action="append")
ap.add_argument("--role"); ap.add_argument("--processed", default="data/processed")
a = ap.parse_args()
df = M.apply_filters(M.load(a.processed), a.competition, a.map, a.role)
team = a.team or M.list_teams(df).index[0]
print(f"TIME: {team} | filtros: competicao={a.competition} mapa={a.map} lado={a.role}")
t = M.list_teams(df).loc[team]; print(f"{int(t.rounds)} rounds em {int(t.partidas)} partidas\n")
res = M.team_metrics(df, team)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
show = res[["label", "x", "n", "n_matches", "rate", "ref_rate", "delta_pp", "ci_low", "ci_high", "percentile", "verdict"]].copy()
for c in ("rate", "ref_rate", "ci_low", "ci_high"): show[c] = (show[c] * 100).round(1)
show["delta_pp"] = show["delta_pp"].round(1); show["percentile"] = show["percentile"].round(0)
print(show.to_string(index=False))
dg = D.diagnose(res)
print("\nDIAGNOSTICOS")
for i in dg["insights"]:
    print(f" [{i['quality']}] {i['title']}\n    {i['text']}")
print("\nsem diferenca confiavel:", dg["notes"]["em_linha"]); print("amostra insuficiente:", dg["notes"]["insuficiente"])
if dg["insights"]:
    top = dg["insights"][0]; k = top["keys"][0]
    ev = D.evidence(df, team, k, top["quality"] if top["quality"] != "misto" else None)
    print(f"\nEVIDENCIA do 1o insight ({k}): {len(ev)} rounds; primeiros 6:")
    print(ev[["match_date", "map_name", "opponent", "round_label", "role", "resultado", "detalhe"]].head(6).to_string(index=False))
