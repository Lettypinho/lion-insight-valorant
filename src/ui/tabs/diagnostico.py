"""Aba 1: diagnóstico — panorama geral do time e análise de cada mapa jogado.

Duas leituras convivem aqui:
  * confirmada: ponto forte / ponto de atenção, só quando o critério estatístico de src.analytics.metrics é atendido;
  * descritiva: todos os números, mesmo de um mapa com uma única partida, sempre com a amostra e o aviso de amostra pequena.
"""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M
from src.ui.components import evidence_table, insight_card, pct_bar, show_metrics_table
from src.ui.formatting import pct


def _cards(dg: dict, R: pd.DataFrame, df: pd.DataFrame, team: str):
    ins = dg["insights"]
    mixed = [i for i in ins if i["quality"] == "misto" or len(i["keys"]) > 1]
    rest = [i for i in ins if i not in mixed]
    for i in mixed:
        insight_card(i, R, df, team)
    good = [i for i in rest if i["quality"] == "ponto_forte"]
    bad = [i for i in rest if i["quality"] == "ponto_de_atencao"]
    if good or bad:
        left, right = st.columns(2)
        with left:
            st.markdown("**O que está funcionando**")
            if not good:
                st.caption("Nenhum ponto forte confirmado isolado.")
            for i in good:
                insight_card(i, R, df, team)
        with right:
            st.markdown("**O que precisa de atenção**")
            if not bad:
                st.caption("Nenhum ponto de atenção confirmado isolado.")
            for i in bad:
                insight_card(i, R, df, team)


def _labels(res: pd.DataFrame, quality: str) -> str:
    return ", ".join(res.loc[res["quality"] == quality, "label"]) or "—"


def _overview(by_map: list) -> pd.DataFrame:
    return pd.DataFrame({
        "Mapa": [m["map_name"] for m in by_map],
        "Partidas": [m["n_matches"] for m in by_map],
        "Rounds vencidos": [f"{m['rounds_won']} de {m['rounds']}" for m in by_map],
        "% de rounds vencidos": [m["rounds_won"] / m["rounds"] * 100 for m in by_map],
        "Pontos fortes confirmados": [_labels(m["res"], "ponto_forte") for m in by_map],
        "Pontos de atenção confirmados": [_labels(m["res"], "ponto_de_atencao") for m in by_map],
        "Amostra": ["suficiente" if m["n_matches"] >= M.MIN_MATCHES else "pequena" for m in by_map],
    })


def _map_detail(m: dict, df_f: pd.DataFrame, team: str):
    mp, res, dg = m["map_name"], m["res"], m["dg"]
    df_map = df_f[df_f["map_name"] == mp]
    R = res.set_index("key")
    st.caption(f"{m['n_matches']} partida(s) e {m['rounds']} rounds em {mp}. "
               f"Referência: os outros times em {mp}, com os mesmos filtros.")
    if m["n_matches"] < M.MIN_MATCHES:
        st.warning(f"Amostra pequena: {m['n_matches']} partida(s) neste mapa. Os números abaixo descrevem o que aconteceu, "
                   f"mas não confirmam um padrão (são necessárias ao menos {M.MIN_MATCHES} partidas).")
    if dg["insights"]:
        _cards(dg, R, df_map, team)
    elif m["n_matches"] >= M.MIN_MATCHES:
        st.info(f"Nenhuma diferença confirmada em {mp}: o time joga perto da referência neste mapa.")

    st.markdown("**Todos os números neste mapa** — do melhor para o pior em relação à referência")
    show_metrics_table(res)

    with st.expander(f"Ver os rounds de uma métrica em {mp}"):
        available = res.loc[res["n"] > 0, "key"].tolist()
        if not available:
            st.info("Nenhuma métrica com dados neste mapa.")
            return
        key = st.selectbox("Métrica", available, format_func=lambda k: M.BY_KEY[k].label, key=f"ev_{team}_{mp}")
        _, out = evidence_table(df_map, team, key, None)
        st.caption(f"{M.BY_KEY[key].what}. {len(out)} rounds.")
        st.dataframe(out, hide_index=True, width="stretch", height=min(360, 38 + 35 * len(out)))


def render(dg: dict, R: pd.DataFrame, res: pd.DataFrame, df_f: pd.DataFrame, team: str, by_map: list):
    # ---------------------------------------------------------------- panorama geral
    st.subheader("Panorama geral")
    st.caption("Todos os mapas do recorte. Referência: os outros times, com os mesmos filtros.")
    if dg["insights"]:
        _cards(dg, R, df_f, team)
    else:
        st.info("Nenhuma diferença confirmada em relação à competição somando todos os mapas. "
                "Diferenças de mapas específicos podem se anular na soma: veja a análise por mapa abaixo.")
    with st.expander("Todos os números do panorama geral"):
        show_metrics_table(res)
        na = res.loc[res["n"] == 0, "label"].tolist()
        if na:
            st.caption("Não se aplica ao recorte: " + ", ".join(na) + ".")

    # ---------------------------------------------------------------- por mapa
    st.subheader("Por mapa")
    st.caption(f"Cada mapa é comparado com os outros times no mesmo mapa. Pontos fortes e de atenção só são confirmados "
               f"com ao menos {M.MIN_MATCHES} partidas e {M.MIN_N} rounds ou eventos; com menos, os números aparecem como descrição.")
    st.dataframe(_overview(by_map), hide_index=True, width="stretch",
                 column_config={"% de rounds vencidos": pct_bar("% de rounds vencidos")})
    names = [m["map_name"] for m in by_map]
    count = {m["map_name"]: m["n_matches"] for m in by_map}
    chosen = st.segmented_control("Ver o mapa", names, default=names[0], key=f"diag_map_{team}_{hash(tuple(names))}",
                                  format_func=lambda n: f"{n} ({count[n]})") or names[0]
    _map_detail(next(m for m in by_map if m["map_name"] == chosen), df_f, team)

    st.caption(f"São indícios, não sentenças: com {len(M.METRICS)} comparações por recorte, algum resultado pode aparecer por acaso.")
