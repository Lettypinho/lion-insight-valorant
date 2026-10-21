"""
Diagnosticos explicaveis + rounds de evidencia.

Nada aqui e "caixa-preta": cada frase nasce de uma regra com
  metrica  +  diferenca para a referencia  +  tamanho da amostra  +  rounds que a sustentam.
So geramos frase quando o veredito de src.analytics.metrics e confiavel (acima/abaixo);
caso contrario o sistema diz que nao ha diferenca confiavel ou que faltam dados.
"""
import numpy as np
import pandas as pd

from src.analytics.metrics import BY_KEY as TEAM_KEYS
from src.analytics.players import BY_KEY as PLAYER_KEYS

BY_KEY = {**TEAM_KEYS, **PLAYER_KEYS}

# (frase se ponto_forte, frase se ponto_de_atencao)
TEXTS = {
    "fk_rate": ("Abre os rounds com frequência: faz o primeiro abate em {rate} dos rounds (referência {ref}).",
                "Raramente abre o round: faz o primeiro abate em {rate} dos rounds (referência {ref})."),
    "fk_conv": ("Converte bem o primeiro abate em vitória: {rate} dos rounds (referência {ref}).",
                "Desperdiça a vantagem do primeiro abate: vence {rate} desses rounds (referência {ref})."),
    "fd_recovery": ("Resiliente: ainda vence {rate} dos rounds mesmo sofrendo o primeiro abate (referência {ref}).",
                    "Tem dificuldade de se recuperar quando sofre o primeiro abate: vence {rate} desses rounds (referência {ref})."),
    "trade_rate": ("Troca bem: {rate} das mortes com aliado vivo são vingadas em até 5 s (referência {ref}).",
                   "Perde jogadores sem troca: só {rate} das mortes com aliado vivo são vingadas em até 5 s (referência {ref})."),
    "isolated_rate": ("Joga junto: só {rate} das mortes acontecem longe dos aliados (referência {ref}).",
                      "Morre isolado: {rate} das mortes acontecem longe dos aliados (referência {ref})."),
    "pistol_win": ("Forte nos rounds de pistola: vence {rate} (referência {ref}).",
                   "Fraco nos rounds de pistola: vence {rate} (referência {ref})."),
    "econ_adv_conv": ("Converte a vantagem econômica: vence {rate} dos rounds em que gasta bem mais (referência {ref}).",
                      "Não converte a vantagem econômica: vence só {rate} dos rounds em que gasta bem mais (referência {ref})."),
    "econ_disadv_win": ("Competitivo mesmo em desvantagem econômica: vence {rate} desses rounds (referência {ref}).",
                        "Cai muito quando gasta menos que o adversário: vence {rate} desses rounds (referência {ref})."),
    "plant_rate": ("Consegue plantar com frequência: {rate} dos rounds de ataque (referência {ref}).",
                   "Tem dificuldade de plantar: {rate} dos rounds de ataque (referência {ref})."),
    "post_plant_win": ("Protege bem o plant: vence {rate} dos rounds depois de plantar (referência {ref}).",
                       "Perde rounds depois de plantar: vence só {rate} desses rounds (referência {ref})."),
    "ability_kills": ("Mata bastante com utilitário: {rate} dos abates com habilidade ou ultimate (referência {ref}).",
                      "Mata quase só com arma: {rate} dos abates com habilidade ou ultimate (referência {ref})."),
    "ability_deaths": ("Sofre bastante com o utilitário adversário: {rate} das mortes por habilidade ou ultimate (referência {ref}).",
                       "Raramente morre para utilitário: {rate} das mortes por habilidade ou ultimate (referência {ref})."),
    "plant_uncovered": ("Planta com cobertura: o plantador é abatido sem troca logo após plantar em só {rate} dos plants (referência {ref}).",
                        "Planta sem cobertura: o plantador é abatido sem troca em até 5 s em {rate} dos plants (referência {ref})."),
    "plant_punish": ("Pune o plant: abate o plantador sem troca em até 5 s em {rate} dos plants adversários (referência {ref}).",
                     "Raramente pune o plant: abate o plantador sem troca em até 5 s em só {rate} dos plants adversários (referência {ref})."),
    "retake_win": ("Retoma bem os sites: vence {rate} dos rounds em que o spike foi plantado (referência {ref}).",
                   "Retake fraco: vence só {rate} dos rounds em que o spike foi plantado (referência {ref})."),
}

