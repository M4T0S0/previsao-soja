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

As features que montei tiveram estas correlações: `oni` −0,11, `oni_lag2` −0,05, `oni_lag8` +0,21 e `oni_var3` −0,17.

Faz sentido o efeito aparecer com atraso: o El Niño mexe com a safra da América do Sul meses depois, e só aí o preço reage. Guardei o `oni_lag2` e o `oni_lag8` e vou deixar o Ridge decidir entre eles na etapa 06.

## 03_wasde

Li 318 relatórios do WASDE, de janeiro de 2000 a outubro de 2026. Faltam quatro meses: outubro de 2013, janeiro de 2019 e outubro de 2025, quando o governo dos EUA parou e o relatório não saiu, e janeiro de 2015, cujo arquivo não consegui ler. Nesses meses repito o último estoque/uso e uso revisão zero.

Antes do teste, as correlações ficaram assim:

| Feature | Com o alvo (mês seguinte) | Com a variação do mesmo mês |
|---|---|---|
| `estoque_uso_mundo` | −0,02 | −0,10 |
| `estoque_uso_eua` | 0,08 | −0,01 |
| `revisao_brasil` | −0,01 | −0,05 |
| `revisao_eua` | 0,06 | −0,18 |
| `revisao_china_import` | 0,03 | −0,01 |

Sozinhas, elas quase não se relacionam com o alvo. Faz sentido, porque o mercado reage ao relatório no próprio mês. A revisão dos EUA mostra isso bem: o preço cai no mês em que a produção é revisada para cima (−0,18) e devolve um pouco no mês seguinte (+0,06). Mesmo fracas, mantenho as cinco para testar no Ridge, porque juntas com o preço e o El Niño elas podem ajudar.

## 04_extras

Testei quatro grupos novos de features:

- **Mais revisões do WASDE:** produção da Argentina, exportações e esmagamento dos EUA e estoque final do mundo.
- **Fundos (CFTC):** posição líquida dos especuladores na soja de Chicago (compras − vendas ÷ contratos em aberto) e quanto ela mudou no mês. Só uso relatórios publicados até o fim do mês.
- **Momentum e volatilidade:** tendência de 6 e 12 meses e desvio padrão da variação nos últimos 6 meses.
- **Exportações do Brasil (Comex Stat):** soja em grão contra o mesmo mês do ano anterior, usando o mês anterior, porque o dado sai só no começo do mês seguinte. A API do Comex Stat limita o número de consultas, então baixo tudo numa consulta só.

Correlação com o alvo antes do teste:

| Feature | Correlação |
|---|---|
| `fundos_var` | 0,38 |
| `fundos_liquido` | 0,14 |
| `tendencia_6m` | 0,08 |
| `revisao_eua_export` | 0,06 |
| `exportacao_br_12m` | 0,06 |
| `revisao_eua_esmagamento` | 0,03 |
| `revisao_estoque_mundo` | −0,02 |
| `tendencia_12m` | −0,03 |
| `revisao_argentina` | −0,05 |
| `volatilidade_6m` | −0,19 |

A `fundos_var` virou a feature mais correlacionada de todas, acima até da variação do próprio preço (0,35). Desconfiei e conferi três coisas:

1. **Não é vazamento:** a posição vem do relatório de terça, publicado na sexta, e só entram relatórios publicados até o último dia do mês.
2. **Não é só o preço disfarçado:** descontando o efeito do `dlog_preco`, a correlação ainda fica em 0,25.
3. **Continua no teste:** de 2015 a 2026 a correlação é 0,25.

A minha explicação é que o preço do FMI é a média do mês. A posição dos fundos no fim do mês carrega o que aconteceu nas últimas semanas, e isso ainda vai pesar na média do mês seguinte.

A volatilidade também chamou atenção (−0,19): depois de meses agitados, o preço tende a cair no mês seguinte.

A `exportacao_br_12m` tem alguns valores extremos nos primeiros anos, quando um mês quase não teve exportação. Vou ficar de olho nisso no Ridge.

### Grupo novo: fim do mês e fundos por tipo

Como os fundos funcionaram por causa da média do mês, testei features que olham direto para o fim do mês:

| Feature | Antes do teste | No teste |
|---|---|---|
| `fim_vs_media` | 0,69 | 0,67 |
| `ultima_semana` | 0,52 | 0,47 |
| `gestores_var` | 0,35 | 0,22 |
| `produtores_var` | −0,39 | −0,23 |

O `fim_vs_media` (último dia contra a média do mês, com o preço diário de Chicago) virou de longe a feature mais forte. O motivo é simples: o preço do FMI é a média do mês do mesmo contrato de Chicago. Se o mês termina acima da média, o mês seguinte já começa acima, e a média dele tende a subir.

