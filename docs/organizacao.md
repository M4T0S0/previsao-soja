# Organização do repositório

Neste arquivo eu explico como organizei as pastas e por quê.

## Visão geral

```
previsao-soja/
├── README.md            apresentação do projeto e das etapas
├── requirements.txt     bibliotecas que uso
├── .gitignore           o que deixo fora do Git
├── docs/
│   ├── decisoes.md      o que decidi em cada etapa, com os números e o porquê
│   └── organizacao.md   este arquivo
├── src/soja/            código que todas as etapas usam
├── notebooks/           um notebook por etapa
├── results/             o que cada notebook produziu
├── app/                 aplicação em Streamlit
└── data/                downloads brutos e cache do WASDE (só no computador, fora do Git)
```

Quis separar três coisas: o código que reaproveito (`src/soja/`), a execução de cada experimento (`notebooks/`) e o que cada experimento gerou (`results/`). Assim os notebooks ficam curtos, porque a lógica mora nos módulos, e consigo conferir qualquer resultado sem rodar nada de novo.

## Etapas e nomes

Cada etapa tem um número e um nome curto. O notebook e a pasta de resultados usam o mesmo nome, então `notebooks/06_features.ipynb` grava em `results/06_features/`.

| Etapa | Notebook e pasta | O que faço nela |
|---|---|---|
| 01 | `01_preco` | Baixo o preço da soja (FMI), calculo o alvo e as features de preço |
| 02 | `02_enso` | Trago o índice ONI do El Niño e as features dele |
| 03 | `03_wasde` | Baixo e leio os relatórios WASDE do USDA e monto as features de oferta |
| 04 | `04_extras` | Testo fontes novas que podem virar features (outras colunas do WASDE, posição dos fundos, exportações...) |
| 05 | `05_tabela` | Junto as etapas 01 a 04 numa tabela mensal |
| 06 | `06_features` | Com um Ridge, comparo cada grupo de features com o passeio aleatório e escolho o conjunto final |
| 07 | `07_modelos` | Comparo Ridge, Random Forest, LSTM e BiLSTM (Optuna) usando as features escolhidas |
| 08 | `08_modelo_final` | Treino o modelo escolhido e gero a previsão do próximo mês |
| 09 | `09_tabelas_figuras` | Gero as tabelas e figuras do relatório da disciplina |

Não coloquei o período de teste (janeiro de 2015 a junho de 2026) nem o alvo no nome das pastas. Eles ficam no `config.json` de cada pasta de resultados, junto com os outros parâmetros da rodada.

Uma etapa depende das anteriores. A 05 lê o que saiu de 01 a 04, a 06 lê a tabela da 05, a 07 usa as features que escolhi na 06, a 08 usa o modelo que escolhi na 07, a 09 só lê resultados, e o `app/` lê a previsão da 08.

A etapa 04 vai crescendo aos poucos. Cada fonte nova ganha uma célula nela e vira um grupo no teste da 06. Uma feature só entra no conjunto final se melhorar o Ridge na 06.

## Código (`src/soja/`)

| Módulo | O que tem nele |
|---|---|
| `config.py` | Datas, período de teste, sementes, lista de features e caminhos |
| `dados.py` | Download do preço (FRED/FMI) e do ONI (NOAA) |
| `wasde.py` | Busca dos relatórios no ESMIS, leitura da tabela de soja em XML e TXT, e o cache |
| `features.py` | Cálculo do alvo e das features de cada grupo |
| `modelos.py` | Ridge, Random Forest, LSTM e BiLSTM |
| `avaliacao.py` | Erro relativo ao passeio, erro médio absoluto, acerto de direção e Diebold-Mariano |
| `experimento.py` | Janela expansiva com retreino mensal e comparação entre grupos |
| `otimizacao.py` | Busca de hiperparâmetros com Optuna, sem tocar no período de teste |

Todos os notebooks começam igual: acham a pasta do projeto, no computador ou no dataset do Kaggle, e importam `soja`. Como o dataset do Kaggle é só de leitura, as saídas vão para `/kaggle/working/results/` e depois eu copio para `results/`.

## Resultados (`results/`)

Repito os mesmos nomes de arquivo em todas as etapas, para ficar fácil de achar as coisas:

| Arquivo | O que tem nele |
|---|---|
| `config.json` | Parâmetros da rodada (período, features, sementes, hiperparâmetros) |
| `previsoes.csv` | Uma linha por modelo, grupo de features e mês de teste |
| `resumo.csv` | Erro, erro relativo ao passeio, erro médio absoluto, acerto de direção e p contra o passeio |
| `diebold_mariano.csv` | Comparações de Diebold-Mariano da etapa |
| `hiperparametros.json` | Melhor conjunto que o Optuna achou (etapa 07) |
| `trials.csv` | Todas as tentativas do Optuna (etapa 07) |
| `*.png` | Figura para conferir a etapa |

As etapas 01 a 04 gravam a série mensal da sua fonte (`preco.csv`, `oni.csv`, `wasde.csv`, `extras.csv`), e a 05 grava `tabela_mensal.csv`, que é a entrada de todos os modelos.

Na etapa 09 separo `tabelas/` (em CSV) e `figuras/` (em PNG). São esses os arquivos que uso no relatório.

Todos os números de `results/` vêm da rodada que fiz no Kaggle. Quando refaço uma etapa, troco a pasta inteira.

## O que deixo fora do Git

| Item | Por quê |
|---|---|
| `data/` | Downloads brutos do FRED, da NOAA e do ESMIS, que são refeitos na primeira execução |
| `data/wasde_tabelas.csv` | Cache das tabelas de soja de cada WASDE, porque baixar tudo de novo demora |
| `*.zip` | Pacotes que o Kaggle gera para download |
| `__pycache__/`, `.ipynb_checkpoints/` | Arquivos temporários do Python e do Jupyter |

## Como eu trabalho

1. Edito o código no computador, na pasta do repositório.
2. Subo a pasta inteira para o Kaggle como Dataset (New Version a cada mudança).
3. Importo o notebook da etapa no Kaggle e rodo com a internet ligada.
4. Baixo o zip de `/kaggle/working/results/` e extraio em `results/`.
5. Anoto os números e a decisão da etapa em `docs/decisoes.md`.
6. Mando para o GitHub com `git add -A`, `git commit` e `git push`.

Quando crio uma etapa nova, sigo o mesmo padrão: um notebook `NN_nome.ipynb`, uma pasta `results/NN_nome/` com os mesmos nomes de arquivo, uma linha no README e uma seção no `decisoes.md`.
