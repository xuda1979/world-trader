"""HUNT_CRYPTO2 ROUND 6 (a) — independent cross-verification of HUNT_VOL2 R5.

Fraud-catch audit per charter. Reimplements the PCR-overlay arithmetic FROM SCRATCH
(no import of pcr5_lib / round5_scan) and compares against their published artifacts:
  work_r5/pcr_overlay_scan.csv (148 filtered), work_r5/pcr_overlay_scan_UNFILTERED_disclosure.csv (224).

Their claimed conventions, re-pinned from their lib source (read, not imported):
  win 2008-03-31..2019-10-07; covariate NaN -> hold champion; gate p = g.shift(1),
  p0 entry turn vs 1.0; net = p*r - 6.4e-4*1.6*|dp|; z = expanding causal minp 502 ddof 0;
  chg = diff(5); ann geo, sr sqrt(252)-on-daily, halves split len//2, neg_years calendar.
Verdict claims to test: 0/148 dAnn>0 (8c binding), best dAnn -0.429pp, unfiltered best
-0.404pp, 0/148 dSR>=0, best dSR -0.0032 (equity level>0.9 to=0.5), 148/148 leak_ok with
max |same_period_corr| 0.063, window n=3007, champ ann-in-window 36.22%.
"""
import hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
R5 = f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r6_out_must_not_exist"  # guard
VOL2 = f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r5"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
PCR = f"{ROOT}/tools/quant/data/cboe_pcr/pcr_covariates_SPY_daily.csv"
COST, GEAR = 6.4e-4, 1.6
WIN_LO, WIN_HI = "2008-03-31", "2019-10-07"
SERIES = ["pcr_total", "pcr_index", "pcr_equity", "pcr_spx", "pcr_etp", "pcr_vix"]
LEVEL_THR = {"pcr_total": [0.75, 0.85, 0.95, 1.05], "pcr_index": [1.0, 1.2, 1.4],
             "pcr_equity": [0.6, 0.7, 0.8, 0.9], "pcr_spx": [1.3, 1.5, 1.7],
             "pcr_etp": [1.0, 1.3, 1.6], "pcr_vix": [0.3, 0.4, 0.5]}
Z_THR, CHG_THR, TO_LIST = [1.0, 1.5, 2.0], [0.05, 0.10, 0.15], [0.0, 0.5]
MIN_TRIG, MAX_TRIG = 0.01, 0.60


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


ch = pd.read_csv(CHAMP, parse_dates=["date"]).set_index("date")["ret"]
cov = pd.read_csv(PCR, parse_dates=["date"]).set_index("date").sort_index()
print("champ sha16", sha16(CHAMP), "pcr sha16", sha16(PCR))
cw = ch.loc[WIN_LO:WIN_HI]
print("window n =", len(cw), "champ ann_in_win (geo) = %.2f%%" %
      ((np.prod(1 + cw) ** (252 / len(cw)) - 1) * 100))


def ann_geo(x):
    x = x.dropna()
    return np.prod(1 + x) ** (252 / len(x)) - 1


def sr(x):
    x = x.dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(252)


def mdd(x):
    x = x.dropna()
    nav = (1 + x).cumprod()
    return (nav / nav.cummax() - 1).min()


def halves(x):
    x = x.dropna()
    k = len(x) // 2
    return sr(x.iloc[:k]), sr(x.iloc[k:])


def neg_years(x):
    x = x.dropna()
    y = (1 + x).groupby(x.index.year).prod() - 1
    return int((y < 0).sum()), float(y.min())


def gate(series, kind, op, thr, to):
    if kind == "level":
        x = series
    elif kind == "z":
        m = series.expanding(min_periods=502).mean()
        sd = series.expanding(min_periods=502).std(ddof=0)
        x = (series - m) / sd.replace(0.0, np.nan)
    elif kind == "chg":
        x = series.diff(5)
    else:
        raise ValueError(kind)
    trig = (x > thr) if op == "gt" else (x < thr)
    g = pd.Series(np.where(trig, to, 1.0), index=series.index)
    g[x.isna()] = np.nan
    return g


def overlay_net(g, r):
    gg = g.reindex(r.index).fillna(1.0)
    p = gg.shift(1).fillna(1.0)
    dp = p.diff().abs()
    if len(p):
        dp.iloc[0] = abs(p.iloc[0] - 1.0)
    return p * r.fillna(0.0) - dp * COST * GEAR


def variants():
    out = []
    for s in SERIES:
        for k in ["level", "z", "chg"]:
            thrs = LEVEL_THR[s] if k == "level" else (Z_THR if k == "z" else CHG_THR)
            for op in ["gt", "lt"]:
                for thr in thrs:
                    for to in TO_LIST:
                        out.append((s, k, op, thr, to))
    return out