Isso muda a régua. Só de prever que a média do mês que vem vai ser igual ao preço do último dia, o erro no teste cai para **0,741** do passeio aleatório, sem modelo nenhum. Ou seja, boa parte do que parecia "previsão" é só o efeito da média. Por isso, a partir da etapa 06, comparo os modelos com duas referências: o passeio aleatório e o "último dia".

Os gestores e produtores só existem desde 2006 (o relatório desagregado da CFTC começa aí), e o `fim_vs_media` não tem 8 meses no começo da série.

## 05_tabela

Juntei tudo numa tabela só: 321 meses (janeiro de 2000 a setembro de 2026) e 29 features, mais o preço e o alvo. A última linha, setembro de 2026, não tem alvo, porque é dela que sai a previsão de outubro. Também incluí o mês do ano como seno e cosseno (`mes_sin`, `mes_cos`), para dezembro ficar perto de janeiro.

Meses sem valor:

- O começo da série, por causa das diferenças e médias móveis (até 12 meses na `tendencia_12m`).
- `fim_vs_media` e `ultima_semana` começam em setembro de 2000, quando começa o preço diário do Yahoo.
- `gestores_*` e `produtores_var` só existem a partir de junho de 2006.

Pares que trazem quase a mesma informação (correlação acima de 0,7 em módulo):

| Par | Correlação |
|---|---|
| `fundos_liquido` × `gestores_liquido` | 0,95 |
| `fundos_var` × `produtores_var` | −0,95 |
| `fundos_var` × `gestores_var` | 0,93 |
| `gestores_var` × `produtores_var` | −0,90 |
| `oni` × `oni_lag2` | 0,89 |
| `dlog_preco_lag1` × `tendencia_3m` | 0,77 |
| `fim_vs_media` × `ultima_semana` | 0,77 |
| `tendencia_3m` × `tendencia_6m` | 0,73 |

Os fundos do relatório antigo e os do desagregado medem praticamente a mesma coisa, e os antigos têm a vantagem de começar em 2000. Vou levar isso em conta na etapa 06.

A `exportacao_br_12m` tem valores extremos (−8,3 em fevereiro de 2013, +4,8 em fevereiro de 2014), em meses de entressafra em que a exportação quase zera e a razão contra o ano anterior explode.

## 06_features

Usei um Ridge (padronização + `RidgeCV`) com janela expansiva, retreinado todo mês. Para não escolher as features olhando o teste, separei um período de **validação (2010 a 2014)**: escolho os grupos ali e só depois confiro no teste (janeiro de 2015 a junho de 2026). A `exportacao_br_12m` foi limitada em ±1 por causa dos extremos da entressafra.

**Referências:**

| | Validação | Teste |
|---|---|---|
| Passeio (RMSE) | 0,0534 | 0,0461 |
| Último dia (RMSE) | 0,0389 | 0,0342 |
| Último dia ÷ passeio | 0,727 | 0,741 |

**Cada grupo somado à base** (base = preço + sazonalidade), RMSE no teste:

| Modelo | ÷ passeio | ÷ último dia |
|---|---|---|
| base | 0,969 | 1,307 |
| + enso | 0,981 | 1,323 |
| + wasde | 0,959 | 1,293 |
| + wasde_extras | 0,966 | 1,303 |
| + fundos | 0,965 | 1,302 |
| + momentum | 0,975 | 1,316 |
| + exportacao | 0,969 | 1,307 |
| + fim_do_mes | 0,747 | 1,007 |
| + fundos_por_tipo | 0,980 | 1,322 |

**Seleção para frente na validação:** base → + fim_do_mes → + enso → + fundos. Depois disso nenhum grupo reduziu o erro.

**Conjunto escolhido no teste** (13 features): RMSE 0,0359, acerto de direção 66,7%.

- Contra o passeio: **0,779** (p = 0,003). Ganha com folga e de forma significativa.
- Contra o último dia: **1,051** (p = 0,24). Fica um pouco pior, mas a diferença não é significativa.

Ou seja, quase todo o ganho sobre o passeio vem do efeito da média mensal, que o "último dia" já captura sozinho. Preço, El Niño, WASDE, fundos e exportações não acrescentam nada além do último preço. Também testei prever só o desvio em relação ao último dia (o Ridge "puxando" para o último dia em vez de para zero), e deu praticamente empate: entre 0,97 e 1,01 do último dia.

Isso combina com a ideia de que o mercado de soja é eficiente: o último preço já resume quase tudo o que se sabe.

## 07_modelos

Testei modelos não lineares com as 13 features da etapa 06. Todos preveem o **desvio em relação ao último dia** (alvo − `fim_vs_media`), e a previsão final é último dia + desvio. Assim, um modelo que não aprende nada fica igual ao último dia, e qualquer ganho é ganho de verdade.

