#!/usr/bin/env python3
"""HUNT_SECTOR2 round-2 scan: (a) RS-ratio rotation, (b) sector-bond barbell w/ VIX gate,
(c) XLE-vs-CRUD lead-lag switch, (d) XLU/IEF stealth-rate de-risk.
T+1 everywhere, 6.4bps one-side FULL |dW|, borrow 0.5%/yr shorts, trailing 10% VT clip 3.
Eval from 2008-01-01 (champion starts 2008-03-31). Per-BOOK calendars (no cross-book
XLC/DBC binding); no_silent_fill guard on every book. Writes /tmp/sector2_scan.csv."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2")
import hunt_sector2_lib as L

START = "2008-01-01"
RISK = ["XLK", "XLY", "XLI"]
DEF = ["XLP", "XLU", "XLV"]
S9 = [t for t in L.SECTORS if t not in ("XLC", "XLRE")]
RET = {t: L.etf_ret(t) for t in L.SECTORS + ["IEF", "LQD", "TLT", "USO", "DBC"]}
SPY_R = L.etf_close("SPY").pct_change()
VIX = L.fred("VIXCLS")


def cal_of(tickers, extra=()):
    """Per-book calendar: inner join on THIS book's own legs (never another leg's start)."""
    parts = [RET[t] for t in tickers] + [RET[t] for t in extra] + [SPY_R] * (len(extra) == 0 and True or False)
    parts = [RET[t] for t in tickers] + [RET[t] for t in extra]
    if len(extra) == 0:
        parts = parts + [SPY_R]
    j = pd.concat(parts, axis=1, join="inner").dropna()
    return j.index[j.index >= START]


def net_multi(w: pd.DataFrame, rets: pd.DataFrame, vt="on") -> pd.Series:
    """Joint multi-leg book: T+1, optional per-BOOK VT (scale whole book, trailing only),
    6.4bps on sum_i |dW_i| (FULL traded notional), borrow 0.5%/yr on short legs."""
    L.no_silent_fill(w, rets)
    p = w.shift(1).fillna(0.0)
    if vt == "on":
        bk = (p * rets).sum(axis=1)
        p = p.mul(L.vt_scale(bk, cap=3.0), axis=0)
    r = rets.reindex(p.index)
    to = p.diff().abs().sum(axis=1)
    to.iloc[0] = p.iloc[0].abs().sum()
    gross = (p * r).sum(axis=1)
    bor = (-p.clip(upper=0.0)).sum(axis=1) * L.BORROW / L.ANN
    return (gross - to * L.COST / 1e4 - bor).dropna()


# ---------------- (a) RS-ratio rotation ----------------
def a_positions(sectors, lb=126, topk=3, rebal="W-FRI"):
    px = pd.DataFrame({t: L.etf_close(t) for t in sectors})
    spy = L.etf_close("SPY").rename("SPY")
    j = pd.concat([px, spy], axis=1, join="inner").dropna()
    rs = np.log(j[sectors].div(j["SPY"], axis=0))
    mom = rs - rs.shift(lb)
    rank = mom.rank(axis=1, ascending=False)
    w = pd.DataFrame(0.0, index=j.index, columns=sectors)
    for t in sectors:
        w[t] = np.where(rank[t] <= topk, 1.0 / topk, 0.0)
    if rebal != "D":
        w = w.resample(rebal).last().reindex(j.index, method="ffill")
    return w[w.index >= START]


# ---------------- (b) barbell + VIX gate ----------------
def b_positions(momlb=63, gate="mean110", switch="IEF"):
    rp = pd.DataFrame({t: L.etf_close(t) for t in RISK}).dropna()
    dp = pd.DataFrame({t: L.etf_close(t) for t in DEF}).dropna()
    j = pd.concat([rp.mean(axis=1).rename("risk"), dp.mean(axis=1).rename("def")],
                  axis=1, join="inner")
    spr = np.log(j["risk"] / j["def"])
    m = ((spr - spr.shift(momlb)) > 0).reindex(j.index).fillna(False)
    v = VIX.reindex(j.index).ffill()
    ma = v.rolling(252, min_periods=126).mean()
    sd = v.rolling(252, min_periods=126).std()
    if gate == "off":
        g = pd.Series(False, index=j.index)
    elif gate == "mean110":
        g = (v > ma * 1.10).fillna(False)
    elif gate == "mean100":
        g = (v > ma).fillna(False)
    elif gate == "z1":
        g = ((v - ma) / sd > 1.0).fillna(False)
    w = pd.DataFrame(0.0, index=j.index, columns=RISK + DEF + ["IEF"])
    risk_on, defn, stress = m & ~g, ~m & ~g, g
    if switch == "IEF":
        for t in RISK:
            w[t] = np.where(risk_on, 1.0 / 3, 0.0)
        for t in DEF:
            w[t] = np.where(defn, 1.0 / 3, 0.0)
        w["IEF"] = np.where(stress, 1.0, 0.0)
    else:  # IEFhalf: half the book always carries the momentum basket; gate parks half in IEF
        for t in RISK:
            w[t] = np.where(m, 1.0 / 6, 0.0)
        for t in DEF:
            w[t] = np.where(~m, 1.0 / 6, 0.0)
        w["IEF"] = np.where(g, 0.5, 0.0)
    return w[w.index >= START]


# ---------------- (c) XLE-vs-CRUD lead-lag ----------------
def c_positions(cal, xwin=63, lag=5, mode="switch", sgn=1):
    xle = RET["XLE"].reindex(cal).fillna(0.0)
    crud = ((RET["USO"] + RET["DBC"]) / 2).reindex(cal).fillna(0.0)
    corr = xle.rolling(xwin).corr(crud.shift(lag))
    cr_mom = crud.rolling(lag).sum()
    long_xle = ((corr > 0) & (cr_mom > 0 if sgn > 0 else cr_mom < 0)).fillna(False)
    w = pd.DataFrame(0.0, index=cal, columns=["XLE", "IEF"])
    w["XLE"] = np.where(long_xle, 1.0, 0.0)
    if mode == "switch":
        w["IEF"] = np.where(~long_xle & corr.notna(), 1.0, 0.0)
    return w


# ---------------- (d) XLU/IEF stealth-rate ----------------
def d_positions(sectors, lb=63, dirn="riskoff", target="IEF"):
    xu = L.etf_close("XLU").rename("XLU")
    ief = L.etf_close("IEF").rename("IEF")
    j = pd.concat([xu, ief], axis=1, join="inner").dropna()
    ratio = np.log(j["XLU"] / j["IEF"])
    trend = ((ratio - ratio.rolling(lb).mean()) > 0).reindex(j.index).fillna(False)
    bad = trend if dirn == "riskoff" else ~trend
    cols = sectors + (["IEF"] if target == "IEF" else DEF if target == "DEF" else [])
    w = pd.DataFrame(0.0, index=j.index, columns=cols)
    eqw = 1.0 / len(sectors)
    for t in sectors:
        w[t] = np.where(~bad, eqw, 0.0)
    if target == "IEF":
        w["IEF"] = np.where(bad, 1.0, 0.0)
    elif target == "DEF":
        for t in DEF:
            w[t] = np.where(bad, 1.0 / 3, 0.0)
    return w[w.index >= START]


def turnover(w):
    p = w.shift(1).fillna(0.0)
    return float(p.diff().abs().sum(axis=1).mean() * L.ANN * L.COST / 1e4 * 100)


def run(name, w, rets_map, vt="on", scramble=False):
    rets = pd.DataFrame(rets_map).reindex(w.index)
    net = net_multi(w, rets, vt=vt)
    raw = net_multi(w, rets, vt=None)
    st = L.stats(net)
    st.update(name=name, raw_sr=round(L.stats(raw)["sr"], 3),
              corr_champ=round(L.corr_champ(net), 3),
              cost_bp_yr=round(turnover(w), 1), scram=None)
    if scramble and st["sr"] > 0.3:
        st["scram"] = round(scramble_multi(w, rets), 3)
    return st, net


def scramble_multi(w, rets, n=200, seed=0):
    """Scramble each leg's weight path (columns permuted jointly per-row-block? No:
    per-leg independent permutation destroys cross-sectional structure too)."""
    rng = np.random.default_rng(seed)
    p = w.shift(1).fillna(0.0)
    r = rets.reindex(p.index)

    def sr_of(wv):
        to = np.abs(np.diff(wv, axis=0, prepend=wv[:1])).sum(axis=1)
        g = (wv * r.values).sum(axis=1)
        net = g - to * L.COST / 1e4
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(L.ANN))

    pv = p.values
    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        perm = np.apply_along_axis(rng.permutation, 0, pv)
        if sr_of(perm) >= real:
            cnt += 1
    return cnt / n


def main():
    rows, store = [], {}
    CAL9 = cal_of(S9)
    CAL11 = cal_of(L.SECTORS)

    # (a) RS-ratio: 9-sector long window + 11-sector charter window
    for tag, sectors, cal in (("a9", S9, CAL9), ("a11", L.SECTORS, CAL11)):
        for lb in (63, 126, 252):
            for k in (2, 3, 4):
                for rb in ("D", "W-FRI", "ME"):
                    w = a_positions(sectors, lb, k, rb)
                    st, net = run(f"{tag}|lb{lb}|k{k}|{rb}", w, {t: RET[t] for t in sectors})
                    rows.append(st); store[st["name"]] = (net, w)

    # (b) barbell: RISK/DEF/IEF all live 2006+ -> long window
    for momlb in (21, 63, 126):
        for gate in ("off", "mean100", "mean110", "z1"):
            for sw in ("IEF", "IEFhalf"):
                w = b_positions(momlb, gate, sw)
                st, net = run(f"b|m{momlb}|{gate}|{sw}", w,
                              {t: RET[t] for t in RISK + DEF + ["IEF"]})
                rows.append(st); store[st["name"]] = (net, w)

    # (c) XLE/CRUD: DBC starts 2008-01-02 -> ~champion window
    CALC = cal_of(["XLE", "USO", "DBC"])
    for xwin in (42, 63, 126):
        for lag in (1, 5, 10, 21):
            for mode in ("switch", "longflat"):
                for sgn in (1, -1):
                    w = c_positions(CALC, xwin, lag, mode, sgn)
                    st, net = run(f"c|w{xwin}|l{lag}|{mode}|s{sgn}", w,
                                  {"XLE": RET["XLE"], "IEF": RET["IEF"]})
                    rows.append(st); store[st["name"]] = (net, w)

    # (d) XLU/IEF stealth-rate: 9-sector long window + 11-sector
    for tag, sectors in (("d9", S9), ("d11", L.SECTORS)):
        for lb in (21, 63, 126, 252):
            for dirn in ("riskoff", "riskon"):
                for tgt in ("IEF", "DEF", "FLAT"):
                    w = d_positions(sectors, lb, dirn, tgt)
                    legs = sectors + (["IEF"] if tgt == "IEF" else DEF if tgt == "DEF" else [])
                    st, net = run(f"{tag}|lb{lb}|{dirn}|{tgt}", w, {t: RET[t] for t in legs})
                    rows.append(st); store[st["name"]] = (net, w)

    df = pd.DataFrame(rows)
    cols = ["name", "n", "sr", "raw_sr", "ann", "vol", "neg_yr", "n_yr", "worst",
            "h1", "h2", "corr_champ", "cost_bp_yr", "scram"]
    df = df[cols].sort_values("sr", ascending=False)
    df.to_csv("/tmp/sector2_scan.csv", index=False)
    print(df.head(25).to_string(index=False))
    print("...")
    print("TOTAL VARIANTS:", len(df))
    import pickle
    with open("/tmp/sector2_store.pkl", "wb") as f:
        pickle.dump(store, f)


if __name__ == "__main__":
    main()
