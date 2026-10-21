"""Aba 4: metodologia — de onde vêm os números e quando o sistema afirma algo."""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M


def render():
    st.markdown(f"""
**De onde vêm os números.** Apenas dos arquivos JSON de partidas fornecidos pela organização do Hackathon: nenhuma API, coleta ou
dado externo. A análise é toda pós-partida.

**Como lemos um round.** Para cada time em cada round registramos quem fez o primeiro abate, quantas mortes foram trocadas em até 5 s,
quantas mortes aconteceram longe dos aliados (aliado vivo mais próximo a mais de 3000 unidades do jogo), a economia relativa ao
adversário (vantagem: loadout ≥ 1,25× o do adversário; desvantagem: ≤ 0,80×) e o que aconteceu com o spike — inclusive
se quem plantou foi abatido em até 5 s sem troca (plant sem cobertura, do lado do ataque; punição ao plant, do lado da defesa).

**A referência.** É a taxa de todos os *outros* times, nas mesmas condições (competição, mapa e lado). O time nunca é comparado com ele mesmo.

**Quando o sistema afirma algo.** Cada partida conta como uma unidade, porque rounds da mesma partida não são independentes.
Só dizemos "acima" ou "abaixo" quando a diferença supera a incerteza do time *e* da referência, vale pelo menos
{M.MIN_DELTA_PP:.0f} pontos percentuais e há ao menos {M.MIN_N} rounds ou eventos em {M.MIN_MATCHES} partidas.
Testamos o método com times sorteados ao acaso, sem diferença real: o falso alerta ficou entre 4% e 7% (esperado: 5%).

**O que ainda pode enganar.**
- São {len(M.METRICS)} comparações por time, então cerca de {str(round(len(M.METRICS) * 0.05, 1)).replace(".", ",")} alerta por acaso é esperado. Leia como indício.
- Um time muito forte tende a ficar acima da referência em quase tudo. Os contrastes dentro do próprio time costumam ser mais úteis.
- A referência mistura adversários de níveis diferentes e não corrige a força do adversário em cada partida.
- Só temos posições no momento de kills, plant e defuse, não o trajeto completo, e nenhuma informação de habilidades usadas por round.
""")
    st.markdown(f"**As {len(M.METRICS)} métricas**")
    st.dataframe(pd.DataFrame({"Grupo": [m.group for m in M.METRICS], "Métrica": [m.label for m in M.METRICS],
                               "O que mede": [m.what for m in M.METRICS],
                               "Melhor quando": ["maior" if m.higher_better else "menor" for m in M.METRICS]}),
                 hide_index=True, width="stretch")
