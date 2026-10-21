"""Teste de nulidade: forma 'times' sinteticos sorteando um time ao acaso em cada partida.
Nao ha diferenca real, entao a taxa de alertas deve ficar perto de ~5% por metrica (0,55 de 11)."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
from src.analytics import metrics as M
df = M.load(); rng = np.random.default_rng(1)
mids = df.match_id.unique(); res = {}
sizes = [int(a) for a in sys.argv[1].split(',')] if len(sys.argv) > 1 else [3, 5, 8, 15, 30]
min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else M.MIN_MATCHES
min_delta = float(sys.argv[3]) if len(sys.argv) > 3 else M.MIN_DELTA_PP
n_pseudo = 80
tt = df[['match_id', 'team']].drop_duplicates()
by_match = tt.groupby('match_id')['team'].apply(list).to_dict()
for m in sizes:
    flags = []; applicable = []
    for _ in range(n_pseudo):
        pick = rng.choice(mids, m, replace=False)
        d = df.copy()
        chosen = {mid: rng.choice(by_match[mid]) for mid in pick}
        mask = d.match_id.isin(pick) & (d.team == d.match_id.map(chosen))
        d.loc[mask, 'team'] = 'PSEUDO'
        r = M.team_metrics(d, 'PSEUDO', min_matches=min_matches, min_delta_pp=min_delta)
        ok = r[r.verdict.isin(['acima', 'abaixo', 'em_linha'])]
        flags.append(int(ok.verdict.isin(['acima', 'abaixo']).sum())); applicable.append(len(ok))
    res[m] = (np.mean(flags), np.mean(applicable), np.mean(flags) / max(np.mean(applicable), 1e-9))
    print(f'{m:2d} partidas: {res[m][0]:.2f} alertas/time de {res[m][1]:.1f} metricas avaliaveis -> taxa de falso alerta {res[m][2]:.1%}')
