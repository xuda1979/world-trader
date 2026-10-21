#!/usr/bin/env python3
"""HUNT_SECTOR2 ROUND 2 hunter. Four arms per charter:
 (a) RS-RATIO rotation: SPY-relative-strength ratio momentum, top-3 sectors, weekly, VT10.
 (b) SECTOR-BOND barbell switch: risk-vs-defensive spread momentum, VIXCLS gate -> IEF.
 (c) XLE-vs-CRUD lead-lag: lagged crude momentum as energy timing switch.
 (d) XLU-as-bond-proxy: XLU/IEF ratio trend as stealth-rate de-risk signal.
Costs 6.4bps one-side FULL |dW| + borrow 0.5%/yr short notional; T+1; trailing-only VT10 clip<=3.
Run: python3 hunt_sector2_r2.py            (scans + full gate block on every arm/variant)
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import hunt_sector2_lib as L

COST, BORROW, ANN = L.COST, L.BORROW, L.ANN
OUT = []          # result rows


# ---------------------------------------------------------------- accounting
def net_multi(w: pd.DataFrame, rets: pd.DataFrame, vt="on", cap=3.0) -> pd.Series:
    """w = desired weights at close t (UNshifted). T+1 shift, optional trailing-only VT
    on the BOOK return, 6.4bps on FULL |dW|, borrow on short notional. Fail-closed on
    zero-filled active legs."""
    L.no_silent_fill(w, rets)
    p = w.shift(1).fillna(0.0)
    r = rets.reindex(p.index)
    if vt == "on":
        s = L.vt_scale((p * r).sum(axis=1), cap=cap)
        p = p.mul(s, axis=0)
    to = p.diff().abs().sum(axis=1)
    to.iloc[0] = p.iloc[0].abs().sum()
    gross = (p * r).sum(axis=1)
    short = (-p.clip(upper=0.0)).sum(axis=1)
    return (gross - to * COST / 1e4 - short * BORROW / ANN).dropna()


def weekly_weights(daily_sig: pd.DataFrame) -> pd.DataFrame:
    """Signal computed daily -> hold the last signal of each ISO week, ffilled to the
    daily grid. net_multi's shift(1) makes the week-end decision tradable next day."""
    eow = daily_sig.groupby([daily_sig.index.isocalendar().year,
                             daily_sig.index.isocalendar().week]).apply(lambda x: x.index[-1])
    w = daily_sig.loc[eow.values]
    return w.reindex(daily_sig.index).ffill().fillna(0.0)


def scramble_multi(w: pd.DataFrame, rets: pd.DataFrame, n=200, seed=0) -> float:
    """Signal-scramble on the joint weight path (rows permuted, legs kept aligned)."""
    rng = np.random.default_rng(seed)
    p = w.shift(1).fillna(0.0)
    r = rets.reindex(p.index).values
    pv = p.values

    def sr_of(q):
        to = np.abs(np.diff(q, axis=0, prepend=np.zeros((1, q.shape[1])))).sum(axis=1)
        net = (q * r).sum(axis=1) - to * COST / 1e4 \
            + np.minimum(q, 0.0).sum(axis=1) * -BORROW / ANN
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(ANN))

    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        if sr_of(rng.permutation(pv, axis=0)) >= real:
            cnt += 1
    return cnt / n


def plateau(sr_by_param: dict, chosen) -> str:
    """Chosen param's SR must be within 20% of the scan peak AND neighbors within 20%."""
    srs = sr_by_param
    peak = max(srs.values())
    if chosen not in srs:
        return "FAIL_no_param"
    neigh = [v for k, v in srs.items() if k != chosen]
    ok_self = srs[chosen] >= 0.8 * peak
    ok_neigh = (max(neigh) >= 0.8 * peak) if neigh else False
    return "PASS" if (ok_self and ok_neigh) else f"FAIL(self={srs[chosen]:.2f} peak={peak:.2f} maxneigh={max(neigh):.2f})"


def gates(name, w, rets, sr_by_param=None, chosen=None, vt="on", extra="") -> dict:
    net = net_multi(w, rets, vt=vt)
    s = L.stats(net)
    cc = L.corr_champ(net)
    lib = L.corr_library(net)
    sp = scramble_multi(w, rets, n=200, seed=0)
    g = {
        "name": name, "n": s["n"], "sr": round(s["sr"], 3), "ann": round(s["ann"], 2),
        "vol": round(s["vol"], 2), "h1": round(s["h1"], 2), "h2": round(s["h2"], 2),
        "neg_yr": s["neg_yr"], "n_yr": s["n_yr"], "worst": round(s["worst"], 1),
        "corr_champ": round(cc, 3), "corr_lib_maxabs": lib["maxabs"],
        "scramble_p": sp, "plateau": plateau(sr_by_param, chosen) if sr_by_param else "n/a",
        "yearly": s["yearly"], "extra": extra,
    }
    g["verdict"] = (
        ("PASS" if s["sr"] >= 1.0 else "FAIL_SR") +
        ("|FAIL_HALVES" if (s["h1"] < 0.5 or s["h2"] < 0.5) else "") +
        ("|FAIL_NEGYR" if (s["neg_yr"] > 2 or s["worst"] <= -5.0) else "") +
        ("|FAIL_SCRAMBLE" if sp >= 0.05 else "") +
        ("|FAIL_PLATEAU" if g["plateau"] != "PASS" and g["plateau"] != "n/a" else "") +
        ("|corr_ok_secondary" if 0.15 <= abs(cc) < 0.35 else ("|FAIL_CORR" if abs(cc) >= 0.35 else ""))
    )
    OUT.append(g)
    print(f"[{name}] n={s['n']} SR={s['sr']:.3f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
          f"H1={s['h1']:.2f} H2={s['h2']:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% "
          f"corr={cc:.3f} scramble_p={sp:.3f} plateau={g['plateau']} -> {g['verdict']}")
    return g


