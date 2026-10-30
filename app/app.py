"""Previsão do preço médio da soja para o próximo mês."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RESULTS = Path(__file__).resolve().parents[1] / "results"
BUSHELS_POR_T = 1000 / 27.2155
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

st.set_page_config(page_title="Previsão da soja", page_icon="🌱", layout="centered")


def nome_mes(periodo: pd.Period) -> str:
    return f"{MESES[periodo.month - 1]} de {periodo.year}"


@st.cache_data
def carregar():
    previsao = json.loads((RESULTS / "08_modelo_final" / "previsao.json").read_text())
    tabela = pd.read_csv(RESULTS / "05_tabela" / "tabela_mensal.csv", index_col="mes")
    tabela.index = pd.PeriodIndex(tabela.index, freq="M")
    previsoes = pd.read_csv(RESULTS / "07_modelos" / "previsoes.csv")
    previsoes = previsoes.query("modelo == 'ridge' and periodo == 'teste'").copy()
    previsoes["mes"] = pd.PeriodIndex(previsoes["mes"], freq="M")
    resumo = pd.read_csv(RESULTS / "07_modelos" / "resumo.csv").query("modelo == 'ridge' and periodo == 'teste'").iloc[0]
    coeficientes = pd.read_csv(RESULTS / "08_modelo_final" / "coeficientes.csv")
    return previsao, tabela, previsoes.set_index("mes"), resumo, coeficientes


@st.cache_data(ttl=3600)
def cotacao_hoje():
    """Último fechamento do contrato de Chicago (ZS=F), em US$/t. Devolve None se o Yahoo não responder."""
    try:
        import yfinance as yf
        fech = yf.download("ZS=F", period="5d", progress=False, auto_adjust=False)["Close"].dropna()
        fech = fech.iloc[:, 0] if isinstance(fech, pd.DataFrame) else fech
        return float(fech.iloc[-1]) / 100 * BUSHELS_POR_T, fech.index[-1].date()
    except Exception:
        return None


previsao, tabela, previsoes, resumo, coeficientes = carregar()
mes_base = pd.Period(previsao["mes_base"], "M")
mes_previsto = pd.Period(previsao["mes_previsto"], "M")
preco_atual, preco_previsto = previsao["preco_atual"], previsao["preco_previsto"]
a80, b80 = previsao["faixas"]["80%"]
a95, b95 = previsao["faixas"]["95%"]

st.title("Previsão do preço da soja")
st.caption("Preço internacional da soja (média mensal do FMI, em US$ por tonelada).")

st.subheader(f"Média prevista para {nome_mes(mes_previsto)}")
c1, c2, c3 = st.columns(3)
c1.metric("Previsão", f"US$ {preco_previsto:,.0f}/t", f"{preco_previsto / preco_atual - 1:+.1%} sobre {MESES[mes_base.month - 1]}")
c2.metric("Faixa provável (80%)", f"{a80:,.0f} a {b80:,.0f}")
c3.metric(f"Média de {MESES[mes_base.month - 1]}", f"US$ {preco_atual:,.0f}/t")
st.caption(f"Em 95% dos casos, a média deve ficar entre US$ {a95:,.0f} e {b95:,.0f}/t.")

# histórico dos últimos 3 anos e a previsão com as faixas
hist = tabela.loc[mes_base - 35:mes_base, "preco_usd_t"]
x_hist = hist.index.to_timestamp()
x0, x1 = mes_base.to_timestamp(), mes_previsto.to_timestamp()
fig = go.Figure()
for (a, b), cor, nome in [((a95, b95), "rgba(214,39,40,0.12)", "faixa de 95%"), ((a80, b80), "rgba(214,39,40,0.28)", "faixa de 80%")]:
    fig.add_trace(go.Scatter(x=[x0, x1, x1, x0], y=[preco_atual, b, a, preco_atual], mode="lines", fill="toself",
                             fillcolor=cor, line=dict(width=0), name=nome, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=x_hist, y=hist, mode="lines", line=dict(color="black"), name="preço FMI",
                         hovertemplate="%{x|%m/%Y}: US$ %{y:.0f}/t<extra></extra>"))
fig.add_trace(go.Scatter(x=[x0, x1], y=[preco_atual, preco_previsto], mode="lines+markers",
                         line=dict(color="#d62728", dash="dot"), name="previsão",
                         hovertemplate="%{x|%m/%Y}: US$ %{y:.0f}/t<extra></extra>"))
fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="US$/t", xaxis_tickformat="%m/%Y",
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, width="stretch")

cotacao = cotacao_hoje()
if cotacao:
    valor, dia = cotacao
    st.info(f"**Cotação em Chicago ({dia:%d/%m/%Y}):** US$ {valor:,.0f}/t (contrato ZS=F convertido de centavos por bushel). "
            "É o preço de um dia; a previsão acima é a média do mês inteiro, publicada pelo FMI no mês seguinte.")
else:
    st.info("Não consegui buscar a cotação de hoje em Chicago agora.")

st.warning("**Ferramenta de planejamento, não recomendação de investimento.** O modelo erra 26% menos que repetir "
           "a média do mês atual, mas empata com o último preço do mês: ele não antecipa o mercado. "
           "Serve para estimar a média do próximo mês e quanto ela pode variar.")

with st.expander("Como funciona"):
    st.markdown(
        f"""
- **O que prevejo:** a média do próximo mês do preço internacional da soja (série do FMI).
- **Modelo:** regressão Ridge com 13 variáveis: preço recente, mês do ano, fechamento do mês em Chicago, El Niño (ONI) e posição dos fundos (CFTC).
- **Teste:** de 2015 a meados de 2026 ({int(resumo['meses'])} meses), sempre treinando só com o passado.
- **Resultado:** erro {1 - resumo['rmse_rel_passeio']:.0%} menor que repetir a média do mês atual, e acerto de direção de {resumo['direcao']:.0%}.
- **Faixas:** vêm dos erros reais do modelo nesse teste.
"""
    )
    real = tabela.loc[previsoes.index, "preco_usd_t"] * np.exp(previsoes["alvo"])
    prev = tabela.loc[previsoes.index, "preco_usd_t"] * np.exp(previsoes["previsao"])
    x = (previsoes.index + 1).to_timestamp()
    teste = go.Figure([go.Scatter(x=x, y=real, name="real", line=dict(color="black", width=1.5)),
                       go.Scatter(x=x, y=prev, name="previsão", line=dict(color="#d62728", width=1))])
    teste.update_layout(height=320, xaxis_tickformat="%Y", margin=dict(l=10, r=10, t=30, b=10), yaxis_title="US$/t",
                        title="Previsão contra o valor real no teste", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(teste, width="stretch")

    coef = coeficientes.sort_values("coeficiente")
    pesos = go.Figure(go.Bar(x=coef["coeficiente"], y=coef["feature"], orientation="h",
                             marker_color=np.where(coef["coeficiente"] > 0, "#2ca02c", "#d62728")))
    pesos.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), title="Peso de cada variável (padronizado)")
    st.plotly_chart(pesos, width="stretch")

st.caption("Projeto da disciplina Oficina de Projetos em Ciência de Dados e IA (UTFPR). "
           "Fontes: FMI/FRED, NOAA, CFTC, Yahoo Finance.")