# metricas por jogador (src/analytics/players.py)
TEXTS.update({
    "p_open_part": ("Protagonista na abertura: participa do duelo de abertura em {rate} dos rounds (referência {ref}).",
                    "Joga longe da abertura: participa do duelo de abertura em {rate} dos rounds (referência {ref})."),
    "p_open_win": ("Vence o duelo de abertura: {rate} dos seus duelos de abertura (referência {ref}).",
                   "Perde o duelo de abertura: vence só {rate} dos seus duelos de abertura (referência {ref})."),
    "p_fk_conv": ("Quando abre, a equipe converte: {rate} dos rounds vencidos após o seu primeiro abate (referência {ref}).",
                  "O primeiro abate dele rende pouco: {rate} dos rounds vencidos depois dele (referência {ref})."),
    "p_survival": ("Sobrevive bastante: não é abatido em {rate} dos rounds (referência {ref}).",
                   "Morre muito: sobrevive só em {rate} dos rounds (referência {ref})."),
    "p_trade_rate": ("Morre perto da equipe: {rate} das mortes com aliado vivo são vingadas em até 5 s (referência {ref}).",
                     "Morre sem troca: só {rate} das mortes com aliado vivo são vingadas em até 5 s (referência {ref})."),
    "p_isolated": ("Joga junto: só {rate} das mortes acontecem longe dos aliados (referência {ref}).",
                   "Morre isolado: {rate} das mortes acontecem longe dos aliados (referência {ref})."),
    "p_ability_kills": ("Mata bastante com utilitário: {rate} dos abates com habilidade ou ultimate (referência {ref}).",
                        "Mata quase só com arma: {rate} dos abates com habilidade ou ultimate (referência {ref})."),
    "p_ability_deaths": ("Morre bastante para utilitário: {rate} das mortes por habilidade ou ultimate (referência {ref}).",
                         "Raramente morre para utilitário: {rate} das mortes por habilidade ou ultimate (referência {ref})."),
    "p_trade_kills": ("Faz a troca pela equipe: {rate} dos abates vingam um aliado (referência {ref}).",
                      "Raramente é quem faz a troca: {rate} dos abates vingam um aliado (referência {ref})."),
})

# Combinacoes que contam uma historia unica. a = 1a metrica do par, b = 2a.
# O texto traz os numeros reais (taxa e referencia de cada uma) para nao repetir o titulo.
COMBOS = {
    ("fk_conv", "fd_recovery"): {
        ("ponto_forte", "ponto_de_atencao"): ("Converte quando abre, mas não se recupera quando sofre",
            "Vence {a_rate} dos rounds em que faz o primeiro abate (referência {a_ref}), mas só {b_rate} dos rounds em que sofre a first death (referência {b_ref})."),
        ("ponto_de_atencao", "ponto_forte"): ("Resiliente, mas desperdiça a abertura",
            "Vence só {a_rate} dos rounds em que faz o primeiro abate (referência {a_ref}), mas {b_rate} dos rounds em que sofre a first death (referência {b_ref})."),
        ("ponto_forte", "ponto_forte"): ("Sólido nos dois cenários",
            "Vence {a_rate} dos rounds em que faz o primeiro abate (referência {a_ref}) e {b_rate} dos rounds em que sofre a first death (referência {b_ref})."),
        ("ponto_de_atencao", "ponto_de_atencao"): ("Rounds decididos cedo",
            "Vence só {a_rate} dos rounds em que faz o primeiro abate (referência {a_ref}) e só {b_rate} dos rounds em que sofre a first death (referência {b_ref})."),
    },
    ("isolated_rate", "trade_rate"): {
        ("ponto_de_atencao", "ponto_de_atencao"): ("Morre longe e sem troca",
            "{a_rate} das mortes acontecem longe dos aliados (referência {a_ref}) e só {b_rate} das mortes com aliado vivo são vingadas em até 5 s (referência {b_ref}): as mortes saem de graça."),
        ("ponto_forte", "ponto_forte"): ("Jogo coletivo forte",
            "Só {a_rate} das mortes acontecem longe dos aliados (referência {a_ref}) e {b_rate} das mortes com aliado vivo são vingadas em até 5 s (referência {b_ref})."),
    },
}


# texto de cada round de evidencia: (se x==n, senao). Nas metricas por morte: "<x> de <n> <texto>"
NOTES = {
    "fk_rate": ("Fez o primeiro abate", "Sofreu o primeiro abate"),
    "fk_conv": ("Fez o 1º abate e venceu", "Fez o 1º abate e perdeu"),
    "fd_recovery": ("Sofreu o 1º abate e venceu", "Sofreu o 1º abate e perdeu"),
    "trade_rate": ("mortes trocadas", ""),
    "isolated_rate": ("mortes isoladas", ""),
    "pistol_win": ("Venceu a pistola", "Perdeu a pistola"),
    "econ_adv_conv": ("Venceu com vantagem econômica", "Perdeu com vantagem econômica"),
    "econ_disadv_win": ("Venceu em desvantagem econômica", "Perdeu em desvantagem econômica"),
    "plant_rate": ("Plantou o spike", "Não plantou"),
    "post_plant_win": ("Plantou e venceu", "Plantou e perdeu"),
    "retake_win": ("Retake bem-sucedido", "Retake falhou"),
    "plant_uncovered": ("Plantador abatido em até 5 s, sem troca", "Plant com cobertura"),
    "ability_kills": ("abates com habilidade", ""),
    "ability_deaths": ("mortes por habilidade", ""),
    "p_ability_kills": ("abates com habilidade", ""),
    "p_ability_deaths": ("mortes por habilidade", ""),
    "plant_punish": ("Abateu o plantador em até 5 s, sem troca", "Plantador sobreviveu ou foi trocado"),
    "p_open_part": ("Participou do duelo de abertura", "Fora do duelo de abertura"),
    "p_open_win": ("Venceu o duelo de abertura", "Perdeu o duelo de abertura"),
    "p_fk_conv": ("Fez o 1º abate e o time venceu", "Fez o 1º abate e o time perdeu"),
    "p_survival": ("Sobreviveu", "Foi abatido"),
    "p_trade_rate": ("mortes trocadas", ""),
    "p_isolated": ("mortes isoladas", ""),
    "p_trade_kills": ("abates de troca", ""),
}


