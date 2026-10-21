#!/usr/bin/env python3
"""HUNT_ENSO_AG — ENSO/NAO climate-index tilts on the ag-ETF complex.

Pre-registered configs per ../CHARTER.md (sealed commit 47700c3e BEFORE any
result). The charter's per-family enumeration governs: E1 6 + E2 2 + E3 4 +
E4 2 = 14 configs (the charter's 'Total 16' line is an arithmetic slip; NO
post-hoc additions). MEIv2 is sha-pinned as a frozen input per charter but
consumes no config (documented in FINDINGS).

Costs: 6.4bps one-side on FULL |dW|; borrow 0.5%/yr on short notional.
Gates per coord/GATES_CONTRACT.md.

Publication conventions (conservative, fail-closed):
  ONI  label month M (window M-1..M+1, center-labeled) knowable >= 12th of M+2
  NAO  month M knowable >= 12th of M+1
As-of joined to ETF daily calendars; trade t+1 (weight at t earns return t+1).

Gate e (signal-scramble) implemented per CONTRACT text: permute the monthly
signal-state sequence (200x, rng seed 17), recompute the full cost +
vol-target pipeline, p = frac(|SR_scram| >= |SR_real|); pass iff p < 0.05.
(The prior WX harness shuffled net returns, which is SR-permutation-invariant
and therefore degenerate; contract text requires scrambling the SIGNAL.)
"""
import hashlib
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 0.00064
BORROW = 0.005
CHAMPION = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

INPUT_SHA = {
    "oni": "a458c1cc929c36ab",
    "meiv2": "ce8c21bf3c4dc2ee",   # pinned per charter; unused by configs
    "nao": "3e723c3c42ac609f",
    "DBA": "7a12c1e0d6f11f65",
    "CORN": "a579ceacc2dc1d21",
    "WEAT": "33c6813fc1c5db93",
    "SOYB": "b53ab1388a569b6b",
}


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def load_index(name):
    p = f"{ROOT}/tools/quant/data/noaa_climate/{name}.csv"
    assert _sha(p) == INPUT_SHA[name], f"vintage drift {name}"
    return (pd.read_csv(p, parse_dates=["date"])
            .set_index("date")["value"].astype(float).sort_index())


def load_etf(sym):
    p = f"{ROOT}/tools/quant/data/more_etf/{sym}.csv"
    assert _sha(p) == INPUT_SHA[sym], f"vintage drift {sym}"
    return (pd.read_csv(p, parse_dates=["date"])
            .set_index("date")["close"].astype(float).sort_index())


def month_signal_date(m_date, lag):
    """Month-M label knowable at 12th of M+lag (lag=2 ONI, lag=1 NAO)."""
    total = m_date.year * 12 + (m_date.month - 1) + lag
    return pd.Timestamp(year=total // 12, month=total % 12 + 1, day=12)


def z_vs_trailing(series_m, years=10, min_years=5):
    """z vs trailing `years` same-month history (min min_years), using ONLY
    data at least 1 year old. Mirrors HUNT_WX_DEMAND construction."""
    out = pd.Series(index=series_m.index, dtype=float)
    vals = series_m.values
    idx = series_m.index
    for i, ts in enumerate(idx):
        hist = [vals[j] for j in range(i)
                if idx[j].month == ts.month and (ts - idx[j]).days >= 365]
        if len(hist) < min_years:
            continue
        h = np.array(hist[-years:])
        sd = h.std(ddof=1)
        if sd <= 1e-12:
            continue
        out.iloc[i] = (vals[i] - h.mean()) / sd
    return out


def state_pos(z_m, thr):
    """Symmetric state tilt: +1 if z >= +thr, -1 if z <= -thr, else 0."""
    pos = pd.Series(0.0, index=z_m.index)
    pos[z_m >= thr] = 1.0
    pos[z_m <= -thr] = -1.0
    return pos


def net_returns(daily_ret, daily_w):
    """T+1 accounting (caller shifts w). Costs on FULL |dW|. Borrow on short."""
    dw = daily_w.diff().abs().fillna(daily_w.abs())
    gross_short = daily_w.clip(upper=0).abs()
    borrow_daily = gross_short * BORROW / 252.0
    return daily_ret * daily_w - dw * COST - borrow_daily


def sr(x):
    x = x.dropna()
    if len(x) < 200 or x.std(ddof=1) <= 1e-12:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def halves(x):
    x = x.dropna()
    h = len(x) // 2
    return sr(x.iloc[:h]), sr(x.iloc[h:])


def neg_years(x):
    x = x.dropna()
    yr = (1 + x).groupby(x.index.year).prod() - 1
    return int((yr < 0).sum()), float(yr.min()) if len(yr) else 0.0


def vol_target(net, target=0.10, min_hist=252):
    """Trailing-only vol target ~10% ann, scale clip <= 3.0 (gate g)."""
    vol = net.shift(1).rolling(min_hist).std() * np.sqrt(252)
    scale = (target / vol).clip(upper=3.0)
    return (net * scale).dropna()


def daily_state(pos_m, days, lag):
    """Monthly states -> daily as-of state via conservative signal dates."""
    sig_dates = pd.Series(
        pos_m.values,
        index=pd.DatetimeIndex([month_signal_date(d, lag) for d in pos_m.index])
    ).sort_index()
    pos_idx = np.searchsorted(sig_dates.index.values, days.values, side="right") - 1
    return pd.Series(
        [sig_dates.iloc[i] if i >= 0 else 0.0 for i in pos_idx], index=days)


def build_tilt_net(pos_m, etf_ret, lag, mask_months=None):
    """Monthly position series -> daily net (T+1, costs, NO vol-target)."""
    days = etf_ret.index
    state_d = daily_state(pos_m, days, lag)
    if mask_months is not None:
        state_d = state_d * state_d.index.month.isin(mask_months).astype(float)
    w = state_d.shift(1)  # T+1
    return net_returns(etf_ret.fillna(0.0), w)


def scramble_p_states(pos_m, etf_ret, lag, real_net_vt, seed=17, n=200,
                      mask_months=None):
    """Gate e per CONTRACT: permute monthly state sequence, rebuild pipeline,
    p = frac(|SR_scram| >= |SR_real|). Pass iff p < 0.05."""
    vals = np.array(pos_m.values, copy=True)
    rng = np.random.default_rng(seed)
    real = abs(sr(real_net_vt))
    wins = 0
    for _ in range(n):
        rng.shuffle(vals)
        net = build_tilt_net(pd.Series(vals, index=pos_m.index),
                             etf_ret, lag, mask_months)
        if abs(sr(vol_target(net))) >= real:
            wins += 1
    return wins / n


def corr_vs_champion(net_vt, champ):
    j = pd.concat([net_vt.rename("s"), champ.rename("c")],
                  axis=1, join="inner").dropna()
    if len(j) < 200:
        return float("nan")
    return float(j["s"].corr(j["c"]))


def record(fam, label, net_vt, champ, results):
    h1, h2 = halves(net_vt)
    ny, worst = neg_years(net_vt)
    results.append({
        "fam": fam, "config": label, "SR": sr(net_vt),
        "H1": h1, "H2": h2, "negY": ny, "worstY": worst,
        "corr": corr_vs_champion(net_vt, champ),
        "span": f"{net_vt.index[0].date()}..{net_vt.index[-1].date()}",
        "n": len(net_vt),
    })


# ------------------------------------------------------------------ E4 pieces
E4_SYMS = ("CORN", "WEAT", "SOYB")


def e4_weights(active_m, closes, lag, mode):
    """Cross-sectional weights per ETF. At each monthly signal date where the
    state is active: rank E4_SYMS by trailing 60-TRADING-day cumulative return
    (knowable at the signal date); long the weakest / short the strongest
    (mode='nino') or long the strongest / short the weakest (mode='nina').
    Positions persist until the next monthly signal date. Flat when inactive
    or insufficient history (<61 obs on any ETF)."""
    days_idx = closes["DBA"].index
    W = {s: pd.Series(0.0, index=days_idx) for s in E4_SYMS}
    sig = [month_signal_date(d, lag) for d in active_m.index]
    for i, act in enumerate(active_m.values):
        d = sig[i]
        if not act or d > days_idx[-1]:
            continue
        d_next = sig[i + 1] if i + 1 < len(sig) else days_idx[-1] + pd.Timedelta(days=1)
        r60 = {}
        for s in E4_SYMS:
            c = closes[s]
            hist = c[c.index <= d]
            if len(hist) < 61:
                r60 = None
                break
            r60[s] = hist.iloc[-1] / hist.iloc[-61] - 1.0
        if r60 is None:
            continue
        ranked = sorted(r60, key=r60.get)  # weakest..strongest
        long_s, short_s = (ranked[0], ranked[-1]) if mode == "nino" \
            else (ranked[-1], ranked[0])
        block = (days_idx >= d) & (days_idx < d_next)
        for s in E4_SYMS:
            W[s][block] = 0.0
        W[long_s][block] = 1.0
        W[short_s][block] = -1.0
    return W


def e4_net(W, rets):
    """Per-ETF leg nets (T+1, per-leg costs + borrow), sleeve = mean of the
    two legs = sum over ETFs / 2 (charter: equal-weight of leg net returns)."""
    total = None
    for s in E4_SYMS:
        w = W[s].shift(1)  # T+1
        leg = net_returns(rets[s].fillna(0.0), w)
        total = leg if total is None else total + leg
    return total / 2.0


def scramble_p_e4(active_m, closes, rets, lag, mode, real_net_vt,
                  seed=17, n=200):
    vals = np.array(active_m.values, copy=True)
    rng = np.random.default_rng(seed)
    real = abs(sr(real_net_vt))
    wins = 0
    for _ in range(n):
        rng.shuffle(vals)
        W = e4_weights(pd.Series(vals, index=active_m.index),
                       closes, lag, mode)
        if abs(sr(vol_target(e4_net(W, rets)))) >= real:
            wins += 1
    return wins / n


def main():
    oni = load_index("oni")
    nao = load_index("nao")
    load_index("meiv2")  # sha-assert pinned input (unused by configs)
    dba = load_etf("DBA")
    closes = {"DBA": dba, "CORN": load_etf("CORN"),
              "WEAT": load_etf("WEAT"), "SOYB": load_etf("SOYB")}
    rets = {s: c.pct_change().clip(-0.25, 0.25) for s, c in closes.items()}
    champ = pd.read_csv(CHAMPION, index_col=0, parse_dates=True)["ret"]

    oni_z = z_vs_trailing(oni).clip(-4, 4)
    nao_z = z_vs_trailing(nao).clip(-4, 4)

    results = []

    # -------------------------------------------------- E1 ONI state tilt DBA
    for thr in (0.5, 1.0, 1.5):
        pos = state_pos(oni_z, thr)
        for sign, dname in ((1, "ninolong"), (-1, "ninalong")):
            label = f"E1_oni{thr}_{dname}"
            net = build_tilt_net(sign * pos, rets["DBA"], lag=2)
            net_vt = vol_target(net)
            record("E1", label, net_vt, champ, results)
            results[-1]["scramble"] = scramble_p_states(
                sign * pos, rets["DBA"], lag=2, real_net_vt=net_vt)

    # ------------------------------------- E2 ONI state, SH harvest Nov..Mar
    for sign, dname in ((1, "ninolong"), (-1, "ninalong")):
        label = f"E2_oni1.0sh_{dname}"
        pos = state_pos(oni_z, 1.0)
        net = build_tilt_net(sign * pos, rets["DBA"], lag=2,
                             mask_months=(11, 12, 1, 2, 3))
        net_vt = vol_target(net)
        record("E2", label, net_vt, champ, results)
        results[-1]["scramble"] = scramble_p_states(
            sign * pos, rets["DBA"], lag=2, real_net_vt=net_vt,
            mask_months=(11, 12, 1, 2, 3))

    # -------------------------------------------------- E3 NAO state tilt DBA
    for thr in (1.0, 1.5):
        pos = state_pos(nao_z, thr)
        for sign, dname in ((1, "highlong"), (-1, "lowlong")):
            label = f"E3_nao{thr}_{dname}"
            net = build_tilt_net(sign * pos, rets["DBA"], lag=1)
            net_vt = vol_target(net)
            record("E3", label, net_vt, champ, results)
            results[-1]["scramble"] = scramble_p_states(
                sign * pos, rets["DBA"], lag=1, real_net_vt=net_vt)

    # ------------------------------------- E4 ONI-conditioned ag cross-section
    for mode, mname in ((1, "nino"), (-1, "nina")):
        z = mode * oni_z
        active = z >= 1.0
        label = f"E4_ls1.0_{mname}"
        W = e4_weights(active, closes, lag=2,
                       mode="nino" if mode == 1 else "nina")
        net_vt = vol_target(e4_net(W, rets))
        record("E4", label, net_vt, champ, results)
        results[-1]["scramble"] = scramble_p_e4(
            active, closes, rets, lag=2,
            mode="nino" if mode == 1 else "nina", real_net_vt=net_vt)

    # ------------------------------------------------------------------ report
    print(f"{'fam':4} {'config':22} {'SR':>7} {'H1':>6} {'H2':>6} "
          f"{'negY':>4} {'worstY':>7} {'scram':>6} {'|corr|':>6}  span")
    for r in results:
        print(f"{r['fam']:4} {r['config']:22} {r['SR']:7.3f} "
              f"{r['H1']:6.3f} {r['H2']:6.3f} {r['negY']:4d} "
              f"{r['worstY']:7.3f} {r['scramble']:6.3f} "
              f"{abs(r['corr']):6.3f}  {r['span']} n={r['n']}")
    print("total configs:", len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
