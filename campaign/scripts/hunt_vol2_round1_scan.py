"""HUNT_VOL2 round 1 scan: charter items (a)-(e).
All sleeves/overlays are T+1, 6.4bps FULL |dW| one-side, borrow 0.5%/yr short,
trailing-only 10% vol-target clip<=3. Gates per GATES_CONTRACT.md.
Base books:
  SPY  = equity proxy (long SPY, overlay can de-risk/flip)
  CHAMP = GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (decorrelation target)
Overlays: pos = base_pos * gate  (gate in [0..1] risk-off trim, or -1..1 flip)
Standalone: pos from the vol feature itself.
"""
import sys, json, itertools
import numpy as np, pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/scratch")
import vol2_lib as L

R = L.spy()                       # SPY daily returns (target book for overlays)
CHAMP = L.champion()
START = "2011-01-04"              # VIX9D live from here (shortest series)
R = R[R.index >= START]
SPY_POS = pd.Series(1.0, index=R.index)


def z(s, win):
    m = s.rolling(win).mean(); sd = s.rolling(win).std()
    return (s - m) / sd.replace(0, np.nan)


def eval_book(name, pos, ret=R, note="", vt="on"):
    net = L.net_of(pos, ret, vt=vt)
    ok, line = L.gates_line(name, net, pos, ret, extra=note)
    return net, ok, line


rows = []
def rec(family, variant, pos, ret=R, vt="on"):
    net, ok, line = eval_book(f"{family}|{variant}", pos, ret, vt=vt)
    rows.append(dict(family=family, variant=variant, net=net, ok=ok, line=line,
                     pos=pos, ret=ret))
    return net


# ---------------- load vol features ----------------
V = {n: L.vol(n) for n in ["VIX", "VIX9D", "VIX3M", "VIX6M", "VVIX", "SKEW", "GVZ", "OVX", "RVX", "VXV"]}
V = {n: s[s.index >= START] for n, s in V.items()}

# =====================================================================
# (a) VVIX level / change as risk-off timing gate
#   gate variants: trim when VVIX z>thr or VVIX dN-day chg > thr; also flip.
# =====================================================================
print("=== (a) VVIX gate ===")
vv = V["VVIX"]
best_a = None
for win in [20, 60, 120]:
    for chg in [1, 5, 10]:
        for thr in [0.5, 1.0, 1.5, 2.0]:
            zz = z(vv, win)
            if chg > 1:
                sig = vv.diff(chg) / vv.rolling(60).std().replace(0, np.nan)
            else:
                sig = zz
            gate = (sig < thr).astype(float)  # risk-off when sig >= thr -> trim to 0
            pos = SPY_POS * gate.reindex(R.index).fillna(1.0)
            net = rec("A_VVIX", f"trim_z{win}_chg{chg}_thr{thr}", pos)
            netf = rec("A_VVIX", f"flip_z{win}_chg{chg}_thr{thr}", SPY_POS * (2 * gate - 1).reindex(R.index).fillna(0.0))
print(f"a variants run: {len(rows)}")

# standalone VVIX momentum (vol-of-vol trending => risk premium harvest direction)
for win in [10, 21, 63]:
    mom = vv.pct_change(win)
    pos = np.sign(mom).reindex(R.index).fillna(0.0)
    rec("A_VVIX_STANDALONE", f"mom{win}", pos)

# =====================================================================
# (b) SKEW sharp rise -> risk-off
# =====================================================================
print("=== (b) SKEW gate ===")
sk = V["SKEW"]
for chg in [1, 5, 10, 21]:
    for q in [0.90, 0.95, 0.98]:
        d = sk.diff(chg)
        thr = d.quantile(q)
        gate = (d < thr).astype(float)
        rec("B_SKEW", f"trim_chg{chg}_q{q}", SPY_POS * gate.reindex(R.index).fillna(1.0))
        rec("B_SKEW", f"flip_chg{chg}_q{q}", SPY_POS * (2 * gate - 1).reindex(R.index).fillna(0.0))
for win in [20, 60, 120]:
    for thr in [1.0, 1.5, 2.0]:
        zz = z(sk, win)
        gate = (zz < thr).astype(float)
        rec("B_SKEW", f"trim_z{win}_thr{thr}", SPY_POS * gate.reindex(R.index).fillna(1.0))

# =====================================================================
# (c) VIX9D/VIX3M/VIX6M short-end term structure 2-3 window
# =====================================================================
print("=== (c) term structure ===")
ts_pairs = [("VIX9D", "VIX3M"), ("VIX9D", "VIX6M"), ("VIX3M", "VIX6M"), ("VIX", "VIX3M")]
for a, b in ts_pairs:
    ratio = (V[a] / V[b]).reindex(R.index)
    for ma in [5, 10, 21]:
        s = ratio.rolling(ma).mean()
        pos = np.sign(1.0 - s).reindex(R.index).fillna(0.0)  # contango(s<1) -> long
        rec("C_TS", f"{a}{b}_ma{ma}_sign", pos)
        pos2 = (1.0 - s).clip(-1, 1).reindex(R.index).fillna(0.0)  # linear in slope
        rec("C_TS", f"{a}{b}_ma{ma}_lin", pos2)
    # 2-window z of the ratio
    for win in [21, 63]:
        zz = z(ratio, win)
        pos = (-zz).clip(-1, 1).reindex(R.index).fillna(0.0)
        rec("C_TS", f"{a}{b}_z{win}_neg", pos)