O Optuna fez 30 tentativas por modelo, olhando só a validação (2010 a 2014), com retreino anual. No teste, as redes usam a média de 5 sementes. O Ridge sobre o desvio, retreinado todo mês, entrou como referência linear.

Hiperparâmetros escolhidos:

- **Random Forest:** 500 árvores, profundidade 2, mínimo de 14 meses por folha, 64% das features por divisão.
- **LSTM:** janela de 6 meses, 11 unidades, 1 camada, dropout 0,36, 80 épocas.
- **BiLSTM:** janela de 6 meses, 15 unidades, 1 camada, dropout 0,35, 40 épocas.

O Optuna preferiu modelos bem pequenos (árvores rasas, redes com poucas unidades), o que já indica que não há muito padrão para aprender.

Resultado no teste (janeiro de 2015 a junho de 2026, 138 meses):

| Modelo | RMSE | ÷ passeio | ÷ último dia | p contra o último dia | Acerto de direção |
|---|---|---|---|---|---|
| Ridge | 0,0342 | 0,743 | 1,002 | 0,96 | 68,8% |
| Random Forest | 0,0346 | 0,751 | 1,013 | 0,60 | 68,8% |
| LSTM | 0,0340 | 0,738 | 0,995 | 0,86 | 69,6% |
| BiLSTM | 0,0342 | 0,742 | 1,002 | 0,95 | 70,3% |

Nenhum modelo ganhou do último dia. O melhor foi a LSTM, com erro 0,5% menor, mas a diferença é ruído (p = 0,86). No gráfico de vantagem acumulada, as redes e o Ridge passam um período na frente (2021 a 2023) e devolvem tudo depois.

Conclusão: com estes dados, nem modelos lineares nem redes conseguem prever a soja melhor que o último preço do mês. Toda a vantagem sobre o passeio aleatório (cerca de 26%) vem do efeito da média mensal.

## 08_modelo_final

Escolhi o Ridge sobre o desvio em relação ao último dia. Ele empatou com as redes na etapa 07, é simples, treina em segundos e deixa ver o peso de cada feature, o que ajuda no app.

Treinei com todos os meses que têm as 13 features e o alvo (setembro de 2000 a agosto de 2026, 312 meses). O RidgeCV escolheu alpha = 356, um valor alto: os coeficientes ficam todos perto de zero (o maior, `mes_cos`, é 0,003 por desvio-padrão), então a previsão quase não se afasta do último dia.

A faixa de incerteza vem dos 138 erros do Ridge no teste da etapa 07 (alvo − previsão, em log):

- **80%:** −0,042 a +0,041
- **95%:** −0,067 a +0,060

Previsão para outubro de 2026, a partir de setembro (média de US$ 481,7/t):

- **Ridge:** US$ 472,2/t (−2,0%)
- **Último dia:** US$ 476,8/t
- **Faixa de 80%:** US$ 453 a 492/t
- **Faixa de 95%:** US$ 442 a 501/t

O `modelo.pkl` foi salvo com scikit-learn 1.6.1, então o app precisa usar a mesma versão para carregá-lo.

## 09_tabelas_figuras

Juntei as tabelas e figuras do relatório num notebook só, que lê os resultados das etapas 01 a 08 e não baixa nada. Cada tabela sai em `.csv` e `.tex`.

- **Tabelas:** features do modelo final; correlação de todas as features com o alvo (até 2014 e de 2015 em diante); grupos de features na validação; modelos no teste contra as duas réguas; hiperparâmetros; previsão do próximo mês.
- **Figuras:** preço com os períodos; efeito da média mensal (fim do mês contra o alvo); maiores correlações; grupos; modelos contra as duas réguas; previsões no teste; vantagem acumulada sobre o último dia; previsão de outubro de 2026; pesos do Ridge final.

## App

O app (`app/app.py`) mostra a previsão do próximo mês. Ao abrir, ele baixa os dados mais recentes (preço do FMI pelo FRED, ONI da NOAA, fundos da CFTC dos dois últimos anos e preço diário do Yahoo), monta as 13 features com as mesmas funções de `src/soja/` e aplica os coeficientes salvos na etapa 08. Faço a conta da padronização e do Ridge à mão (`src/soja/ao_vivo.py`), em vez de carregar o `modelo.pkl`, para o app não depender da versão do scikit-learn; conferi que dá exatamente o mesmo número (US$ 472,2/t para outubro de 2026).

O resultado fica em cache por 6 horas. Se alguma fonte estiver fora do ar, o app mostra a última previsão salva da etapa 08 e avisa isso no rodapé.
