"""Busca de hiperparâmetros com Optuna, usando só o período de validação."""
import numpy as np
import optuna
import pandas as pd

from . import config, experimento, modelos


def espaco_rf(trial):
    return dict(n_estimators=trial.suggest_int("n_estimators", 100, 500, step=100),
                max_depth=trial.suggest_int("max_depth", 2, 10),
                min_samples_leaf=trial.suggest_int("min_samples_leaf", 5, 40),
                max_features=trial.suggest_float("max_features", 0.3, 1.0))


def espaco_rede(trial):
    return dict(janela=trial.suggest_categorical("janela", [3, 6, 12]),
                unidades=trial.suggest_int("unidades", 8, 64, log=True),
                camadas=trial.suggest_int("camadas", 1, 2),
                dropout=trial.suggest_float("dropout", 0.0, 0.5),
                lr=trial.suggest_float("lr", 1e-4, 1e-2, log=True),
                epocas=trial.suggest_int("epocas", 30, 200, step=10),
                weight_decay=trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True))


def prever(tipo, params, tabela, colunas, alvo, inicio, fim, sementes):
    """Previsões de um modelo (média entre sementes) com retreino anual."""
    if tipo == "rf":
        return experimento.retreino_anual(tabela, colunas, alvo, lambda: modelos.random_forest(**params), inicio, fim)
    p = dict(params)
    janela = p.pop("janela")
    bidirecional = tipo == "bilstm"
    resultados = [experimento.retreino_anual(
        tabela, colunas, alvo,
        lambda s=s: modelos.RedeRecorrente(bidirecional=bidirecional, janela=janela, semente=s, **p),
        inicio, fim, janela=janela, sequencial=True) for s in sementes]
    return pd.concat(resultados, axis=1).mean(axis=1).rename("previsao")


def buscar(tipo, tabela, colunas, alvo, n_trials, semente=config.SEMENTE):
    """Escolhe os hiperparâmetros que minimizam o RMSE na validação (uma semente por tentativa)."""
    espaco = espaco_rf if tipo == "rf" else espaco_rede
    ini, fim = config.VALIDACAO_INICIO, config.VALIDACAO_FIM
    real = tabela.loc[ini:fim, alvo]

    def objetivo(trial):
        prev = prever(tipo, espaco(trial), tabela, colunas, alvo, ini, fim, [semente]).reindex(real.index)
        return float(np.sqrt(np.mean((real - prev) ** 2)))

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    estudo = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=semente))
    estudo.optimize(objetivo, n_trials=n_trials, show_progress_bar=False)
    return estudo
