"""
model.py
--------
PyTorch implementation of the AlphaPortfolio panel Transformer with
  - SREM (sequence/relation-extraction module): temporal self-attention over the
    K+1 lagged feature vectors (self-attention across the time/lookback dimension).
  - RREM (relation-extraction module): cross-asset attention across the cross-section
    at a given date, producing the date-specific relation matrix Omega_t.
  - Score MLP -> asset score s_{i,t}.
  - Long-Short Portfolio generator LSP (paper Eq. 11): softmax-normed long basket of
    the top G assets and short basket of the bottom G assets.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class SREM(nn.Module):
    """Temporal (sequence) self-attention module over the lagged lookback window."""

    def __init__(self, in_dim, d_model=32, n_heads=4, dropout=0.1):
        super().__init__()
        self.in_proj = nn.Linear(in_dim, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout,
                                          batch_first=True)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 2 * d_model), nn.ReLU(), nn.Linear(2 * d_model, d_model))
        self.norm3 = nn.LayerNorm(d_model)

    def forward(self, x):
        # x: (B, L, F) - L = K+1 lagged positions, F features
        h = self.in_proj(x)
        a, _ = self.attn(h, h, h)
        h = self.norm1(h + a)
        h = self.norm3(h + self.ff(self.norm2(h)))
        return h  # (B, L, d_model)


class ScoreNet(nn.Module):
    """Map the SREM+RREM pooled representation to a per-asset score."""

    def __init__(self, in_dim, hid=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hid), nn.ReLU(),
            nn.Linear(hid, hid), nn.ReLU(),
            nn.Linear(hid, 1),
        )

    def forward(self, h):
        return self.net(h).squeeze(-1)


class AlphaPortfolio(nn.Module):
    """Full AlphaPortfolio: SREM -> RREM -> scores -> (external LSP).

    Args:
        n_features: number of input characteristics F
        lookback: K+1 (lagged months incl. current)
        pool: pooling over the temporal SREM output ('last' or 'mean')
    """

    def __init__(self, n_features, lookback=12, d_model=32, n_heads=4,
                 hid=64, pool="mean", use_rrem=True):
        super().__init__()
        self.srem = SREM(n_features, d_model=d_model, n_heads=n_heads)
        self.pool = pool
        self.use_rrem = use_rrem
        self.d_model = d_model
        # RREM: lightweight per-asset projection for cross-asset attention keys/values
        if use_rrem:
            self.rrem_proj = nn.Linear(d_model, d_model)
        self.score = ScoreNet(d_model, hid=hid)

    def forward_scores(self, seqs):
        """seqs: (B, L, F) one batch of asset-month sequences.
        Returns scores (B,) and representations."""
        h = self.srem(seqs)                     # (B, L, d)
        hpool = h.mean(dim=1) if self.pool == "mean" else h[:, -1]
        return h, hpool

    def forward(self, date_tensor):
        """RREM-aware forward over a full date's cross-section.

        date_tensor: (I, L, F) for the I assets present at a date.
        Returns scores s (I,).
        """
        I, L, Fdim = date_tensor.shape
        if not self.use_rrem:
            _, hpool = self.forward_scores(date_tensor)
            s = self.score(hpool)
            return s

        h, hpool = self.forward_scores(date_tensor)   # hpool (I, d)
        # RREM: cross-asset attention - each asset attends to all others
        Q = self.rrem_proj(hpool.unsqueeze(1))        # (I,1,d)
        K = self.rrem_proj(hpool.unsqueeze(0))        # (I,I,d)
        V = hpool.unsqueeze(0).expand(I, I, -1)       # (I,I,d)
        attn = (Q @ K.transpose(1, 2)) / (self.d_model ** 0.5)  # (I,I,I)->(I,1,I)
        attn = attn.squeeze(1)                        # (I,I)
        attn = F.softmax(attn, dim=1)                 # per-asset attention over peers
        context = (attn.unsqueeze(-1) * V).sum(dim=1)  # (I,d)
        combined = hpool + context                     # relation-enhanced rep
        s = self.score(combined)
        return s


# ---------------------------------------------------------------------------
# Long-Short Portfolio generator (paper Eq. 11)
# ---------------------------------------------------------------------------

def long_short_weights(scores, gross=1.0, G=None):
    """Compute normalized long-short weights from asset scores.

    scores: (I,) of per-asset scores (higher = more desirable long)
    G: number of long assets (and of short assets). Defaults to top/bottom 10%.
    Follows Eq. 11 of the paper (softmax-weighted baskets, zero otherwise).
    Returns weights (I,), sum(long)=+gross/2-ish, sum(short)=-gross/2.
    """
    scores = np.asarray(scores, dtype=np.float64)
    I = len(scores)
    if G is None:
        G = max(1, int(round(0.10 * I)))
    elif 0.0 < G < 1.0:
        G = max(1, int(round(G * I)))   # G given as a fraction of universe
    G = int(G)
    order = np.argsort(-scores, kind="stable")   # descending
    long_idx = order[:G]
    short_idx = order[-G:]

    w = np.zeros(I)
    es = np.exp(scores - scores.max())
    # long basket: softmax over the G selected longs
    lw = es[long_idx] / (es[long_idx].sum() + 1e-12)
    w[long_idx] = lw
    # short basket: softmax over selected shorts (negative)
    sw = es[short_idx] / (es[short_idx].sum() + 1e-12)
    w[short_idx] = -sw
    # scale so gross exposure = 1 (0.5 long / -0.5 short)
    w = w / (np.abs(w).sum() + 1e-12) * gross
    return w


def portfolio_return(weights, rets):
    """Weights (I,), rets (I,) -> scalar portfolio return."""
    w = np.asarray(weights, dtype=np.float64)
    r = np.asarray(rets, dtype=np.float64)
    return float(np.dot(w, r))


def differentiable_sharpe(weights_list, rets_list, rf=0.0, periods_per_year=12):
    """Annualized Sharpe of a sequence of portfolio returns.

    weights_list: list of arrays; rets_list: corresponding month returns.
    Returns scalar and a tensor (for autograd use torch tensors).
    """
    r = torch.stack([torch.as_tensor(pr, dtype=torch.float32) for pr in rets_list])
    excess = r - rf / periods_per_year
    mu = excess.mean()
    sd = excess.std(unbiased=False) + 1e-8
    sharpe = (mu / sd) * np.sqrt(periods_per_year)
    return sharpe
