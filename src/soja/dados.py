"""Download das séries mensais usadas no projeto."""
import io
import time
import zipfile

import pandas as pd
import requests

URL_FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={codigo}"


def baixar_fred(codigo: str) -> pd.Series:
    """Baixa uma série mensal do FRED e devolve com índice mensal (período)."""
    df = pd.read_csv(URL_FRED.format(codigo=codigo), na_values=".")
    meses = pd.to_datetime(df.iloc[:, 0]).dt.to_period("M")
    return pd.Series(df.iloc[:, 1].values, index=meses, name=codigo).dropna()


def baixar_preco() -> pd.Series:
    """Preço mensal da soja do FMI (PSOYBUSDM), em US$/t."""
    return baixar_fred("PSOYBUSDM").rename("preco_usd_t")


URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
TRIMESTRES = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def baixar_oni() -> pd.Series:
    """Índice ONI da NOAA, um valor por mês.

    Cada valor é a média de um trimestre (DJF, JFM...). Coloco ele no último mês
    do trimestre (DJF vai para fevereiro), que é quando ele já pode ser conhecido.
    """
    df = pd.read_csv(URL_ONI, sep=r"\s+")
    mes_central = df["SEAS"].map({s: i + 1 for i, s in enumerate(TRIMESTRES)})
    meses = pd.PeriodIndex.from_fields(year=df["YR"], month=mes_central, freq="M") + 1
    return pd.Series(df["ANOM"].values, index=meses, name="oni")


# Commitments of Traders (CFTC), relatório "legacy" só de futuros. Soja de Chicago = código 005602.
URL_COT_HISTORICO = "https://www.cftc.gov/files/dea/history/deacot1986_2016.zip"
URL_COT_ANO = "https://www.cftc.gov/files/dea/history/deacot{ano}.zip"
CODIGO_SOJA_CBOT = "005602"


def _ler_zip_csv(url: str) -> pd.DataFrame:
    conteudo = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=180).content
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        return pd.read_csv(z.open(z.namelist()[0]), dtype=str, low_memory=False)


def baixar_cot(ate: int) -> pd.DataFrame:
    """Posições semanais da soja: data, contratos em aberto e compras/vendas dos não comerciais (fundos)."""
    urls = [URL_COT_HISTORICO] + [URL_COT_ANO.format(ano=a) for a in range(2017, ate + 1)]
    partes = []
    for url in urls:
        df = _ler_zip_csv(url)
        col = lambda trecho: next(c for c in df.columns if trecho.lower() in c.lower())
        codigo = df[col("CFTC Contract Market Code")].str.strip().str.zfill(6)
        df = df[codigo == CODIGO_SOJA_CBOT]
        partes.append(pd.DataFrame({
            "data": pd.to_datetime(df[col("YYYY-MM-DD")]),
            "contratos": pd.to_numeric(df[col("Open Interest (All)")]),
            "fundos_compra": pd.to_numeric(df[col("Noncommercial Positions-Long (All)")]),
            "fundos_venda": pd.to_numeric(df[col("Noncommercial Positions-Short (All)")]),
        }))
    return pd.concat(partes).drop_duplicates("data").sort_values("data").reset_index(drop=True)


# Comex Stat (governo federal): exportações mensais de soja em grão.
# O código NCM da soja em grão mudou em 2012: 12010090 até 2011 e 12019000 depois.
URL_COMEX = "https://api-comexstat.mdic.gov.br/general"
NCM_SOJA = ["12010090", "12019000"]


def _consulta_comex(ano: int) -> pd.DataFrame:
    corpo = {
        "flow": "export", "monthDetail": True,
        "period": {"from": f"{ano}-01", "to": f"{ano}-12"},
        "filters": [{"filter": "ncm", "values": NCM_SOJA}],
        "details": ["ncm"], "metrics": ["metricKG"],
    }
    for tentativa in range(5):
        resposta = requests.post(URL_COMEX, json=corpo, timeout=120)
        if resposta.status_code == 429:  # muitas consultas seguidas: espera e tenta de novo
            time.sleep(15)
            continue
        dados = resposta.json()
        if "data" not in dados:
            raise RuntimeError(f"Comex Stat respondeu {resposta.status_code} em {ano}: {dados}")
        lista = dados["data"]["list"] if isinstance(dados["data"], dict) else dados["data"]
        return pd.DataFrame(lista)
    raise RuntimeError(f"Comex Stat recusou as consultas de {ano} (limite de acessos)")


def baixar_exportacoes_br(desde: int, ate: int) -> pd.Series:
    """Toneladas de soja em grão exportadas pelo Brasil por mês."""
    partes = []
    for ano in range(desde, ate + 1):
        partes.append(_consulta_comex(ano))
        time.sleep(2)
    df = pd.concat(partes)
    col = lambda trecho: next(c for c in df.columns if trecho.lower() in c.lower())
    meses = pd.PeriodIndex.from_fields(year=df[col("year")].astype(int), month=df[col("monthnumber")].astype(int), freq="M")
    toneladas = pd.to_numeric(df[col("kg")]).values / 1000
    return pd.Series(toneladas, index=meses, name="exportacao_t").groupby(level=0).sum().sort_index()