rows = []
for v in variants():
    s, k, op, thr, to = v
    w = cov[[s]].reindex(cw.index)[s]
    g = gate(w, k, op, thr, to)
    freq = float((g.fillna(1.0) == to).mean())
    kept = MIN_TRIG <= freq <= MAX_TRIG
    net = overlay_net(g, cw)
    h1, h2 = halves(net)
    ny, wy = neg_years(net)
    # leak probe: same-period corr of held positions vs same-day champ ret
    sig = g.fillna(1.0).shift(1).fillna(1.0)
    both = pd.concat([sig, cw], axis=1).dropna()
    lc = float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])
    rows.append(dict(series=s, kind=k, op=op, thr=thr, to=to, freq=freq, kept=kept,
                     d_ann=(ann_geo(net) - ann_geo(cw)) * 100, d_sr=sr(net) - sr(cw),
                     d_mdd=(mdd(net) - mdd(cw)) * 100, d_h1=h1 - halves(cw)[0],
                     d_h2=h2 - halves(cw)[1], neg_yrs_net=ny, worst=wy * 100,
                     leak_corr=lc))
mine = pd.DataFrame(rows)
print("\nvariants declared:", len(mine), " kept in [1%,60%]:", int(mine.kept.sum()))

for name, sub in [("FILTERED(148)", mine[mine.kept]), ("UNFILTERED(224)", mine)]:
    best = sub.loc[sub.d_ann.idxmax()]
    bestdsr = sub.loc[sub.d_sr.idxmax()]
    print(f"{name}: n={len(sub)}  dAnn>0: {int((sub.d_ann > 0).sum())}/{len(sub)}"
          f"  best dAnn {best.d_ann:+.3f}pp [{best.series} {best.kind} {best.op}"
          f" thr={best.thr} to={best.to}]"
          f"  dSR>=0: {int((sub.d_sr >= 0).sum())}/{len(sub)}"
          f"  best dSR {bestdsr.d_sr:+.4f} [{bestdsr.series} {bestdsr.kind}"
          f" {bestdsr.op} thr={bestdsr.thr} to={bestdsr.to}]"
          f"  max|leak_corr| {sub.leak_corr.abs().max():.4f}")

# row-by-row match vs their published FILTERED csv
theirs = pd.read_csv(f"{VOL2}/pcr_overlay_scan.csv")
m = mine[mine.kept].merge(theirs, on=["series", "kind", "op", "thr", "to"],
                          suffixes=("_mine", "_theirs"))
print("\nmerged rows:", len(m), "(theirs had", len(theirs), ")")
for col in ["freq", "d_ann", "d_sr", "d_mdd", "d_h1", "d_h2"]:
    d = (m[f"{col}_mine"] - m[f"{col}_theirs"]).abs()
    print(f"  max|d {col}| = {d.max():.6g}   rows>tol: {int((d > (1e-6 if col=='freq' else 5e-4)).sum())}")
for col in ["neg_yrs_net"]:
    print(f"  neg_yrs mismatch rows: {int((m.neg_yrs_net_mine != m.neg_yrs_net_theirs).sum())}")
lk = m.leak_corr_mine.abs().sub(m.leak_corr_theirs.abs()).abs()
print(f"  max|leak_corr diff| = {lk.max():.6g}  theirs max {m.leak_corr_theirs.abs().max():.4f}"
      f"  mine max {m.leak_corr_mine.abs().max():.4f}")

# --- placebo (§8h analogue) reproduction, own code, same stated design ----------
def placebo(g, to, n=200, seed=0):
    rng = np.random.default_rng(seed)
    idx = cw.index
    m_ = len(idx)
    flat = (g.fillna(1.0) == to).values
    eps, run = [], 0
    for f in flat:
        if f:
            run += 1
        elif run:
            eps.append(run); run = 0
    if run:
        eps.append(run)
    eps = np.array(eps)
    base = sr(cw)
    dsr = np.empty(n)
    for j in range(n):
        g2 = pd.Series(1.0, index=idx)
        pos = 0
        while pos < m_:
            ln = int(eps[rng.integers(0, len(eps))])
            if pos + ln <= m_:
                g2.iloc[pos:pos + ln] = to
            pos += ln + int(rng.integers(1, 8))
        dsr[j] = sr(overlay_net(g2, cw)) - base
    real = sr(overlay_net(g, cw)) - base
    return real, dsr

for label, (s_, k_, op_, thr_, to_) in [
        ("pcr_vix z>2.0 to=0.5", ("pcr_vix", "z", "gt", 2.0, 0.5)),
        ("pcr_equity level>0.9 to=0.5", ("pcr_equity", "level", "gt", 0.9, 0.5))]:
    w = cov[[s_]].reindex(cw.index)[s_]
    g = gate(w, k_, op_, thr_, to_)
    real, dsr = placebo(g, to_)
    print(f"placebo {label}: real dSR {real:+.4f}  null median {np.median(dsr):+.4f}"
          f"  p95 {np.percentile(dsr, 95):+.4f}  frac_pos {(dsr > 0).mean():.3f}"
          f"  z {(real - np.median(dsr)) / dsr.std(ddof=1):+.2f}")
# unfiltered disclosure csv
theirs_u = pd.read_csv(f"{VOL2}/pcr_overlay_scan_UNFILTERED_disclosure.csv")
print("unfiltered csv rows:", len(theirs_u),
      "their max d_ann:", theirs_u.d_ann.max(),
      "| n d_ann>0:", int((theirs_u.d_ann > 0).sum()))
mine.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r6/vol2_own_recompute.csv",
            index=False)
print("\nsaved own recompute.")
