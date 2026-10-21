"""
data.py
-------
Generates a synthetic monthly U.S.-equity cross-sectional panel and the train /
validation / test splits following the AlphaPortfolio paper's empirical protocol.

The paper uses proprietary WRDS data (CRSP + Compustat); that data is unavailable in
this workspace and public endpoints are rate-limited. Instead we synthesize a monthly
panel of I stocks x T months that encodes the *documented* cross-sectional pricing
premia the model is designed to harvest (momentum, short-term reversal, size, value,
low-volatility, profitability), with calibrated signal strengths and a realistic
cross-asset sector/factor structure. This makes the full replication pipeline
executable end-to-end while the methodology (feature construction, model architecture,
objective, evaluation) follows the paper exactly.
"""

import numpy as np
import pandas as pd


def generate_panel(
    n_stocks: int = 300,
    start: str = "1990-01-01",
    end: str = "2020-12-01",
    seed: int = 7,
):
    """Return a monthly cross-sectional panel indexed by (date, id).

    Fields: id, date, ret, mom_12_1, mom_1, size, bm, vol, roe, acc, liq, sector
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, end=end, freq="MS")
    T = len(dates)
    ids = [f"STK{i:04d}" for i in range(n_stocks)]

    n_sectors = 8
    sector = rng.integers(0, n_sectors, size=n_stocks)
    # firm factor loadings on sector factors (sparse-ish: each firm loads mainly on its sector)
    load = rng.normal(0, 0.5, size=(n_stocks, n_sectors))
    load[np.arange(n_stocks), sector] += 1.0   # dominant own-sector loading

    ffactor = rng.normal(0, 0.015, size=(T, n_sectors))
    mkt = rng.normal(0.006, 0.04, size=T)
    idio = rng.normal(0, 0.08, size=(T, n_stocks))

    # fixed firm traits
    size_log = rng.normal(-1.0, 1.5, size=n_stocks)
    bm_firm = rng.lognormal(0.0, 0.6, size=n_stocks)
    roe_firm = rng.normal(0.10, 0.12, size=n_stocks)

    # characteristic signals
    mom_12_1 = np.zeros((T, n_stocks))
    mom_1 = np.zeros((T, n_stocks))
    vol = np.full((T, n_stocks), 0.02)
    liq = np.empty((T, n_stocks))
    acc = np.empty((T, n_stocks))

    # annualized cross-sectional premia (monthly = /12)
    PREM_MOM = 0.10
    PREM_REV = -0.06
    PREM_SIZE = -0.04
    PREM_VALUE = 0.04
    PREM_VOL = -0.04

    histor = []      # rolling realized returns for momentum
    ret = np.empty((T, n_stocks))
    for t in range(T):
        # current idiosyncratic-vol measure
        vt = 0.015 + 0.02 * rng.beta(2, 6, size=n_stocks)
        vol[t] = vt

        # momentum: mean of prior returns (built from history)
        if len(histor) >= 2:
            mom12 = np.mean(histor[-12:], axis=0)
            m1 = histor[-1]
        else:
            mom12 = rng.normal(0, 0.01, n_stocks)
            m1 = rng.normal(0, 0.01, n_stocks)
        mom_12_1[t] = mom12
        mom_1[t] = m1

        # expected (annualized) return driven by characteristics
        mu = (
            PREM_SIZE * (size_log + 1.0)
            + PREM_VALUE * np.log(bm_firm)
            - PREM_VOL * (vt - 0.025) * 200.0
            + PREM_MOM * mom12 * 40.0
            + PREM_REV * m1 * 40.0
            + 0.04 * (roe_firm - 0.10)
        )
        factor_ret = ffactor[t] @ load.T
        monthly = mu / 12.0 + mkt[t] + 0.10 * factor_ret + 0.9 * idio[t]
        monthly = monthly / 1.5   # scale to realistic magnitudes
        ret[t] = monthly
        histor.append(monthly)
        liq[t] = rng.gamma(2.0, 0.01, size=n_stocks).clip(1e-4)
        acc[t] = rng.normal(0.0, 0.03, size=n_stocks)

    rows = []
    for t in range(T):
        for j in range(n_stocks):
            rows.append(dict(
                id=ids[j], date=dates[t], ret=ret[t, j],
                mom_12_1=mom_12_1[t, j], mom_1=mom_1[t, j],
                size=size_log[j], bm=bm_firm[j], vol=vol[t, j],
                roe=roe_firm[j] + rng.normal(0, 0.02), acc=acc[t, j],
                liq=liq[t, j], sector=int(sector[j]),
            ))
    return pd.DataFrame(rows), dates


def add_listing_filter(df, min_months: int = 24):
    g = df.groupby("id")["date"].transform("count")
    return df[g >= min_months].reset_index(drop=True)


def splits(df, train_end="2004-12-01", val_end="2009-12-01"):
    train = df[df["date"] <= train_end]
    val = df[(df["date"] > train_end) & (df["date"] <= val_end)]
    test = df[df["date"] > val_end]
    return train, val, test
