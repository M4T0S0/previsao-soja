"""Métricas de erro usadas para comparar os modelos."""
import numpy as np
import pandas as pd


def rmse(erro: pd.Series) -> float:
    return float(np.sqrt(np.mean(np.square(erro))))
