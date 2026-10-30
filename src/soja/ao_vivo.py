"""Previsão do próximo mês com dados baixados na hora, usada pelo app.

Monta as 13 features do modelo final só para os meses recentes e aplica os coeficientes
salvos na etapa 08. A conta é a mesma do pipeline (padronização + Ridge), feita à mão
para o app não depender da versão do scikit-learn.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import dados, features

PASTA_MODELO = Path(__file__).resolve().parents[2] / "results" / "08_modelo_final"


def carregar_modelo(pasta: Path = PASTA_MODELO) -> dict:
    coef = pd.read_csv(pasta / "coeficientes.csv").set_index("feature")
    cfg = json.loads((pasta / "config.json").read_text())
    return {"coef": coef, "intercepto": cfg["intercepto"], "faixas": cfg["faixas_erro_log"], "colunas": cfg["colunas"]}


def montar_tabela(preco: pd.Series, oni: pd.Series, cot: pd.DataFrame, diario: pd.Series) -> pd.DataFrame:
    """Mesmas features das etapas 01, 02 e 04, uma linha por mês do preço do FMI."""
    tabela = pd.concat([
        preco.rename("preco_usd_t"),
        features.features_preco(preco),
        features.features_sazonalidade(preco.index),
        features.features_enso(oni),
        features.features_fundos(cot),
        features.features_fim_do_mes(diario),
    ], axis=1)
    return tabela.loc[:preco.index[-1]]


def prever(tabela: pd.DataFrame, modelo: dict) -> dict:
    """Previsão da média do mês seguinte ao último mês da tabela com todas as features."""
    colunas = modelo["colunas"]
    completos = tabela[colunas].dropna()
    mes_base = completos.index[-1]
    coef = modelo["coef"].loc[colunas]
    x = completos.loc[mes_base].to_numpy(float)
    desvio = modelo["intercepto"] + float(np.sum(coef["coeficiente"] * (x - coef["media"]) / coef["desvio_padrao"]))
    variacao = float(tabela.at[mes_base, "fim_vs_media"]) + desvio
    preco_atual = float(tabela.at[mes_base, "preco_usd_t"])
    return {
        "mes_base": str(mes_base), "mes_previsto": str(mes_base + 1), "preco_atual": preco_atual,
        "variacao_log": variacao, "preco_previsto": float(preco_atual * np.exp(variacao)),
        "preco_ultimo_dia": float(preco_atual * np.exp(tabela.at[mes_base, "fim_vs_media"])),
        "faixas": {n: [float(preco_atual * np.exp(variacao + e)) for e in f] for n, f in modelo["faixas"].items()},
    }


def baixar_e_prever(modelo: dict | None = None) -> tuple[dict, pd.Series]:
    """Baixa só o necessário (preço e ONI completos, fundos e preço diário do último ano e meio) e prevê."""
    modelo = modelo or carregar_modelo()
    hoje = pd.Timestamp.today()
    preco = dados.baixar_preco()
    oni = dados.baixar_oni()
    cot = dados.baixar_cot(ate=hoje.year, desde=hoje.year - 1)
    diario = dados.baixar_soja_diaria(desde=f"{hoje.year - 1}-01-01")
    diario.index = pd.to_datetime(diario.index).tz_localize(None)
    tabela = montar_tabela(preco, oni, cot, diario)
    return prever(tabela, modelo), preco
