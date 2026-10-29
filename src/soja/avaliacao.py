"""Métricas de erro usadas para comparar os modelos."""
import numpy as np
import pandas as pd
from scipy import stats


def rmse(erro: pd.Series) -> float:
    return float(np.sqrt(np.mean(np.square(erro))))


def mae(erro: pd.Series) -> float:
    return float(np.mean(np.abs(erro)))


def acerto_direcao(previsao: pd.Series, alvo: pd.Series) -> float:
    """Fração dos meses em que o modelo acertou se o preço sobe ou desce."""
    return float(np.mean(np.sign(previsao) == np.sign(alvo)))


def diebold_mariano(erro_a: pd.Series, erro_b: pd.Series) -> float:
    """p-valor (bicaudal) de o erro quadrático de A ser diferente do de B, um passo à frente.

    Uso a correção de Harvey, Leybourne e Newbold para amostras pequenas.
    """
    d = np.square(np.asarray(erro_a)) - np.square(np.asarray(erro_b))
    n = len(d)
    estat = d.mean() / np.sqrt(d.var(ddof=0) / n)
    estat *= np.sqrt((n - 1) / n)  # correção HLN para h = 1
    return float(2 * stats.t.sf(abs(estat), df=n - 1))


def resumo(previsao: pd.Series, alvo: pd.Series, referencias: dict) -> dict:
    """RMSE, MAE, direção e comparação com cada referência ({nome: previsão})."""
    erro = alvo - previsao
    saida = {"rmse": rmse(erro), "mae": mae(erro), "direcao": acerto_direcao(previsao, alvo)}
    for nome, ref in referencias.items():
        erro_ref = alvo - ref
        saida[f"rmse_rel_{nome}"] = saida["rmse"] / rmse(erro_ref)
        saida[f"p_{nome}"] = diebold_mariano(erro, erro_ref)
    return saida
