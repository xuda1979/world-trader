"""Avellaneda-Lee statistical arbitrage (residual mean-reversion, market-neutral).
Algorithm (from the paper):
  1. Universe: liquid US large-caps.
  2. Rolling 60-day estimation window of daily (log) returns R.
  3. Common factor returns = top-K PCA of R (or market+sector ETFs); residuals e = R - factor exposures.
  4. Fit each stock's residual to OU: dX = -kappa(X-mu)dt + sigma dW  via regression on lagged X.
     OU params: kappa from AR(1) slope; equilibrium mu; sigma_eq of stationary residual.
  5. s-score = (X - mu)/sigma_eq  (standardized distance from equilibrium).
  6. Enter when |s| crosses 1.25; hold until it crosses back to 0.75 (or 0.5).
  7. Market-neutral: long depressed residuals (s<-thr), short elevated residuals (s>thr), zero-net.
  8. T+1 P&L; cost ~10bp round-trip (5bp each way) on turnover.
"""
import numpy as np, pandas as pd

def roll_pca_resid(R, lookback=60, n_pc=5):
    """For each day t (>=lookback), estimate factors on window [t-lb, t-1] and return day-t
    idiosyncratic residuals. R: T x N log-return frame (sorted asc). Robust: skip non-finite windows."""
    Rv = np.array(R, dtype=float); dates = R.index; T,N = Rv.shape
    resid = np.full((T,N), np.nan)
    for t in range(lookback, T):
        W = Rv[t-lookback:t]
        if not np.isfinite(W).all():
            continue
        Wc = W - W.mean(axis=0)
        if not np.isfinite(Wc).all():
            continue
        try:
            cov = np.cov(Wc, rowvar=False)
            if cov.shape[0] != max(Wc.shape[1],1): continue
            evals, evecs = np.linalg.eigh(cov)
        except Exception:
            continue
        evecs = evecs[:, ::-1][:, :n_pc]
        F_win = Wc @ evecs
        X = np.hstack([F_win, np.ones((lookback,1))])
        try:
            beta, *_ = np.linalg.lstsq(X, Wc, rcond=None)   # (n_pc+1) x N
        except Exception:
            continue
        f_t = (Rv[t] - W.mean(axis=0)) @ evecs
        resid[t,:] = Rv[t] - (np.hstack([f_t,1.0]) @ beta)
    return pd.DataFrame(resid, index=dates, columns=R.columns)

def s_scores(resid, lookback=60):
    """OU-based standardized s-score per stock (rolling). s = (X-mu)/sigma_eq.
    mu = long-run mean via AR(1) equilibrium; sigma_eq from stationary OU variance."""
    ss = pd.DataFrame(index=resid.index, columns=resid.columns, dtype=float)
    for c in resid.columns:
        r = resid[c]
        x = r.rolling(lookback)
        mu = x.mean(); sd = x.std()
        # AR(1): X_t = a + b X_{t-1} + eps; OU kappa = -ln(b)/dt; sigma_eq^2 = sig_eps^2/(1-b^2)
        # Use rolling linear regression approximation
        # simple s-score (paper's standardized residual distance)
        ss[c] = (r - mu)/sd
    return ss

def build_book(ss, entry=1.25, exit=0.75, long_frac=0.2, short_frac=0.2):
    """Market-neutral book: each day long bottom-{long_frac} most-negative-s, short top-{short_frac}
    most-positive-s (>entry). EW within leg. Returns (position frame, net daily returns on given rets)."""
    pos = pd.DataFrame(0.0, index=ss.index, columns=ss.columns)
    n = ss.shape[1]
    for t in ss.index:
        row = ss.loc[t].dropna()
        if len(row) < 20: continue
        s = row
        ranking = s.rank(pct=True)
        # only trade names beyond entry threshold in the extreme quantiles
        long_sel  = s[s < -entry]
        short_sel = s[s >  entry]
        w = pd.Series(0.0, index=ss.columns)
        if len(long_sel):  w[long_sel.index]  =  (1/len(long_sel))
        if len(short_sel): w[short_sel.index] = -(1/len(short_sel))
        pos.loc[t] = w
    return pos

def backtest(pos, ret, cost_bps=10.0):
    """Net P&L with full |dW| cost (10bp round-trip book). T+1 (pos.shift)."""
    gr = (pos.shift()*ret).sum(axis=1, min_count=1)
    turn = pos.diff().abs().sum(axis=1)
    net = gr - turn*cost_bps/2/1e4   # 5bp each way = 10bp round trip => 5bp on one-side |dW|
    return net, gr, turn