# =====================================================================
# (d) GVZ / OVX asset-specific vol-timing overlays on GLD / USO(->XOP proxy oil eq)
# =====================================================================
print("=== (d) GVZ/OVX ===")
for volname, etf, tag in [("GVZ", "GLD", "GOLD"), ("OVX", "USO", "OIL")]:
    # RVX/RUT dropped: no RUT/IWM close series anywhere in tools/quant/data (checked
    # more_etf, twelve_liq, twelve_big, polygon, newdata) - honest data gap.
    try:
        er = L.etf_ret(etf)
    except Exception:
        continue
    er = er[er.index >= START]
    vv2 = V[volname].reindex(er.index)
    base = pd.Series(1.0, index=er.index)
    for win in [20, 60]:
        for thr in [0.5, 1.0, 1.5]:
            zz = z(vv2, win)
            gate = (zz < thr).astype(float)
            rec(f"D_{tag}", f"{volname}trim_z{win}_thr{thr}", base * gate.fillna(1.0), ret=er)
    for win in [10, 21, 63]:
        pos = np.sign(vv2.pct_change(win)).reindex(er.index).fillna(0.0)
        rec(f"D_{tag}", f"{volname}mom{win}_sign", pos, ret=er)

# =====================================================================
# (e) cross-asset vol ratio relative value: long asset whose vol cheap vs other
# =====================================================================
print("=== (e) cross-vol ratio ===")
for num, den, longetf, shortetf, tag in [
    ("GVZ", "VIX", "GLD", "SPY", "GOLDvsSPX"),
    ("OVX", "VIX", "USO", "SPY", "OILvsSPX"),
    ("GVZ", "OVX", "GLD", "USO", "GOLDvsOIL"),
]:
    er_l = L.etf_ret(longetf); er_s = L.etf_ret(shortetf)
    er_l = er_l[er_l.index >= START]; er_s = er_s[er_s.index >= START]
    ratio = (V[num] / V[den])
    for ma in [10, 21, 63]:
        s = (ratio / ratio.rolling(ma).mean() - 1.0).reindex(er_l.index)
        # ratio rich vs its MA -> num-side vol expensive -> short num asset
        pos = (-np.sign(s)).reindex(er_l.index).fillna(0.0)
        j = pd.concat([er_l, er_s], axis=1, join="inner").dropna()
        ret_ls = j.iloc[:, 0].fillna(0) - j.iloc[:, 1].fillna(0)
        rec(f"E_XVOL_{tag}", f"{num}{den}_ma{ma}", pos, ret=ret_ls.reindex(pos.index).fillna(0.0))

print(f"\ntotal variants: {len(rows)}")
# ---------------- summary table ----------------
print("\n==== SUMMARY (sorted by SR) ====")
summ = []
for r_ in rows:
    s = L.stats(r_["net"])
    ok = r_["ok"]
    summ.append((s["sr"], r_["family"], r_["variant"], s["ann"], s["neg_yr"], s["n_yr"],
                 s["worst"], s["h1"], s["h2"], ok["f_corr"]))
summ.sort(reverse=True)
for sr, fam, var, ann, ny, nyr, worst, h1, h2, cc in summ[:40]:
    print(f"SR={sr:6.2f} ann={ann:7.2f}% negyr={ny}/{nyr} worst={worst:6.1f}% H1={h1:5.2f} H2={h2:5.2f} corr={cc:+.2f}  {fam}|{var}")
print("\n---- FULL GATE DETAIL for top 15 ----")
for sr, fam, var, *_ in summ[:15]:
    for r_ in rows:
        if r_["family"] == fam and r_["variant"] == var:
            print(r_["line"])
            break

json.dump([[sr, fam, var] for sr, fam, var, *_ in summ[:25]],
          open("/tmp/vol2_scan_top.json", "w"))

# full table dump for honest per-family reporting (not just top-40 print)
import csv
with open("/tmp/vol2_scan_full.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["family", "variant", "SR", "ann", "vol", "negyr", "n_yr", "worst",
                "H1", "H2", "scram_p", "corrChamp", "corrLibMax"])
    for r_ in sorted(rows, key=lambda x: -L.stats(x["net"])["sr"]):
        s = L.stats(r_["net"]); ok = r_["ok"]
        sp = L.scramble_p(r_["pos"], r_.get("ret", R), n=200, seed=7) if "pos" in r_ else float("nan")
        cc = L.corr_champ(r_["net"]); cl = L.corr_library(r_["net"])["maxabs"]
        w.writerow([r_["family"], r_["variant"], round(s["sr"], 3), round(s["ann"], 2),
                    round(s["vol"], 2), s["neg_yr"], s["n_yr"], round(s["worst"], 2),
                    round(s["h1"], 2), round(s["h2"], 2),
                    None if sp != sp else round(sp, 3), round(cc, 3), round(cl, 3)])
print("\nfull table -> /tmp/vol2_scan_full.csv")
