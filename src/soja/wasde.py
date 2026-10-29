"""Relatórios WASDE do USDA: busca no ESMIS, leitura da tabela de soja e cache.

Todo mês, por volta do dia 10, o USDA publica o WASDE. O ESMIS guarda cada relatório
como foi publicado, então a linha do mês t só usa o relatório publicado em t.
De julho de 2010 em diante o relatório vem em XML; antes disso, só em texto.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
SITE = "https://esmis.nal.usda.gov"
LISTA = SITE + "/publication/world-agricultural-supply-and-demand-estimates?page={}"
TITULO = "World Soybean Supply and Use"
MESES = r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
COLUNAS_TXT = ["Beginning Stocks", "Production", "Imports", "Domestic Crush", "Domestic Total", "Exports", "Ending Stocks"]


def mes_do_arquivo(nome: str):
    """Mês do relatório pelo nome do arquivo (wasde0926, wasde0626v2, wasde-12-09-2015)."""
    m = re.match(r"wasde(\d{2})(\d{2})(v\d)?$", nome)
    if m:
        return pd.Period(f"20{m[2]}-{m[1]}", "M")
    m = re.match(r"wasde-(\d{2})-\d{2}-(\d{4})", nome)
    if m:
        return pd.Period(f"{m[2]}-{m[1]}", "M")
    return None


def mes_do_xml(conteudo: bytes):
    """De 2018 a 2021 o arquivo se chama só latest.xml, então o mês vem de dentro do XML."""
    m = re.search(rb'Report_Month="([A-Za-z]+) (\d{4})"', conteudo)
    return pd.Period(pd.to_datetime(m[1].decode() + " " + m[2].decode()), "M") if m else None


def listar_relatorios(desde: str = "2000-01") -> dict:
    """Percorre as páginas do ESMIS e devolve {url: (nome do arquivo, 'xml' ou 'txt')}."""
    links = {}
    for pagina in range(0, 80):
        html = requests.get(LISTA.format(pagina), headers=H, timeout=60).text
        achados = re.findall(r'href="((?:https://esmis\.nal\.usda\.gov)?/sites/default/release-files/[^"]+/([^"/]+)\.(xml|txt))"', html)
        for url, nome, tipo in achados:
            mes = mes_do_arquivo(nome)
            # texto só para os meses sem XML (março de 2006 só tem a versão "_revision")
            if tipo == "txt" and not (re.fullmatch(r"wasde-\d{2}-\d{2}-\d{4}(_revision)?", nome, flags=re.I)
                                      and mes < pd.Period("2010-08", "M")):
                continue
            if mes is None or mes >= pd.Period(desde, "M"):
                links[url if url.startswith("http") else SITE + url] = (nome, tipo)
        datas = re.findall(r'world-agricultural-supply-and-demand-estimates/(\d{4})-(\d{2})-\d{2}"', html)
        if datas and max(pd.Period(f"{a}-{m}", "M") for a, m in datas) < pd.Period(desde, "M"):
            break
    return links


def ler_tabela_soja_xml(conteudo: bytes) -> pd.DataFrame:
    """Linhas (ano, regiao, mes, item, valor) da tabela de soja do XML.

    Os nomes das tags mudam um pouco entre relatórios (region4, attribute4...),
    então procuro pelo começo do nome.
    """
    linhas = []
    for rep in ET.fromstring(conteudo).iter("Report"):
        if TITULO not in (rep.get("sub_report_title") or ""):
            continue

        def andar(el, ctx):
            ctx = dict(ctx)
            for k, v in el.attrib.items():
                v = " ".join(v.split())
                if k.startswith("region_header"):
                    ctx["ano"] = v
                elif k.startswith("region"):
                    ctx["regiao"] = v
                elif k.startswith("attribute"):
                    ctx["item"] = v
                elif "month" in k.lower() and el.tag != "Report":
                    ctx["mes"] = v
                elif k.startswith("cell_value"):
                    linhas.append({**ctx, "valor": v})
            for filho in el:
                andar(filho, ctx)

        andar(rep, {})
    return pd.DataFrame(linhas)


def ler_tabela_soja_txt(texto: str) -> pd.DataFrame:
    """A mesma tabela nos relatórios em texto (2000 a julho de 2010).

    Cada linha tem 'Região  mês : 7 números'. Quando a região está sozinha na linha,
    os números vêm nas linhas de baixo, uma por mês.
    """
    for parte in texto.split(TITULO)[1:]:
        linhas, ano, regiao = [], None, None
        for linha in parte.splitlines()[1:]:
            if re.match(r"\s*1/", linha):  # notas de rodapé = fim da tabela
                break
            if ":" not in linha:
                continue
            nome, resto = linha.split(":", 1)
            m = re.search(r"(\d{4}/\d{2})", resto)
            if m and not re.search(r"\d+\.\d+", resto):  # linha do ano-safra
                ano = m[1]
                continue
            mes = re.search(MESES, nome)
            if re.sub(MESES, "", nome).strip():
                regiao = re.sub(MESES, "", nome).strip()
            valores = re.findall(r"-?\d+\.\d+|NA", resto)
            if len(valores) == 7 and ano and regiao:
                for item, v in zip(COLUNAS_TXT, valores):
                    linhas.append({"ano": ano, "regiao": regiao, "mes": mes[1] if mes else None, "item": item, "valor": v})
        if linhas:
            return pd.DataFrame(linhas)
    return pd.DataFrame()


def baixar_tabelas(desde: str = "2000-01") -> pd.DataFrame:
    """Baixa todos os relatórios e junta a tabela de soja de cada um (coluna 'relatorio' = mês)."""
    relatorios = listar_relatorios(desde)
    print("Arquivos encontrados:", len(relatorios))
    partes, fonte = {}, {}
    for i, (url, (nome, tipo)) in enumerate(relatorios.items()):
        try:
            conteudo = requests.get(url, headers=H, timeout=180).content
            mes = mes_do_arquivo(nome) or mes_do_xml(conteudo)
            if mes is None or mes < pd.Period(desde, "M"):
                continue
            prioridade = (tipo == "xml", nome)  # XML antes do texto; se houver v2, fica a corrigida
            if mes in fonte and prioridade < fonte[mes]:
                continue
            tabela = ler_tabela_soja_xml(conteudo) if tipo == "xml" else ler_tabela_soja_txt(conteudo.decode("latin-1"))
            if tabela.empty:
                raise ValueError("tabela de soja não encontrada")
            partes[mes] = tabela.assign(relatorio=str(mes))
            fonte[mes] = prioridade
        except Exception as e:
            print("  problema em", nome, tipo, "→", type(e).__name__, str(e)[:80])
        if i % 25 == 0:
            print(f"  {i + 1}/{len(relatorios)}")
    return pd.concat(partes.values(), ignore_index=True)


def carregar_tabelas(cache: Path, desde: str = "2000-01") -> pd.DataFrame:
    """Usa o cache se ele existir; senão baixa tudo e grava o cache."""
    if cache.exists():
        tabelas = pd.read_csv(cache, dtype=str)
        print(f"Usando {cache.name}: {tabelas['relatorio'].nunique()} relatórios")
        return tabelas
    tabelas = baixar_tabelas(desde)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tabelas.to_csv(cache, index=False)
    return tabelas


def resumo_do_relatorio(t: pd.DataFrame) -> dict:
    """Números de um relatório, no ano-safra mais recente dele.

    Estoque/uso = estoque final ÷ consumo total. Revisão = ln(valor deste relatório ÷ valor
    do relatório anterior), que o próprio WASDE traz nas colunas de mês.
    """
    t = t.copy()
    t["ano_safra"] = t["ano"].str.extract(r"(\d{4}/\d{2})", expand=False)
    t["regiao"] = t["regiao"].str.replace(r"\s*\d/$", "", regex=True).str.strip()
    t["valor"] = pd.to_numeric(t["valor"], errors="coerce")
    ultimo = t[t["ano_safra"] == t["ano_safra"].max()]
    if "mes" not in ultimo or ultimo["mes"].isna().all():
        ultimo = ultimo.assign(mes="atual")
    meses = list(dict.fromkeys(ultimo["mes"].dropna()))  # na ordem do relatório: [anterior, atual]

    def valor(regiao, item, qual=-1):
        sel = ultimo[(ultimo["regiao"] == regiao) & ultimo["item"].str.startswith(item) & (ultimo["mes"] == meses[qual])]
        return sel["valor"].iloc[0] if len(sel) else np.nan

    def revisao(regiao, item):
        atual = valor(regiao, item)
        antes = valor(regiao, item, 0) if len(meses) > 1 else np.nan
        return np.log(atual / antes) if antes > 0 and atual > 0 else 0.0

    return {
        "ano_safra": ultimo["ano_safra"].iloc[0],
        "estoque_uso_mundo": valor("World", "Ending Stocks") / valor("World", "Domestic Total"),
        "estoque_uso_eua": valor("United States", "Ending Stocks") / valor("United States", "Domestic Total"),
        "revisao_brasil": revisao("Brazil", "Production"),
        "revisao_eua": revisao("United States", "Production"),
        "revisao_china_import": revisao("China", "Imports"),
    }
