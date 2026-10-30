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

# paleta: neutros cinza + um acento verde (Tailwind gray / emerald)
VERDE = "#047857"
CINZA_900, CINZA_500, CINZA_300, CINZA_100 = "#111827", "#6b7280", "#d1d5db", "#f3f4f6"

st.set_page_config(page_title="Preço da soja", page_icon="🌱", layout="centered")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stCaption {{ font-family: 'Inter', sans-serif; }}
.block-container {{ padding-top: 3rem; max-width: 760px; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.marca {{ color: {VERDE}; font-weight: 600; font-size: .8125rem; letter-spacing: .06em; }}
.titulo {{ color: {CINZA_900}; font-size: 1.875rem; font-weight: 700; letter-spacing: -.02em; margin: .25rem 0 1.5rem; }}
.cartao {{ background: white; border: 1px solid {CINZA_100}; border-radius: .75rem; padding: 1.75rem 2rem;
           box-shadow: 0 1px 2px rgba(17,24,39,.04); }}
.rotulo {{ color: {CINZA_500}; font-size: .875rem; }}
.valor {{ color: {CINZA_900}; font-size: 3rem; font-weight: 700; letter-spacing: -.03em; line-height: 1.1;
          font-variant-numeric: tabular-nums; margin: .25rem 0 .5rem; }}
.valor small {{ font-size: 1.125rem; font-weight: 500; color: {CINZA_500}; letter-spacing: 0; }}
.variacao {{ display: inline-block; font-size: .875rem; font-weight: 500; padding: .125rem .625rem; border-radius: 999px; }}
.faixa {{ color: {CINZA_900}; font-size: 1rem; margin-top: 1rem; }}
.faixa b {{ font-variant-numeric: tabular-nums; }}
.linha {{ display: flex; gap: 1rem; margin: 1rem 0 2rem; }}
.mini {{ flex: 1; background: white; border: 1px solid {CINZA_100}; border-radius: .75rem; padding: 1rem 1.25rem; }}
.mini .num {{ color: {CINZA_900}; font-size: 1.25rem; font-weight: 600; font-variant-numeric: tabular-nums; }}
.aviso {{ color: {CINZA_500}; font-size: .8125rem; text-align: center; margin: 1.5rem 0 1rem; }}
.legenda {{ color: {CINZA_500}; font-size: .8125rem; }}
h3 {{ font-size: 1.125rem !important; font-weight: 600 !important; color: {CINZA_900}; }}
</style>
""", unsafe_allow_html=True)


def mes(periodo: pd.Period) -> str:
    return MESES[periodo.month - 1]


def usd(valor: float) -> str:
    return "US$ " + f"{valor:,.0f}".replace(",", ".")


def pct(valor: float) -> str:
    return f"{valor:.1%}".replace(".", ",")


@st.cache_data
def carregar():
    previsao = json.loads((RESULTS / "08_modelo_final" / "previsao.json").read_text())
    tabela = pd.read_csv(RESULTS / "05_tabela" / "tabela_mensal.csv", index_col="mes")
    tabela.index = pd.PeriodIndex(tabela.index, freq="M")
    teste = pd.read_csv(RESULTS / "07_modelos" / "previsoes.csv").query("modelo == 'ridge' and periodo == 'teste'").copy()
    teste["mes"] = pd.PeriodIndex(teste["mes"], freq="M")
    resumo = pd.read_csv(RESULTS / "07_modelos" / "resumo.csv").query("modelo == 'ridge' and periodo == 'teste'").iloc[0]
    return previsao, tabela, teste.set_index("mes"), resumo


@st.cache_data(ttl=3600)
def cotacao_hoje():
    """Último fechamento do contrato de Chicago (ZS=F) em US$/t, ou None se o Yahoo não responder."""
    try:
        import yfinance as yf
        fech = yf.download("ZS=F", period="5d", progress=False, auto_adjust=False)["Close"].dropna()
        fech = fech.iloc[:, 0] if isinstance(fech, pd.DataFrame) else fech
        return float(fech.iloc[-1]) / 100 * BUSHELS_POR_T, fech.index[-1].date()
    except Exception:
        return None


def estilo(fig, altura):
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color=CINZA_500, size=12), showlegend=False,
                      hoverlabel=dict(bgcolor="white", font_color=CINZA_900))
    fig.update_xaxes(showgrid=False, linecolor=CINZA_300, ticks="")
    fig.update_yaxes(gridcolor=CINZA_100, zeroline=False, ticksuffix="  ")
    return fig


previsao, tabela, teste, resumo = carregar()
mes_base, mes_prev = pd.Period(previsao["mes_base"], "M"), pd.Period(previsao["mes_previsto"], "M")
atual, prevista = previsao["preco_atual"], previsao["preco_previsto"]
a80, b80 = previsao["faixas"]["80%"]
var = prevista / atual - 1
# alta ou queda não é boa nem ruim para todos (quem compra x quem vende), então o selo fica neutro
cor_var, fundo_var = "#374151", CINZA_100

# 1. a resposta: o preço previsto, em destaque
st.markdown(f"""
<div class="marca">PREÇO INTERNACIONAL DA SOJA</div>
<div class="titulo">Quanto a soja deve custar em {mes(mes_prev)}?</div>
<div class="cartao">
  <div class="rotulo">Preço médio previsto para {mes(mes_prev)} de {mes_prev.year}</div>
  <div class="valor">{usd(prevista)} <small>por tonelada</small></div>
  <span class="variacao" style="color:{cor_var}; background:{fundo_var}">{'▲' if var >= 0 else '▼'} {pct(abs(var))} em relação a {mes(mes_base)}</span>
  <div class="faixa">Deve ficar entre <b>{usd(a80)}</b> e <b>{usd(b80)}</b></div>
</div>
""", unsafe_allow_html=True)

cotacao = cotacao_hoje()
hoje = usd(cotacao[0]) if cotacao else "indisponível"
quando = f"Chicago, {cotacao[1]:%d/%m}" if cotacao else "Chicago"
st.markdown(f"""
<div class="linha">
  <div class="mini"><div class="rotulo">Média de {mes(mes_base)}</div><div class="num">{usd(atual)}</div></div>
  <div class="mini"><div class="rotulo">Hoje ({quando})</div><div class="num">{hoje}</div></div>
</div>
""", unsafe_allow_html=True)

# 2. contexto: últimos 3 anos e a previsão
st.markdown("### Últimos 3 anos")
hist = tabela.loc[mes_base - 35:mes_base, "preco_usd_t"]
x0, x1 = mes_base.to_timestamp(), mes_prev.to_timestamp()
fig = go.Figure()
fig.add_trace(go.Scatter(x=[x0, x1, x1, x0], y=[atual, b80, a80, atual], mode="lines", fill="toself",
                         fillcolor="rgba(4,120,87,0.15)", line=dict(width=0), hoverinfo="skip"))
fig.add_trace(go.Scatter(x=hist.index.to_timestamp(), y=hist, mode="lines", line=dict(color=CINZA_900, width=2),
                         hovertemplate="%{x|%m/%Y}<br><b>US$ %{y:.0f}</b><extra></extra>"))
fig.add_trace(go.Scatter(x=[x0, x1], y=[atual, prevista], mode="lines+markers", line=dict(color=VERDE, width=2, dash="dot"),
                         marker=dict(size=[0, 9], color=VERDE), hovertemplate="previsão<br><b>US$ %{y:.0f}</b><extra></extra>"))
fig.add_annotation(x=x1, y=prevista, text=f"<b>{prevista:.0f}</b>", showarrow=False, xanchor="left", xshift=8,
                   font=dict(color=VERDE, size=13))
fig.update_xaxes(tickformat="%m/%Y")
st.markdown(f'<div class="legenda">US$ por tonelada · a faixa verde é onde o preço deve ficar</div>', unsafe_allow_html=True)
st.plotly_chart(estilo(fig, 320), width="stretch", config={"displayModeBar": False})

st.markdown('<div class="aviso">Esta previsão não é recomendação de investimento.</div>', unsafe_allow_html=True)

# 3. para quem quer saber mais
with st.expander("Como a previsão é feita"):
    st.markdown(f"""
Todo mês, o modelo olha para o preço recente da soja, como o mês terminou na bolsa de Chicago,
o fenômeno El Niño e as apostas dos grandes fundos, e estima a média do mês seguinte.

Testei o modelo nos últimos {len(teste) // 12} anos, sempre prevendo só com o que se sabia na época.
Em média, ele errou **{pct(np.expm1(resumo['mae']))}** do preço.
""")
    real = tabela.loc[teste.index, "preco_usd_t"] * np.exp(teste["alvo"])
    prev = tabela.loc[teste.index, "preco_usd_t"] * np.exp(teste["previsao"])
    x = (teste.index + 1).to_timestamp()
    comp = go.Figure([
        go.Scatter(x=x, y=real, line=dict(color=CINZA_900, width=1.5), hovertemplate="real: US$ %{y:.0f}<extra></extra>"),
        go.Scatter(x=x, y=prev, line=dict(color=VERDE, width=1.5), hovertemplate="previsto: US$ %{y:.0f}<extra></extra>"),
    ])
    comp.update_xaxes(tickformat="%Y")
    st.markdown(f'<div class="legenda"><span style="color:{CINZA_900}">●</span> preço real &nbsp;&nbsp; '
                f'<span style="color:{VERDE}">●</span> previsto</div>', unsafe_allow_html=True)
    st.plotly_chart(estilo(comp, 260), width="stretch", config={"displayModeBar": False})

st.caption("Projeto da disciplina Oficina de Projetos em Ciência de Dados e IA · UTFPR · "
           "Dados: FMI, NOAA, CFTC e Yahoo Finance")
