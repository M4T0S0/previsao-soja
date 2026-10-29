"""Modelos não lineares: Random Forest, LSTM e BiLSTM."""
import numpy as np
import torch
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from torch import nn


def random_forest(n_estimators=300, max_depth=None, min_samples_leaf=5, max_features=1.0, semente=42):
    return RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, min_samples_leaf=min_samples_leaf,
                                 max_features=max_features, random_state=semente, n_jobs=-1)


class _Recorrente(nn.Module):
    def __init__(self, n_features, unidades, camadas, dropout, bidirecional):
        super().__init__()
        self.lstm = nn.LSTM(n_features, unidades, num_layers=camadas, batch_first=True,
                            dropout=dropout if camadas > 1 else 0.0, bidirectional=bidirecional)
        self.saida = nn.Linear(unidades * (2 if bidirecional else 1), 1)

    def forward(self, x):
        sequencia, _ = self.lstm(x)
        return self.saida(sequencia[:, -1]).squeeze(-1)


class RedeRecorrente:
    """LSTM (ou BiLSTM) que recebe os últimos `janela` meses de features e prevê um número.

    Recebe X com formato (amostras, janela, features). A padronização das features e do alvo
    é ajustada só no treino.
    """

    def __init__(self, bidirecional=False, janela=6, unidades=16, camadas=1, dropout=0.0,
                 lr=1e-3, epocas=150, weight_decay=1e-4, semente=42):
        self.p = dict(bidirecional=bidirecional, janela=janela, unidades=unidades, camadas=camadas,
                      dropout=dropout, lr=lr, epocas=epocas, weight_decay=weight_decay, semente=semente)

    def fit(self, X, y):
        torch.manual_seed(self.p["semente"])
        n, j, f = X.shape
        self.escala_x = StandardScaler().fit(X.reshape(-1, f))
        self.media_y, self.desvio_y = float(np.mean(y)), float(np.std(y)) or 1.0
        xt = torch.tensor(self.escala_x.transform(X.reshape(-1, f)).reshape(n, j, f), dtype=torch.float32)
        yt = torch.tensor((np.asarray(y) - self.media_y) / self.desvio_y, dtype=torch.float32)
        self.rede = _Recorrente(f, self.p["unidades"], self.p["camadas"], self.p["dropout"], self.p["bidirecional"])
        otimizador = torch.optim.Adam(self.rede.parameters(), lr=self.p["lr"], weight_decay=self.p["weight_decay"])
        gerador = torch.Generator().manual_seed(self.p["semente"])
        self.rede.train()
        for _ in range(self.p["epocas"]):
            for lote in torch.randperm(n, generator=gerador).split(32):
                otimizador.zero_grad()
                perda = nn.functional.mse_loss(self.rede(xt[lote]), yt[lote])
                perda.backward()
                otimizador.step()
        return self

    def predict(self, X):
        n, j, f = X.shape
        xt = torch.tensor(self.escala_x.transform(X.reshape(-1, f)).reshape(n, j, f), dtype=torch.float32)
        self.rede.eval()
        with torch.no_grad():
            return self.rede(xt).numpy() * self.desvio_y + self.media_y
