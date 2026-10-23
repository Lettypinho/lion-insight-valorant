"""Como os números são produzidos e quais são as limitações da leitura."""
import pandas as pd
import streamlit as st

from src.analytics import metrics as M


def render():
    st.subheader("Como calculamos")
    st.markdown(f"""
**1. Dados de desempenho.** Todas as estatísticas de partidas vêm exclusivamente dos JSONs fornecidos pela organização do
Hackathon. Catálogos públicos são usados **somente para traduzir IDs estáticos do jogo** (por exemplo, agente, arma e
armadura); eles não adicionam resultados, eventos ou estatísticas de partidas. A análise é exclusivamente pós-partida.

**2. Como lemos um round.** Para cada time em cada round registramos primeiro abate, trocas em até 5 s, mortes isoladas,
economia relativa, plant, pós-plant e retake. Uma morte só entra como possível troca quando havia aliado vivo. Para morte
isolada, usamos a distância ao aliado vivo mais próximo; acima de 3000 unidades do jogo é classificada como isolada.

**3. O que significa “referência”.** É o conjunto dos **outros times** que permanece depois dos filtros escolhidos. Sem
filtro de campeonato/etapa, a base completa entra no contexto. Se o usuário filtra campeonato, etapa, mapa ou lado, o
mesmo recorte é aplicado ao time e à referência. O time nunca é comparado com ele mesmo.

**4. Quando chamamos algo de ponto forte ou atenção.** Cada partida é tratada como uma unidade, porque rounds da mesma
partida não são independentes. Só dizemos “acima” ou “abaixo” quando a diferença supera a incerteza do time e da referência,
vale pelo menos {M.MIN_DELTA_PP:.0f} pontos percentuais e há ao menos {M.MIN_N} rounds/eventos em {M.MIN_MATCHES} partidas.
Nos testes de calibração com times aleatórios sem diferença real, a taxa de falso alerta ficou próxima do esperado para 95% de confiança.

**5. Como usar na prática.** O diagnóstico é um ponto de partida. Abra as evidências, observe os rounds reais e só então
transforme o padrão em hipótese de treino, ajuste tático ou revisão de VOD.
""")

    with st.expander("Limitações importantes", expanded=False):
        st.markdown(f"""
- São {len(M.METRICS)} métricas por recorte; algum resultado pode aparecer por acaso. Leia os diagnósticos como **indícios**.
- A referência mistura adversários de níveis diferentes e não corrige a força de cada adversário.
- Uma amostra pequena continua útil para descrição, mas não confirma padrão.
- As posições disponíveis são snapshots de eventos (kills, plant e defuse), não o trajeto completo dos jogadores.
- O dataset não traz efeitos de habilidades por round com consistência suficiente para análise causal de utilitários.
""")

    st.markdown(f"**Glossário das {len(M.METRICS)} métricas de equipe**")
    st.dataframe(
        pd.DataFrame({
            "Grupo": [m.group for m in M.METRICS],
            "Métrica": [m.label for m in M.METRICS],
            "O que mede": [m.what for m in M.METRICS],
            "Leitura favorável": ["quanto maior" if m.higher_better else "quanto menor" for m in M.METRICS],
        }),
        hide_index=True,
        width="stretch",
    )
