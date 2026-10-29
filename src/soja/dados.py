"""Download das séries mensais usadas no projeto."""
import pandas as pd

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
