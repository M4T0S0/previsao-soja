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
