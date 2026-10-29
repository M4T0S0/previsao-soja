# Decisões

Aqui eu anoto o que decidi em cada etapa, os números que saíram e o motivo de cada escolha. Os números sempre vêm dos arquivos em `results/`.

## O que vale para todas as etapas

- **O que prevejo:** a variação do preço no mês seguinte, `ln P(t+1) − ln P(t)`, com o preço da soja do FMI em US$/t. Escolhi a variação porque o preço em si muda muito de nível ao longo dos anos, e prever o nível acaba premiando o modelo que só copia o último valor.
- **Nada do futuro:** a linha de cada mês só tem o que já era conhecido no fim daquele mês. A última linha fica sem alvo, porque é justamente o mês que quero prever.
- **Como testo:** treino com todos os meses até um ponto, prevejo o mês seguinte, acrescento esse mês ao treino e repito (janela expansiva). O teste vai de janeiro de 2015 a junho de 2026.
- **Como comparo:** olho o erro (RMSE) em relação ao passeio aleatório, o erro médio absoluto, quantas vezes acerto se o preço sobe ou desce, e uso o teste de Diebold-Mariano para ver se a diferença é real ou sorte.
- **Escala das features:** a padronização é calculada só com os meses de treino, para não vazar informação do teste.

## 01_preco

A fazer.
