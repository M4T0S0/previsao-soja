"""Cálculo do alvo e das features de cada grupo."""
import numpy as np
import pandas as pd


def alvo(preco: pd.Series) -> pd.Series:
    """Variação log do preço no mês seguinte: ln P(t+1) − ln P(t).

    Fica na linha de t. A última linha não tem alvo, porque é o mês a prever.
    """
    return np.log(preco).diff().shift(-1).rename("alvo")


def features_preco(preco: pd.Series) -> pd.DataFrame:
    """Features que só usam o próprio preço, conhecidas no fim do mês t."""
    log_p = np.log(preco)
    return pd.DataFrame({
        "dlog_preco": log_p.diff(),            # quanto o preço variou neste mês
        "dlog_preco_lag1": log_p.diff().shift(1),  # quanto variou no mês anterior
        "tendencia_3m": log_p.diff(3),         # quanto variou nos últimos 3 meses
    })


def features_enso(oni: pd.Series) -> pd.DataFrame:
    """Features do El Niño a partir do ONI."""
    return pd.DataFrame({
        "oni": oni,                    # intensidade do El Niño (+) ou La Niña (−)
        "oni_lag2": oni.shift(2),      # ONI de 2 meses antes
        "oni_lag8": oni.shift(8),      # ONI de 8 meses antes (efeito na safra chega depois)
        "oni_var3": oni.diff(3),       # quanto o ONI mudou em 3 meses
    })


ESTOQUES = ["estoque_uso_mundo", "estoque_uso_eua"]
REVISOES = ["revisao_brasil", "revisao_eua", "revisao_china_import"]


def features_wasde(tabelas: pd.DataFrame) -> pd.DataFrame:
    """Features de oferta, uma linha por mês, a partir das tabelas de soja do WASDE.

    Mês sem relatório: repito o último estoque/uso e uso revisão 0 (nada foi revisado).
    """
    from .wasde import resumo_do_relatorio

    resumo = pd.DataFrame({pd.Period(r, "M"): resumo_do_relatorio(t) for r, t in tabelas.groupby("relatorio")}).T
    resumo = resumo.sort_index()
    todos = pd.period_range(resumo.index.min(), resumo.index.max(), freq="M")
    saida = resumo.reindex(todos)[ESTOQUES + REVISOES].apply(pd.to_numeric)
    saida["sem_relatorio"] = ~todos.isin(resumo.index)
    saida[ESTOQUES] = saida[ESTOQUES].ffill()
    saida[REVISOES] = saida[REVISOES].fillna(0.0)
    return saida
