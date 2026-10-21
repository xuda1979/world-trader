#!/usr/bin/env python3
"""HUNT_SECTOR2 round-2 harness: shared accounting + gate block for the four charter
arms (A RS-ratio rotation, B sector-bond barbell, C XLE/CRUD lead-lag, D XLU/IEF
stealth-rate). Fail-closed: no_silent_fill + window_check on every evaluation.
Costs 6.4bps one-side FULL |dW| + 0.5%/yr borrow on short notional; T+1; trailing-only
VT10 clip 3. Gates per GATES_CONTRACT.md."""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
for p in (f"{ROOT}/campaign/scripts", f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2"):
    if p not in sys.path:
        sys.path.insert(0, p)
import hunt_sector2_lib as L

START = "2008-01-01"          # champion starts 2008-03-31
S9 = [t for t in L.SECTORS if t not in ("XLC", "XLRE")]
RISK, DEF = ["XLK", "XLY", "XLI"], ["XLP", "XLU", "XLV"]


def weekly_weights(sig: pd.DataFrame) -> pd.DataFrame:
    """Last signal of each ISO week, ffilled to the ORIGINAL daily grid. Grid-preserving
    (R2 regression test): rows are never dropped or resampled away."""
    iso_y = sig.index.isocalendar().year.to_numpy()
    iso_w = sig.index.isocalendar().week.to_numpy()
    eow = pd.Series(np.arange(len(sig)), index=sig.index).groupby([iso_y, iso_w]).max()
    w = sig.iloc[eow.values]
    return w.reindex(sig.index).ffill().fillna(0.0)


def net_multi(w: pd.DataFrame, rets: pd.DataFrame, vt="on", cap=3.0) -> pd.Series:
    """w = desired weights at close t (UNshifted). T+1, optional per-BOOK trailing VT,
    6.4bps on FULL sum_i |dW_i|, borrow 0.5%/yr on short legs. Guards fail-closed."""
    L.no_silent_fill(w, rets)
    p = w.shift(1).fillna(0.0)
    if vt == "on":
        p = p.mul(L.vt_scale((p * rets).sum(axis=1), cap=cap), axis=0)
    to = p.diff().abs().sum(axis=1)
    to.iloc[0] = p.iloc[0].abs().sum()
    gross = (p * rets.reindex(p.index)).sum(axis=1)
    bor = (-p.clip(upper=0.0)).sum(axis=1) * L.BORROW / L.ANN
    net = (gross - to * L.COST / 1e4 - bor).dropna()
    L.window_check(net, rets)
    return net


def scramble_multi(w: pd.DataFrame, rets: pd.DataFrame, n=200, seed=0) -> float:
    """Signal-scramble: permute the joint (rows) weight path, legs kept aligned, against
    real returns with T+1 + full turnover cost (VT off both sides). p = P(perm SR >= real)."""
    rng = np.random.default_rng(seed)
    p = w.shift(1).fillna(0.0)
    r = rets.reindex(p.index).values
    pv = p.values

    def sr_of(q):
        to = np.abs(np.diff(q, axis=0, prepend=np.zeros((1, q.shape[1])))).sum(axis=1)
        net = (q * r).sum(axis=1) - to * L.COST / 1e4 \
            + np.minimum(q, 0.0).sum(axis=1) * -L.BORROW / L.ANN
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(L.ANN))

    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        if sr_of(rng.permutation(pv, axis=0)) >= real:
            cnt += 1
    return cnt / n


def plateau(sr_by_param: dict, chosen) -> str:
    peak = max(sr_by_param.values())
    if chosen not in sr_by_param:
        return "FAIL_no_param"
    neigh = {k: v for k, v in sr_by_param.items() if k != chosen}
    ok_self = sr_by_param[chosen] >= 0.8 * peak
    ok_neigh = bool(neigh) and max(neigh.values()) >= 0.8 * peak
    return "PASS" if (ok_self and ok_neigh) else \
        f"FAIL(self={sr_by_param[chosen]:.2f} peak={peak:.2f} maxneigh={max(neigh.values()):.2f})"


def gates(name, w, rets, sr_by_param=None, chosen=None, vt="on", extra="", save=True):
    net = net_multi(w, rets, vt=vt)
    s = L.stats(net)
    cc = L.corr_champ(net)
    sp = scramble_multi(w, rets, n=200, seed=0)
    g = dict(name=name, n=s["n"], sr=round(s["sr"], 3), ann=round(s["ann"], 2),
             vol=round(s["vol"], 2), h1=round(s["h1"], 2), h2=round(s["h2"], 2),
             neg_yr=s["neg_yr"], n_yr=s["n_yr"], worst=round(s["worst"], 1),
             corr_champ=round(cc, 3), lib=L.corr_library(net), scramble_p=round(sp, 3),
             plateau=plateau(sr_by_param, chosen) if sr_by_param else "n/a",
             yearly=s["yearly"], extra=extra)
    g["verdict"] = (
        ("PASS" if s["sr"] >= 1.0 else "FAIL_SR")
        + ("|FAIL_HALVES" if (s["h1"] < 0.5 or s["h2"] < 0.5) else "")
        + ("|FAIL_NEGYR" if (s["neg_yr"] > 2 or s["worst"] <= -5.0) else "")
        + ("|FAIL_SCRAMBLE" if sp >= 0.05 else "")
        + ("|FAIL_PLATEAU" if g["plateau"] not in ("PASS", "n/a") else "")
        + ("|corr_ok_secondary" if 0.15 <= abs(cc) < 0.35
           else ("|FAIL_CORR" if abs(cc) >= 0.35 else "")))
    print(f"[{name}] n={s['n']} SR={s['sr']:.3f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
          f"H1={s['h1']:.2f} H2={s['h2']:.2f} negyr={s['neg_yr']}/{s['n_yr']} "
          f"worst={s['worst']:.1f}% corr={cc:.3f} lib_maxabs={g['lib']['maxabs']:.2f} "
          f"scr_p={sp:.3f} plateau={g['plateau']} -> {g['verdict']}")
    if save:
        save_sleeve(g, net)
    return g


def save_sleeve(g, net):
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
    os.makedirs(d, exist_ok=True)
    nm = g["name"].replace("/", "_").replace(" ", "_").replace("|", "_")
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
        f.write("rationale=" + RATIONALE.get(g["name"].split("|")[0].split("#")[0], "see FINDINGS") + "\n")


RATIONALE = {
    "A": "Cross-sectional RS-ratio (sector/SPY log ratio) momentum: capital concentrates in "
         "sectors outperforming the index; the ratio strips beta so the bet is pure relative "
         "strength, funded weekly with a 10% vol target so 6.4bps turnover cannot eat it.",
    "B": "Risk-vs-defensive sector spread momentum rotates risk-on/off inside the equity book; "
         "a VIX regime gate (VIX > 110% of trailing 252d mean) flips the defensive arm into "
         "IEF — the barbell's safe leg is duration exactly when equity vol is elevated.",
    "C": "Physical crude leads energy equities: lagged USO/DBC momentum times the XLE sleeve, "
         "parking in IEF when the commodity has not confirmed, i.e. an energy-specific "
         "inflation-timing switch rather than a market-timing bet.",
    "D": "XLU/IEF is a stealth-rate proxy: utilities outperforming duration signals falling "
         "real rates; a deteriorating ratio de-risks the equal-weight sector book into IEF "
         "before broad equity breadth breaks.",
}
