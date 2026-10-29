"""Datas, sementes e caminhos usados por todas as etapas."""
from pathlib import Path

# Período da tabela mensal
INICIO = "2000-01"

# Período de teste (janela expansiva, retreino todo mês)
TESTE_INICIO = "2015-01"
TESTE_FIM = "2026-06"

# Período usado para escolher as features, antes do teste
VALIDACAO_INICIO = "2010-01"
VALIDACAO_FIM = "2014-12"

# Grupos de features (colunas da tabela mensal da etapa 05)
GRUPOS = {
    "preco": ["dlog_preco", "dlog_preco_lag1", "tendencia_3m"],
    "sazonalidade": ["mes_sin", "mes_cos"],
    "enso": ["oni", "oni_lag2", "oni_lag8", "oni_var3"],
    "wasde": ["estoque_uso_mundo", "estoque_uso_eua", "revisao_brasil", "revisao_eua", "revisao_china_import"],
    "wasde_extras": ["revisao_argentina", "revisao_eua_export", "revisao_eua_esmagamento", "revisao_estoque_mundo"],
    "fundos": ["fundos_liquido", "fundos_var"],
    "momentum": ["tendencia_6m", "tendencia_12m", "volatilidade_6m"],
    "exportacao": ["exportacao_br_12m"],
    "fim_do_mes": ["fim_vs_media", "ultima_semana"],
    "fundos_por_tipo": ["gestores_liquido", "gestores_var", "produtores_var"],
}
BASE = ["preco", "sazonalidade"]

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


def salvar_config(pasta: Path, **parametros) -> None:
    """Grava config.json com os parâmetros da rodada."""
    import json
    base = {"inicio": INICIO, "teste_inicio": TESTE_INICIO, "teste_fim": TESTE_FIM, "semente": SEMENTE}
    base.update(parametros)
    (pasta / "config.json").write_text(json.dumps(base, indent=2, ensure_ascii=False))


def ler_resultado(etapa: str, arquivo: str) -> Path:
    """Acha um arquivo de uma etapa anterior: primeiro na saída desta rodada, depois no repositório."""
    for base in (RESULTS, RAIZ / "results"):
        caminho = base / etapa / arquivo
        if caminho.exists():
            return caminho
    raise FileNotFoundError(f"Não achei {etapa}/{arquivo}. Rode a etapa {etapa} antes.")
