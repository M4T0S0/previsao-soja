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
