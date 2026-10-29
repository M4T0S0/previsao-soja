"""Datas, sementes e caminhos usados por todas as etapas."""
from pathlib import Path

# Período da tabela mensal
INICIO = "2000-01"

# Período de teste (janela expansiva, retreino todo mês)
TESTE_INICIO = "2015-01"
TESTE_FIM = "2026-06"

SEMENTE = 42

# Pasta do projeto: o repositório no computador ou o dataset no Kaggle
RAIZ = Path(__file__).resolve().parents[2]
NO_KAGGLE = Path("/kaggle/working").exists()

# No Kaggle o dataset é só de leitura, então dados e resultados vão para /kaggle/working
SAIDA = Path("/kaggle/working") if NO_KAGGLE else RAIZ
DATA = SAIDA / "data"
RESULTS = SAIDA / "results"


def pasta_resultados(etapa: str) -> Path:
    """Cria e devolve results/<etapa>/, por exemplo pasta_resultados("01_preco")."""
    pasta = RESULTS / etapa
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta
