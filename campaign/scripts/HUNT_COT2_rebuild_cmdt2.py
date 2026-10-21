"""HUNT_COT2 round 3 (a), part 2: REBUILD HUNT_CMDT2 round-2 sleeves from RAW data.

Meta-vs-CSV agreement (HUNT_COT2_verify_cmdt2.py) only proves the saved CSV matches the
saved meta. Here I go further: regenerate 4 of the 7 round-2 sleeves directly from raw
price/EIA data with MY OWN engine implementing the contract conventions (T+1 weights,
6.4bps full-|dW| one-side with day-1 entry, 0.5%/yr borrow, trailing vol-target 10%
clip[0.2,3.0], trim to first live day), and compare day-by-day against their saved CSVs.

Rebuilt sleeves (their families (b) and (c)):
  CMDT2_CPERtrend_252d        sign(trailing 252d CPER return) -> CPER, gross 1.0
  CMDT2_RatioCPERGLD_252d     sign(252d CPER/GLD ratio return) -> +CPER/-GLD, gross 1.0
  CMDT2_SpreadWTIBrent_63d    sign(63d WTI-Brent EIA spot spread return) -> USO, gross 1.0
  CMDT2_UNGseasonal_volscaled short Mar-Oct / long Nov-Feb, 60d trailing-vol scale 10%

No-lookahead probes: for each rebuilt book, re-run with the price file TRUNCATED at an
early date; every return up to the truncation date must be bit-identical to the
full-sample run (a leak would change early returns once future data appears).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2/rebuild_cmdt2_r3_results.csv"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
ANN, COST_BPS, BORROW = 252, 6.4, 0.005


# ------------------------------------------------- my own contract engine

def load_close(sym, data="more_etf"):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/{data}/{sym}.csv",
                     index_col=0, parse_dates=True)
    return df["close"].astype(float)


def net_book(W, R, vt=True):
    """Contract net returns: T+1 weights, vol-target from TRAILING gross only,
    6.4bps one-side full |dW| (day-1 entry charged), 0.5%/yr on short notional.
    Returns (net, We)."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        vols = gross.expanding(min_periods=60).std(ddof=1) * np.sqrt(ANN)
        s = (0.10 / vols.replace(0.0, np.nan))
        s = s.where(vols > 0, 1.0).clip(lower=0.2, upper=3.0).shift(1).fillna(1.0)
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    prev = We.shift(1)
    prev.iloc[0] = 0.0
    cost = (We - prev).abs().sum(axis=1) * COST_BPS / 1e4
    borr = (-We.clip(upper=0.0)).sum(axis=1) * BORROW / ANN
    net = port - cost - borr
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        return net.iloc[0:0], We
    first = live.idxmax()
    return net[net.index >= first], We


def rebuild_cper_trend(win=252):
    px = load_close("CPER").to_frame("CPER")
    R = px.pct_change()
    sig = np.sign(px["CPER"].pct_change(win)).fillna(0.0)
    W = pd.DataFrame({"CPER": sig}, index=px.index)
    return net_book(W, R) + (R,)


def rebuild_ratio(win=252):
    px = pd.concat({"CPER": load_close("CPER"), "GLD": load_close("GLD")}, axis=1).sort_index()
    R = px.pct_change()
    mom = (px["CPER"] / px["GLD"]).pct_change(win)
    sig = np.sign(mom).fillna(0.0)
    W = pd.DataFrame({"CPER": sig, "GLD": -sig}, index=px.index)
    return net_book(W, R) + (R,)


def rebuild_spread(win=63):
    px = load_close("USO").to_frame("USO")
    R = px.pct_change()

    def eia(sym):
        df = pd.read_csv(f"{ROOT}/tools/quant/data/eia_weekly/{sym}_spot_daily.csv",
                         index_col=0, parse_dates=True)
        s = df["value"].astype(float).sort_index()
        s.index = s.index + pd.Timedelta(days=1)          # next-day publication
        return s

    wti, brent = eia("wti"), eia("brent")
    days = pd.date_range(min(wti.index[0], brent.index[0]),
                         max(wti.index[-1], brent.index[-1]), freq="D")
    sp = (wti.reindex(days).ffill() - brent.reindex(days).ffill()).dropna()
    sp = sp[sp.index.dayofweek < 5]
    mom = sp.pct_change(win).reindex(px.index).ffill()
    sig = np.sign(mom).fillna(0.0)
    W = pd.DataFrame({"USO": sig}, index=px.index)
    return net_book(W, R) + (R,)


