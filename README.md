# Previsão do preço da soja

Este é o meu projeto da disciplina Oficina de Projetos em Ciência de Dados e IA, na UTFPR. Quero descobrir se dá para prever o preço internacional da soja do mês seguinte e, se der, colocar essa previsão numa aplicação web gratuita, feita em Streamlit.

- **Aluno:** Matheus Leineker Stanula
- **Orientador:** Dr. Luiz Fernando Puttow Southier

## O que eu estou prevendo

Uso o preço mensal da soja publicado pelo FMI, em dólares por tonelada. Em vez de prever o preço direto, eu prevejo quanto ele vai variar no mês seguinte, ou seja, `ln P(t+1) − ln P(t)`. Cada mês só pode usar o que já se sabia até o fim dele, para o modelo não "espiar" o futuro.

Para saber se o modelo presta, comparo com o jeito mais simples de prever: dizer que o preço do mês que vem vai ser igual ao de hoje (o passeio aleatório). Se o modelo não ganhar disso, ele não serve.

## Etapas

Fui dividindo o trabalho em etapas numeradas, cada uma com o seu notebook:

| Etapa | Notebook | O que faço nela | Situação |
|---|---|---|---|
| 01 | `01_preco` | Baixo o preço da soja, calculo o alvo e as features de preço | feita |
| 02 | `02_enso` | Trago o índice do El Niño (ONI) | feita |
| 03 | `03_wasde` | Leio os relatórios WASDE do USDA sobre oferta e demanda | feita |
| 04 | `04_extras` | Testo fontes novas que podem virar features | feita |
| 05 | `05_tabela` | Junto tudo numa tabela mensal | a fazer |
| 06 | `06_features` | Vejo, com um Ridge, quais grupos de features ajudam de verdade | a fazer |
| 07 | `07_modelos` | Comparo Ridge, Random Forest, LSTM e BiLSTM, ajustados com Optuna | a fazer |
| 08 | `08_modelo_final` | Treino o modelo escolhido e prevejo o próximo mês | a fazer |
| 09 | `09_tabelas_figuras` | Gero as tabelas e figuras do relatório | a fazer |

O que decidi em cada etapa, e por quê, está em [`docs/decisoes.md`](docs/decisoes.md). Expliquei a organização das pastas em [`docs/organizacao.md`](docs/organizacao.md).

## Como rodar

Rodo tudo no Kaggle:

1. Subo a pasta do repositório como Dataset.
2. Importo o notebook da etapa, que está em `notebooks/`, e rodo com a internet ligada.
3. Baixo o zip de `/kaggle/working/results/` e extraio em `results/`.

## De onde vêm os dados

| Fonte | O que pego dela |
|---|---|
| FMI, pelo FRED (`PSOYBUSDM`) | Preço mensal da soja em US$/t |
| NOAA CPC | Índice ONI do El Niño |
| USDA WASDE, pelo ESMIS | Oferta e demanda mundial de soja |

São todas públicas, e baixo direto, sem precisar de chave de API.

## Referência

Oliva et al. *The Use of LSTM Models to Estimate Soybean Pricing: A Regional Climate Data Evaluation From Brazil*. IEEE Access, v. 13, 2025. DOI 10.1109/ACCESS.2025.3577087.