def save_sleeve(g, net):
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
    os.makedirs(d, exist_ok=True)
    nm = g["name"].replace("/", "_").replace(" ", "_")
    df = pd.DataFrame({"ret": net})
    df.index.name = "date"
    df.to_csv(f"{d}/{nm}.csv")
    with open(f"{d}/{nm}.csv.meta", "w") as f:
        f.write(f"name={nm}\nverdict={g['verdict']}\n")
        for k in ("sr", "ann", "vol", "h1", "h2", "neg_yr", "n_yr", "worst",
                  "corr_champ", "scramble_p", "plateau", "extra"):
            f.write(f"{k}={g[k]}\n")
        f.write(f"yearly={g['yearly']}\n")
        f.write("cost=6.4bps one-side FULL |dW| + 0.5%/yr borrow; T+1; trailing VT10 clip3\n")
        f.write("rationale=" + RATIONALE.get(nm.split('#')[0], "see FINDINGS") + "\n")


RATIONALE = {
    "A_rs_ratio": "Cross-sectional RS-ratio (sector/SPY) momentum: capital concentrates in "
                  "sectors outperforming the index; the ratio removes beta so the bet is "
                  "relative strength, funded weekly with a 10% vol target to respect costs.",
    "B_barbell":  "Risk-vs-defensive spread momentum rotates between risk-on and defensive "
                  "sectors; a VIX regime gate (VIX above trailing median) flips the defensive "
                  "leg into IEF, i.e. the barbell's safe arm is bonds when vol is elevated.",
    "C_xle_crud": "Crude leads energy equities at the sector level; lagged USO/DBC momentum "
                  "times the XLE sleeve so energy exposure is taken only when the physical "
                  "commodity already confirms.",
    "D_xlu_ief":  "XLU/IEF is a stealth-rate proxy: utilities outperforming duration signals "
                  "falling real rates, so a deteriorating ratio de-risks the sector book into "
                  "IEF before equity breadth breaks.",
}


# ---------------------------------------------------------------- ARM A
def arm_a():
    print("\n=== ARM A: RS-RATIO rotation (sector/SPY ratio momentum, top3, weekly, VT10) ===")
    rets = L.book_rets(L.SECTORS, extra=["SPY"]).dropna()
    spy = L.etf_close("SPY").reindex(rets.index).ffill()
    scan = {}
    best = None
    for lb in (63, 126, 189, 252):
        ratios = pd.concat({t: L.etf_close(t).reindex(rets.index).ffill() / spy for t in L.SECTORS}, axis=1)
        mom = ratios.pct(lb)
        rk = mom.rank(axis=1, ascending=False)
        longs = rk <= 3
        w = weekly_weights(longs.astype(float).div(3.0))
        net = net_multi(w, rets[L.SECTORS])
        s = L.stats(net)
        scan[lb] = round(s["sr"], 3)
        print(f"  A long-top3 lb={lb}: SR={s['sr']:.3f} ann={s['ann']:.1f}% negyr={s['neg_yr']}")
        if best is None or s["sr"] > best[1]:
            best = (lb, s["sr"], w.copy())
    g = gates("A_rs_ratio#long_top3", best[2], rets[L.SECTORS], sr_by_param=scan, chosen=best[0],
              extra=f"lb={best[0]} scan={scan}")
    if g["verdict"].startswith("PASS") or "FAIL_SCRAMBLE" not in g["verdict"]:
        save_sleeve(g, net_multi(best[2], rets[L.SECTORS]))

    # L/S variant on the best lookback: long top3 / short bottom3
    lb = best[0]
    rk = ratios.pct(lb).rank(axis=1, ascending=False)
    wls = weekly_weights((rk <= 3).astype(float).div(3.0) - (rk > len(L.SECTORS) - 3).astype(float).div(3.0))
    g2 = gates(f"A_rs_ratio#LS_top3bot3_lb{lb}", wls, rets[L.SECTORS], extra=f"lb={lb}")