def _pct(v):
    return f"{v * 100:.0f}%"


def _fmt(row, text):
    return text.format(rate=_pct(row.rate), ref=_pct(row.ref_rate))


def _numbers(rows):
    return [dict(key=r.key, label=r.label, rate=r.rate, ref_rate=r.ref_rate, n=int(r.n), unit=r.unit,
                 ci_low=r.ci_low, ci_high=r.ci_high, n_matches=int(r.n_matches)) for r in rows]


def diagnose(res: pd.DataFrame) -> dict:
    """res = saida de src.analytics.metrics.team_metrics. Retorna insights ordenados + notas de transparencia."""
    reliable = res[res["quality"].isin(["ponto_forte", "ponto_de_atencao", "perfil_acima", "perfil_abaixo"])
                   ].set_index("key", drop=False)
    used, insights = set(), []

    for (a, b), table in COMBOS.items():
        if a in reliable.index and b in reliable.index and not (reliable.loc[a].neutral or reliable.loc[b].neutral):
            ra, rb = reliable.loc[a], reliable.loc[b]
            hit = table.get((ra.quality, rb.quality))
            if hit:
                used |= {a, b}
                text = hit[1].format(a_rate=_pct(ra.rate), a_ref=_pct(ra.ref_rate),
                                     b_rate=_pct(rb.rate), b_ref=_pct(rb.ref_rate))
                insights.append(dict(title=hit[0], text=text,
                                     quality="ponto_forte" if ra.quality == rb.quality == "ponto_forte"
                                     else "ponto_de_atencao" if ra.quality == rb.quality else "misto",
                                     keys=[a, b], strength=float(ra.gap + rb.gap),
                                     numbers=_numbers([ra, rb])))
    for key, r in reliable.iterrows():
        if key in used:
            continue
        good, bad = TEXTS[key]  # em metricas de perfil: (texto se acima, texto se abaixo)
        first = r.quality in ("ponto_forte", "perfil_acima")
        insights.append(dict(title=r.label, text=_fmt(r, good if first else bad),
                             quality="perfil" if r.neutral else r.quality, keys=[key], strength=float(r.gap),
                             numbers=_numbers([r])))
    insights.sort(key=lambda i: -i["strength"])

    notes = {
        "em_linha": list(res[res.verdict == "em_linha"]["label"]),
        "insuficiente": list(res[res.verdict == "insuficiente"]["label"]),
        "sem_dados": list(res[res.verdict == "sem_dados"]["label"]),
    }
    return dict(insights=insights, notes=notes)


def evidence(df: pd.DataFrame, team: str, key: str, quality: str = None, key_col: str = "team") -> pd.DataFrame:
    """Rounds do time que entram na metrica `key`.
    quality='ponto_de_atencao' -> so os rounds "ruins"; 'ponto_forte' -> so os "bons"; None -> todos.
    `df` deve ter os mesmos filtros usados no calculo das metricas."""
    m = BY_KEY[key]
    d = df[df[key_col] == team]
    x, n = m.x(d), m.n(d)
    keep = n > 0
    out = d.loc[keep, ["match_date", "competition", "map_name", "opponent", "round_label", "role",
                       "half", "won", "match_id", "round_num"]].copy()
    out["x"], out["n"] = x[keep], n[keep]
    good = (out["x"] == out["n"]) if m.higher_better else (out["x"] == 0)
    out["bom_para_o_time"] = good
    out["resultado"] = np.where(out["won"], "Venceu", "Perdeu")
    pos, neg = NOTES[key]
    if m.unit in ("mortes", "abates"):
        out["detalhe"] = out["x"].astype(str) + " de " + out["n"].astype(str) + " " + pos
    else:
        out["detalhe"] = np.where(out["x"] == out["n"], pos, neg)
    if quality == "ponto_de_atencao":
        out = out[~out["bom_para_o_time"]]
    elif quality == "ponto_forte":
        out = out[out["bom_para_o_time"]]
    return out.sort_values(["match_date", "match_id", "round_num"]).reset_index(drop=True)
