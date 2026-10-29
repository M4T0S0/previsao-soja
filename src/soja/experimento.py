"""Janela expansiva: a cada mês treino com todo o passado e prevejo o mês seguinte."""
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ALPHAS = np.logspace(-2, 4, 30)


def ridge():
    """Padronização + Ridge com alpha escolhido por validação cruzada só no treino."""
    return make_pipeline(StandardScaler(), RidgeCV(alphas=ALPHAS))


def janela_expansiva(tabela: pd.DataFrame, colunas: list, inicio: str, fim: str, modelo=ridge) -> pd.Series:
    """Previsão do alvo para cada mês entre inicio e fim.

    Para prever o mês t, o modelo só vê as linhas anteriores a t que têm todas as colunas e o alvo.
    O alvo da linha t−1 é a variação de t−1 para t, que já é conhecida no fim do mês t.
    """
    dados = tabela[colunas + ["alvo"]]
    previsoes = {}
    for mes in tabela.loc[inicio:fim].index:
        treino = dados.loc[:mes].iloc[:-1].dropna()
        linha = dados.loc[[mes], colunas]
        if linha.isna().any(axis=None) or len(treino) < 24:
            continue
        previsoes[mes] = modelo().fit(treino[colunas], treino["alvo"]).predict(linha)[0]
    return pd.Series(previsoes, name="previsao")


def selecao_para_frente(tabela: pd.DataFrame, base: list, grupos: dict, inicio: str, fim: str):
    """Adiciona, um de cada vez, o grupo que mais reduz o RMSE no período dado, até nenhum ajudar.

    Devolve a lista de grupos escolhidos e o histórico (grupo adicionado, RMSE).
    """
    alvo = tabela.loc[inicio:fim, "alvo"]
    erro = lambda cols: float(np.sqrt(np.mean((alvo - janela_expansiva(tabela, cols, inicio, fim).reindex(alvo.index)) ** 2)))
    atuais, escolhidos = list(base), []
    historico = [("base", erro(atuais))]
    restantes = dict(grupos)
    while restantes:
        testes = {nome: erro(atuais + cols) for nome, cols in restantes.items()}
        melhor = min(testes, key=testes.get)
        if testes[melhor] >= historico[-1][1]:
            break
        atuais += restantes.pop(melhor)
        escolhidos.append(melhor)
        historico.append((melhor, testes[melhor]))
    return escolhidos, historico