# ---------------------------------------------------------------- ARM B
def arm_b():
    print("\n=== ARM B: SECTOR-BOND barbell switch (risk vs def spread mom, VIX gate -> IEF) ===")
    risk, defs = ["XLK", "XLY", "XLI"], ["XLP", "XLU", "XLV"]
    rets = L.book_rets(risk + defs, extra=["IEF"]).dropna()
    rr = rets[risk].mean(axis=1)
    dr = rets[defs].mean(axis=1)
    vix = L.fred("VIXCLS").reindex(rets.index).ffill()
    scan = {}
    best = None
    for lb in (63, 126, 252):
        for mode in ("full_ief", "half_ief"):
            sp = (1 + rr).rolling(lb).apply(np.prod, raw=True) / \
                 (1 + dr).rolling(lb).apply(np.prod, raw=True) - 1
            gate = (vix > vix.rolling(63).median()).astype(float)
            w = pd.DataFrame(0.0, index=rets.index,
                             columns=risk + defs + ["IEF"])
            riskon = (sp > 0) & (gate == 0)
            w.loc[riskon, risk] = 1 / 3
            w.loc[(sp <= 0) & (gate == 0), defs] = 1 / 3
            if mode == "full_ief":
                w.loc[gate == 1, "IEF"] = 1.0
            else:
                w.loc[gate == 1, defs] = 1 / 6
                w.loc[gate == 1, "IEF"] = 0.5
            w = weekly_weights(w)
            net = net_multi(w, rets)
            s = L.stats(net)
            scan[(lb, mode)] = round(s["sr"], 3)
            print(f"  B lb={lb} {mode}: SR={s['sr']:.3f} ann={s['ann']:.1f}% negyr={s['neg_yr']}")
            if best is None or s["sr"] > best[1]:
                best = ((lb, mode), s["sr"], w.copy())
    (lb, mode), _, w = best
    g = gates("B_barbell#vix_ief", w, rets, sr_by_param=scan, chosen=(lb, mode),
              extra=f"lb={lb} mode={mode} scan={scan}")
    save_sleeve(g, net_multi(w, rets))


# ---------------------------------------------------------------- ARM C
def arm_c():
    print("\n=== ARM C: XLE-vs-CRUD lead-lag energy timing switch ===")
    for crud in ("USO", "DBC"):
        rets = L.book_rets(["XLE"], extra=[crud, "SPY"]).dropna()
        cr = rets[crud]
        for lead in (0, 5, 10):
            for lb in (21, 63):
                cm = (1 + cr).rolling(lb).apply(np.prod, raw=True).shift(lead) - 1
                sig = (cm > 0).astype(float)          # long XLE only when crude confirms
                w = weekly_weights(pd.DataFrame({"XLE": sig}))
                net = net_multi(w, rets[["XLE"]])
                s = L.stats(net)
                print(f"  C crud={crud} lead={lead} lb={lb}: SR={s['sr']:.3f} ann={s['ann']:.1f}% "
                      f"negyr={s['neg_yr']}")
                if lead == 0 and lb == 63:
                    g = gates(f"C_xle_crud#{crud}_lb{lb}", w, rets[["XLE"]],
                              extra=f"lead={lead} lb={lb}")
                    save_sleeve(g, net_multi(w, rets[["XLE"]]))


# ---------------------------------------------------------------- ARM D
def arm_d():
    print("\n=== ARM D: XLU/IEF ratio trend stealth-rate de-risk ===")
    rets = L.book_rets(L.SECTORS, extra=["IEF"]).dropna()
    xu = L.etf_close("XLU").reindex(rets.index).ffill()
    ie = L.etf_close("IEF").reindex(rets.index).ffill()
    ratio = xu / ie
    base = rets[L.SECTORS]
    scan = {}
    best = None
    for lb in (63, 126, 252):
        for thr in (0.0, -0.02):
            tr = ratio.pct(lb)
            derisk = tr < thr                       # stealth rates rising -> de-risk
            w = pd.DataFrame(0.0, index=rets.index, columns=list(L.SECTORS) + ["IEF"])
            w.loc[~derisk, L.SECTORS] = 1 / len(L.SECTORS)
            w.loc[derisk, "IEF"] = 1.0
            w = weekly_weights(w)
            net = net_multi(w, rets)
            s = L.stats(net)
            scan[(lb, thr)] = round(s["sr"], 3)
            print(f"  D lb={lb} thr={thr}: SR={s['sr']:.3f} ann={s['ann']:.1f}% negyr={s['neg_yr']}")
            if best is None or s["sr"] > best[1]:
                best = ((lb, thr), s["sr"], w.copy())
    (lb, thr), _, w = best
    g = gates("D_xlu_ief#derisk", w, rets, sr_by_param=scan, chosen=(lb, thr),
              extra=f"lb={lb} thr={thr} scan={scan}")
    save_sleeve(g, net_multi(w, rets))


if __name__ == "__main__":
    arm_a(); arm_b(); arm_c(); arm_d()
    print("\n=== SUMMARY ===")
    for g in OUT:
        print(f"{g['name']:36s} SR={g['sr']:.3f} negyr={g['neg_yr']} corr={g['corr_champ']} "
              f"scramble_p={g['scramble_p']:.3f} -> {g['verdict']}")
