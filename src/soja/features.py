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


def features_wasde_extras(tabelas: pd.DataFrame) -> pd.DataFrame:
    """Revisões extras do WASDE (etapa 04). Mês sem relatório = revisão 0."""
    from .wasde import revisoes_extras

    extras = pd.DataFrame({pd.Period(r, "M"): revisoes_extras(t) for r, t in tabelas.groupby("relatorio")}).T.sort_index()
    todos = pd.period_range(extras.index.min(), extras.index.max(), freq="M")
    return extras.reindex(todos).apply(pd.to_numeric).fillna(0.0)


def features_fundos(cot: pd.DataFrame) -> pd.DataFrame:
    """Posição líquida dos fundos (compras − vendas) ÷ contratos em aberto, no fim de cada mês.

    O relatório da terça sai na sexta, então só uso relatórios publicados até o último dia do mês.
    """
    publicado = cot["data"] + pd.Timedelta(days=3)
    liquido = (cot["fundos_compra"] - cot["fundos_venda"]) / cot["contratos"]
    mensal = liquido.groupby(publicado.dt.to_period("M")).last()
    mensal = mensal.reindex(pd.period_range(mensal.index.min(), mensal.index.max(), freq="M")).ffill()
    return pd.DataFrame({
        "fundos_liquido": mensal,              # quanto os fundos apostam na alta (+) ou na baixa (−)
        "fundos_var": mensal.diff(),           # quanto essa aposta mudou no mês
    })


def features_momentum(preco: pd.Series) -> pd.DataFrame:
    """Tendências mais longas e volatilidade do próprio preço."""
    log_p = np.log(preco)
    return pd.DataFrame({
        "tendencia_6m": log_p.diff(6),
        "tendencia_12m": log_p.diff(12),
        "volatilidade_6m": log_p.diff().rolling(6).std(),  # quanto o preço tem oscilado
    })


def features_exportacao(exportacao: pd.Series) -> pd.DataFrame:
    """Exportação de soja do Brasil contra o mesmo mês do ano anterior.

    O dado de um mês só sai no começo do mês seguinte, então a linha t usa o mês t−1.
    """
    var_12m = np.log(exportacao).diff(12)
    return pd.DataFrame({"exportacao_br_12m": var_12m.shift(1)})


def features_fim_do_mes(diario: pd.Series) -> pd.DataFrame:
    """Como o mês terminou em relação à média dele, a partir do preço diário de Chicago.

    O alvo é a média do mês seguinte, e o fim do mês já aponta para onde essa média vai começar.
    """
    log_p = np.log(diario)
    mes = log_p.index.to_period("M")
    ultimo = log_p.groupby(mes).last()
    media = log_p.groupby(mes).mean()
    cinco_dias_antes = log_p.groupby(mes).apply(lambda x: x.iloc[-6] if len(x) > 5 else np.nan)
    return pd.DataFrame({
        "fim_vs_media": ultimo - media,                 # último dia acima (+) ou abaixo (−) da média do mês
        "ultima_semana": ultimo - cinco_dias_antes,     # variação nos últimos 5 pregões
    })


def features_fundos_por_tipo(cot: pd.DataFrame) -> pd.DataFrame:
    """Posição líquida ÷ contratos em aberto de gestores de fundos e de produtores/indústrias, no fim do mês."""
    publicado = cot["data"] + pd.Timedelta(days=3)
    mes = publicado.dt.to_period("M")
    gestores = ((cot["gestores_compra"] - cot["gestores_venda"]) / cot["contratos"]).groupby(mes).last()
    produtores = ((cot["produtores_compra"] - cot["produtores_venda"]) / cot["contratos"]).groupby(mes).last()
    todos = pd.period_range(gestores.index.min(), gestores.index.max(), freq="M")
    gestores, produtores = gestores.reindex(todos).ffill(), produtores.reindex(todos).ffill()
    return pd.DataFrame({
        "gestores_liquido": gestores,
        "gestores_var": gestores.diff(),
        "produtores_var": produtores.diff(),
    })