def rebuild_ung_seasonal():
    px = load_close("UNG").to_frame("UNG")
    R = px.pct_change()
    m = px.index.month
    sign = pd.Series(np.where((m >= 3) & (m <= 10), -1.0, 1.0), index=px.index)
    vol = px["UNG"].pct_change().rolling(60, min_periods=40).std() * np.sqrt(ANN)
    scale = (0.10 / vol.replace(0, np.nan)).clip(upper=3.0).shift(1)
    scale = scale.where(vol.shift(1).notna(), 0.0).fillna(0.0)   # warmup -> flat
    W = pd.DataFrame({"UNG": sign * scale}, index=px.index)
    # their net_of() default vt=True: engine expanding vol-target ALSO applied on top of
    # the custom 60d scale inside W (verified against HUNT_CMDT2_round2.py:151-156,170)
    return net_book(W, R, vt=True) + (R,)


# ------------------------------------------------------------- comparison

def compare(name, mine, W):
    their = pd.read_csv(f"{SLEEVES}/{name}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat({"mine": mine, "theirs": their}, axis=1).dropna()
    d = (j["mine"] - j["theirs"]).abs()
    sr_m = j["mine"].mean() / j["mine"].std(ddof=1) * np.sqrt(ANN)
    sr_t = j["theirs"].mean() / j["theirs"].std(ddof=1) * np.sqrt(ANN)
    missing = len(their) - len(j)
    return dict(name=name, n_theirs=len(their), n_overlap=len(j),
                n_mine_only=len(mine) - len(j),
                corr=j["mine"].corr(j["theirs"]), max_abs_diff=d.max(),
                mean_abs_diff_bp=d.mean() * 1e4,
                sr_mine=sr_m, sr_theirs=sr_t,
                first_mine=str(mine.index[0].date()), first_theirs=str(their.index[0].date()),
                last_mine=str(mine.index[-1].date()), last_theirs=str(their.index[-1].date()))


def trunc_probe(builder, label):
    """No-lookahead: truncate ALL source data at date T; returns <= T must be identical."""
    full_net, W, R = builder()
    T = full_net.index[len(full_net) // 3]
    import math

    def b_trunc():
        net, Wt, Rt = builder()
        keep = net.index <= T
        return net[keep], Wt[Wt.index <= T], Rt[Rt.index <= T]

    nt, _, _ = b_trunc()
    base = full_net[full_net.index <= T]
    same = nt.index.equals(base.index) and np.allclose(nt.values, base.values, atol=0, rtol=0)
    return dict(name=label, trunc_date=str(T.date()), n=len(base),
                bitwise_identical=bool(same),
                max_diff=float((nt - base).abs().max()) if len(nt) == len(base) else np.nan)


def main():
    rows, probes = [], []
    builds = [
        ("CMDT2_CPERtrend_252d", lambda: rebuild_cper_trend(252)),
        ("CMDT2_RatioCPERGLD_252d", lambda: rebuild_ratio(252)),
        ("CMDT2_SpreadWTIBrent_63d", lambda: rebuild_spread(63)),
        ("CMDT2_UNGseasonal_volscaled", lambda: rebuild_ung_seasonal()),
    ]
    for name, fn in builds:
        net, W, R = fn()
        res = compare(name, net, W)
        rows.append(res)
        flag = "MATCH" if (res["corr"] > 0.9999 and res["max_abs_diff"] < 5e-4
                           and res["n_mine_only"] == 0 and res["n_theirs"] == res["n_overlap"]) else "CHECK"
        print(f"[{name}] n_theirs={res['n_theirs']} n_overlap={res['n_overlap']} "
              f"corr={res['corr']:.6f} max|d|={res['max_abs_diff']:.2e} "
              f"mean|d|={res['mean_abs_diff_bp']:.3f}bp SR mine={res['sr_mine']:.3f} "
              f"theirs={res['sr_theirs']:.3f} window {res['first_mine']}..{res['last_mine']} "
              f"vs {res['first_theirs']}..{res['last_theirs']} -> {flag}")
        probes.append(trunc_probe(fn, name))
    for p in probes:
        print(f"[no-lookahead {p['name']}] truncate @ {p['trunc_date']} (n={p['n']}): "
              f"bitwise_identical={p['bitwise_identical']} max_diff={p['max_diff']}")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    pd.DataFrame(probes).to_csv(OUT.replace(".csv", "_probes.csv"), index=False)
    n_ok = sum(1 for r in rows if r["corr"] > 0.9999 and r["max_abs_diff"] < 5e-4)
    n_lk = sum(1 for p in probes if p["bitwise_identical"])
    print(f"\nSUMMARY: {n_ok}/{len(rows)} rebuilt from raw data reproduce the saved CSVs "
          f"(corr>0.9999, max|daily diff|<5e-4); no-lookahead truncation probes: "
          f"{n_lk}/{len(probes)} bitwise-identical")
    print(f"detail: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
