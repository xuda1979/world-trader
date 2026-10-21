#!/usr/bin/env python3
"""HUNT_SECTOR2 R2 full scan: 4 arms, all variants, guarded accounting (T+1, 6.4bps
FULL |dW|, borrow, trailing VT10 clip3, no_silent_fill + window_check). Prints the
top of each arm and dumps /tmp/sector2_r2_scan.csv + store of nets for gating."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import hunt_sector2_r2_harness as H
import hunt_sector2_lib as L

ROWS, NETS, WS = [], {}, {}


def run(variant, w, rets):
    net = H.net_multi(w, rets)
    s = L.stats(net)
    raw = H.net_multi(w, rets, vt=None)
    rows = dict(variant=variant, n=s["n"], sr=round(s["sr"], 3), raw_sr=round(L.stats(raw)["sr"], 3),
                ann=round(s["ann"], 2), vol=round(s["vol"], 2), neg_yr=s["neg_yr"],
                n_yr=s["n_yr"], worst=round(s["worst"], 1), h1=round(s["h1"], 2),
                h2=round(s["h2"], 2), corr=round(L.corr_champ(net), 3))
    ROWS.append(rows)
    NETS[variant] = net
    WS[variant] = w
    return s


def show(tag):
    d = pd.DataFrame([r for r in ROWS if r["variant"].startswith(tag)])
    if len(d):
        print(f"\n--- {tag} (top 8 of {len(d)}) ---")
        print(d.sort_values("sr", ascending=False).head(8).to_string(index=False))


def main():
    px = {t: L.etf_close(t) for t in L.SECTORS + ["SPY", "IEF", "LQD", "TLT", "USO", "DBC"]}

    # ---- book calendars (per-book inner join, then >= START) ----
    def book(tickers):
        j = pd.concat([px[t] for t in tickers], axis=1, join="inner").dropna()
        return L.book_rets(tickers).loc[lambda d: d.index >= H.START]

    bookA = L.book_rets(H.S9, extra=["SPY"])
    bookA = bookA[bookA.index >= H.START]
    retsA = bookA[H.S9]
    spy_rets = bookA["SPY"]

    bookB = L.book_rets(H.RISK + H.DEF, extra=["IEF"])
    bookB = bookB[bookB.index >= H.START]
    retsB = bookB[H.RISK + H.DEF + ["IEF"]]
    vix = L.fred("VIXCLS")

    bookC = L.book_rets(["XLE"], extra=["USO", "DBC"])
    bookC = bookC[bookC.index >= H.START]
    retsC = bookC[["XLE"]].copy()
    retsC["IEF"] = L.etf_ret("IEF").reindex(bookC.index)

    bookD = L.book_rets(H.S9, extra=["IEF"])
    bookD = bookD[bookD.index >= H.START]
    retsD = bookD[H.S9 + ["IEF"]]

    print("book rows: A=%d B=%d C=%d D=%d (start %s..%s)" % (
        len(bookA), len(bookB), len(bookC), len(bookD),
        bookA.index.min().date(), bookA.index.max().date()))

    # ================= ARM A: RS-ratio rotation =================
    print("\n=== ARM A: RS-ratio (log sector/SPY) momentum, long top-K ===")
    rslog = {}
    for t in H.S9:
        rslog[t] = np.log(px[t] / px["SPY"]).reindex(bookA.index).ffill()
    rslog = pd.DataFrame(rslog)

    for lb in (63, 126, 189, 252):
        mom = rslog - rslog.shift(lb)
        rank = mom.rank(axis=1, ascending=False)
        for k in (2, 3, 4):
            wl = rank.le(k).astype(float).div(k)
            run(f"A|lb{lb}|k{k}|long", H.weekly_weights(wl), retsA)
            ws = rank.le(k).astype(float).div(k) - rank.gt(len(H.S9) - k).astype(float).div(k)
            run(f"A|lb{lb}|k{k}|LS", H.weekly_weights(ws), retsA)
    show("A|")

    # ================= ARM B: sector-bond barbell =================
    print("\n=== ARM B: risk/def spread momentum, VIX gate -> IEF ===")
    rp = pd.concat([px[t] for t in H.RISK], axis=1).mean(axis=1).reindex(bookB.index)
    dp = pd.concat([px[t] for t in H.DEF], axis=1).mean(axis=1).reindex(bookB.index)
    spr = np.log(rp / dp).reindex(bookB.index)
    v = vix.reindex(bookB.index).ffill()
    ma = v.rolling(252, min_periods=126).mean()
    for mlb in (21, 63, 126):
        m = ((spr - spr.shift(mlb)) > 0).fillna(False)
        for gname, g in (("off", pd.Series(False, v.index)),
                         ("mean100", (v > ma).fillna(False)),
                         ("mean110", (v > 1.1 * ma).fillna(False))):
            for sw in ("IEF", "IEFhalf"):
                w = pd.DataFrame(0.0, index=bookB.index,
                                 columns=H.RISK + H.DEF + ["IEF"])
                risk_on, defn, stress = m & ~g, (~m) & (~g), g
                for t in H.RISK:
                    w[t] = np.where(risk_on, 1 / 3, 0.0)
                for t in H.DEF:
                    w[t] = np.where(defn, 1 / 3, 0.0)
                if sw == "IEF":
                    w["IEF"] = np.where(stress, 1.0, 0.0)
                else:
                    for t in H.RISK:
                        w[t] = np.where(m, 1 / 6, 0.0)
                    for t in H.DEF:
                        w[t] = np.where(~m, 1 / 6, 0.0)
                    w["IEF"] = np.where(g, 0.5, 0.0)
                run(f"B|m{mlb}|{gname}|{sw}", H.weekly_weights(w), retsB)
    show("B|")

    # ================= ARM C: XLE vs CRUD lead-lag =================
    print("\n=== ARM C: XLE/CRUD lead-lag switch ===")
    crud = ((L.etf_ret("USO") + L.etf_ret("DBC")) / 2).reindex(bookC.index).fillna(0.0)
    xler = retsC["XLE"]
    for xwin in (42, 63, 126):
        corr = xler.rolling(xwin).corr(crud.shift(5))
        cr63 = crud.rolling(63).sum()
        sig = (corr > 0) & (cr63 > 0)
        for mode in ("switch", "longflat"):
            w = pd.DataFrame(0.0, index=bookC.index, columns=["XLE", "IEF"])
            w["XLE"] = np.where(sig.fillna(False), 1.0, 0.0)
            if mode == "switch":
                w["IEF"] = np.where((~sig) & corr.notna(), 1.0, 0.0)
            run(f"C|w{xwin}|{mode}", H.weekly_weights(w), retsC)
    show("C|")

    # ================= ARM D: XLU/IEF stealth-rate =================
    print("\n=== ARM D: XLU/IEF stealth-rate de-risk ===")
    ratio = np.log(px["XLU"] / px["IEF"]).reindex(bookD.index).ffill()
    for lb in (21, 63, 126, 252):
        tr = (ratio - ratio.rolling(lb).mean()) > 0
        for dirn in ("riskoff", "riskon"):
            bad = tr.fillna(False) if dirn == "riskoff" else ~tr.fillna(False)
            for tgt in ("IEF", "DEF", "FLAT"):
                w = pd.DataFrame(0.0, index=bookD.index, columns=H.S9 + ["IEF"])
                if tgt == "IEF":
                    for t in H.S9:
                        w[t] = np.where(~bad, 1 / len(H.S9), 0.0)
                    w["IEF"] = np.where(bad, 1.0, 0.0)
                elif tgt == "DEF":
                    for t in H.S9:
                        w[t] = np.where(~bad, 1 / len(H.S9), 0.0)
                    for t in H.DEF:
                        w[t] = np.where(bad, 1 / 3, 0.0)
                else:
                    for t in H.S9:
                        w[t] = np.where(~bad, 1 / len(H.S9), 0.0)
                run(f"D|lb{lb}|{dirn}|{tgt}", H.weekly_weights(w), retsD)
    show("D|")

    df = pd.DataFrame(ROWS).sort_values("sr", ascending=False)
    df.to_csv("/tmp/sector2_r2_scan.csv", index=False)
    print(f"\nTOTAL VARIANTS: {len(df)}   FULL-WINDOW rows A={ROWS[0]['n']}")
    import pickle
    with open("/tmp/sector2_r2_store.pkl", "wb") as f:
        pickle.dump({"nets": NETS, "ws": WS}, f)
    print("top 12 overall:")
    print(df.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
