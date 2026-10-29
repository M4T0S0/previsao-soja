# Decisões

Aqui eu anoto o que decidi em cada etapa, os números que saíram e o motivo de cada escolha. Os números sempre vêm dos arquivos em `results/`.

## O que vale para todas as etapas

- **O que prevejo:** a variação do preço no mês seguinte, `ln P(t+1) − ln P(t)`, com o preço da soja do FMI em US$/t. Escolhi a variação porque o preço em si muda muito de nível ao longo dos anos, e prever o nível acaba premiando o modelo que só copia o último valor.
- **Nada do futuro:** a linha de cada mês só tem o que já era conhecido no fim daquele mês. A última linha fica sem alvo, porque é justamente o mês que quero prever.
- **Como testo:** treino com todos os meses até um ponto, prevejo o mês seguinte, acrescento esse mês ao treino e repito (janela expansiva). O teste vai de janeiro de 2015 a junho de 2026.
- **Como comparo:** olho o erro (RMSE) em relação ao passeio aleatório, o erro médio absoluto, quantas vezes acerto se o preço sobe ou desce, e uso o teste de Diebold-Mariano para ver se a diferença é real ou sorte.
- **Escala das features:** a padronização é calculada só com os meses de treino, para não vazar informação do teste.

## 01_preco

Baixei o preço mensal da soja do FMI (FRED `PSOYBUSDM`). A série vai de janeiro de 2000 a setembro de 2026, com 321 meses. Setembro de 2026 fica sem alvo, porque é o mês que quero prever.

A variação mensal tem média de +0,31% e desvio padrão de 5,77%. As maiores quedas foram em agosto de 2004 e outubro de 2008, as duas perto de −25%.

Antes do teste (2000 a 2014), a correlação de cada feature com o alvo foi:

| Feature | Correlação |
|---|---|
| `dlog_preco` | 0,354 |
| `tendencia_3m` | 0,195 |
| `dlog_preco_lag1` | 0,108 |

Isso mostra que o preço tem um pouco de "embalo": quando sobe num mês, tende a subir um pouco no seguinte. Por isso mantenho as três features.

No teste (janeiro de 2015 a junho de 2026, 138 meses), o RMSE do passeio aleatório é **0,0461**, cerca de 4,6% por mês. Esse é o número que os modelos precisam bater.

## 02_enso

Baixei o ONI da NOAA (321 meses, até setembro de 2026). Como cada valor é a média de um trimestre, coloquei ele no último mês do trimestre (DJF vai para fevereiro), que é quando ele já é conhecido. Em setembro de 2026 o ONI está em 2,16, um El Niño forte.

Antes do teste, a correlação do ONI de *k* meses antes com o alvo muda de sinal com o atraso:

| k (meses) | 0 | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|---|
| Correlação | −0,11 | −0,05 | 0,09 | 0,15 | 0,21 | 0,20 | 0,13 |

As features que montei tiveram estas correlações: `oni` −0,11, `oni_lag2` −0,05 e `oni_var3` −0,17.
