"""HUNT_VOL2 ROUND 6 (a): FRAUD-CATCH cross-verification of HUNT_MACRO2's R5 verdicts.

Charter: "reproduce HUNT_MACRO2's R5 verdicts from published artifacts with your OWN code.
Mismatch -> escalate."

Independence rules followed here:
  - NO import of any HUNT_MACRO2 module (round2/round4/round5). Everything below is
    re-implemented from their PUBLISHED descriptions (FINDINGS.md table + code docstrings
    quoted in their round5 script, which is itself a published artifact).
  - Metrics (ann_geo / sharpe / max_dd / neg_years / halves) are my own implementations.
  - The ONLY shared imports are: rawew13v2_build (the harness champion builder, needed to
    reconstruct the slot frame Wg their slot-overlay REGROT variant acts on) and
    bt.gates.run for the V2 section-6 leak probe (the ratified instrument, invoked with
    explicit sig= and leak_check=True per contract).

Published claims under test (HUNT_MACRO2 FINDINGS.md R5 + r5_overlay_results.csv 37 rows
+ r5_leak_probe.json):
  C1 champion 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg / n=4805; rebuild dev ~1e-16.
  C2 fetch_summary.json sha16s match the data files on disk.
  C3 trigger on-frequencies: DEFLev 11.88%, DEFLev2 12.76%, DEFLev3 2.33%, REGROT 97.8%.
  C4 x0.6 book deltas: DEFLev dAnn -1.781pp dMDD +0.000 dSR -0.079; DEFLev2 -0.973pp /
     +0.000 / -0.019; DEFLev3 -0.200pp / +0.000 / +0.005; REGROT -0.020pp / -0.001 / -0.0009.
  C5 controls at matched freq get HIGHER max-dSR: +0.271 / +0.294 / +0.309.
  C6 era-splits at x0.6: DEFLev -0.0393/+0.0000/-0.1897; DEFLev2 -0.0393/+0.0000/-0.0543;
     DEFLev3 +0.0000/+0.0000/-0.0027; REGROT -0.0022/+0.0007/-0.0042.
     (INTERNAL-CONSISTENCY RED FLAG found by inspection pre-run: DEFLev vs DEFLev2 rows
     share byte-identical dSR_H1/dSR_H2 in the CSV but DIFFER in era 2020-26, and
     H1-union-H2 covers every row -> at least one column of the published CSV must be
     wrong. This run decides which.)
  C7 mechanism: dd window 2018-06-19..25; in-window CPI yoy 1.26 vs expanding-q85 3.84,
     GDP 1.82 vs q15 0.11, HICP 1.4; zero trigger days in window; 0/10 top-dd-day overlap.
  C8 DEFLev3 trigger confined to 2025-10-15..2026-08-27, 112 days.
  C9 leak probe: leak_ok=True, same_period_corr -0.0031, composite_pass False.

Run: python3 fraudcatch_macro2_r5.py
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import rawew13v2_build as rb  # noqa: E402  (shared harness builder, not MACRO2 code)

ROOT = "/Users/daxu/software/world-trader"
M2 = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r5"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r6"

GEAR, RATE, BPS = 1.6, 0.045, 6.4
MARGIN_CONST = (GEAR - 1.0) * RATE / 252.0
CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SCALES = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
Q_HI, Q_LO = 0.85, 0.15
ERAS = [(2008, 2013), (2014, 2019), (2020, 2026)]
LAGS = {"hicp_yoy": 40, "cpi_us_m": 45, "ppi_m": 45, "gdp_yoy": 240, "cpi_us_y": 240}
RISK_ON = ["C5ng", "C5ngsum", "carryv2", "QAxasts", "dualmom", "diescrack", "CFX4"]

issues = []          # collected MISMATCHES -> escalate


def flag(cid, mine, theirs, tol):
    if isinstance(mine, str) or isinstance(theirs, str):
        ok = str(mine) == str(theirs)
    else:
        ok = (mine is not None and theirs is not None
              and abs(float(mine) - float(theirs)) <= tol)
    if not ok:
        issues.append((cid, mine, theirs))
    print(f"  [{'ok ' if ok else 'MISMATCH'}] {cid}: mine={mine} published={theirs}")
    return ok


# -------------------------------------------------------------- own metrics (no bt.metrics)
def ann_geo(r):
    prod = (1.0 + r).prod()
    return float(prod ** (252.0 / len(r)) - 1.0)


def sr_d(r):
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252.0))


def max_dd(r):
    eq = (1.0 + r).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def neg_years(r):
    return int((r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1) < 0).sum())


# -------------------------------------------------------------- own overlay algebra
def overlay_book(champ, m):
    """Book-level de-lever per the published R2 algebra (docstring, HUNT_MACRO2_round2.py):
    decision at close t scales P&L from t+1 (held=m.shift(1), first row starts invested),
    turnover on |d held| at full GEAR*BPS, margin re-charged on the OVERLAID gross."""
    m = pd.Series(m, index=champ.index).astype(float)
    held = m.shift(1)
    held.iloc[0] = m.iloc[0]
    dm = held.diff().abs()
    dm.iloc[0] = 0.0
    return (held * (champ + MARGIN_CONST)
            - dm * GEAR * BPS / 1e4
            - np.maximum(held * GEAR - 1.0, 0.0) * RATE / 252.0)


def apply_slot_overlay(Wg, df, M):
    """Slot-level overlay per the published algebra: Wo=M.shift(1)*Wg, full |dWo| turnover,
    margin on overlaid gross (no GEAR multiplier here, per the published formula)."""
    Mh = M.shift(1)
    Mh.iloc[0] = M.iloc[0]
    Wo = Mh * Wg
    port = (df.fillna(0).values * Wo.values).sum(axis=1)
    to = Wo.diff().abs().sum(axis=1).fillna(0.0)
    gross = Wo.abs().sum(axis=1)
    return pd.Series(port, index=Wg.index) - to * BPS / 1e4 \
        - np.maximum(gross - 1.0, 0.0) * RATE / 252.0


# -------------------------------------------------------------- own PIT panel builders
def _month_end(ym):
    return pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(0)


def pit_monthly(df, lag_days):
    idx = pd.to_datetime([_month_end(m) for m in df["period"]]) + pd.Timedelta(days=lag_days)
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").values, index=idx)
    return s[~s.index.duplicated(keep="last")].sort_index()


def pit_annual(df, lag_days):
    idx = pd.to_datetime([str(p) + "-12-31" for p in df["period"]]) + pd.Timedelta(days=lag_days)
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").values, index=idx)
    return s[~s.index.duplicated(keep="last")].sort_index()


def regime_panel(cal):
    cal = pd.DatetimeIndex(cal)
    out = pd.DataFrame(index=cal)

    hicp = pit_monthly(pd.read_csv(f"{M2}/data/eurostat_hicp_ea20_cp00_rch_a.csv"),
                       LAGS["hicp_yoy"])
    out["hicp_yoy"] = hicp.reindex(cal).ffill()

    cpi = pit_monthly(pd.read_csv(f"{M2}/data/bls_cusr0000sa0.csv"), LAGS["cpi_us_m"])
    out["cpi_us_m"] = (cpi / cpi.shift(12) - 1.0) * 100
    out["cpi_us_m"] = out["cpi_us_m"].reindex(cal).ffill()

    ppi = pit_monthly(pd.read_csv(f"{M2}/data/bls_wpsfd49207.csv"), LAGS["ppi_m"])
    out["ppi_m"] = (ppi / ppi.shift(12) - 1.0) * 100
    out["ppi_m"] = out["ppi_m"].reindex(cal).ffill()

    gdp = pit_annual(pd.read_csv(f"{M2}/data/worldbank_usa_gdp_growth.csv"), LAGS["gdp_yoy"])
    out["gdp_yoy"] = gdp.reindex(cal).ffill()

    cpiy = pit_annual(pd.read_csv(f"{M2}/data/worldbank_usa_cpi_annual.csv"), LAGS["cpi_us_y"])
    out["cpi_us_y"] = cpiy.reindex(cal).ffill()
    return out


def expanding_band_trigger(s, q, side, min_obs=252):
    qv = s.shift(1).expanding(min_periods=min_obs).quantile(q)
    return ((s > qv) if side == "hi" else (s < qv)).fillna(False)


def ownvol_trigger(r, win=21, qtarget=0.95):
    r = pd.Series(r).fillna(0.0)
    vol = r.rolling(win).std(ddof=1).shift(1)
    q = vol.expanding(min_periods=win).quantile(qtarget)
    return (vol > q).fillna(False)


def match_quantile_for_freq(r, win=21, target_freq=0.069, tol=0.003):
    for q in np.arange(0.999, 0.49, -0.001):
        if abs(ownvol_trigger(r, win=win, qtarget=float(q)).mean() - target_freq) <= tol:
            return float(q)
    raise RuntimeError(f"no quantile matches freq {target_freq} within {tol}")


# ================================================================ C2 data integrity
print("=== C2: data files vs published fetch_summary.json ===")
with open(f"{M2}/data/fetch_summary.json") as f:
    fetch = json.load(f)
for e in fetch:
    p = f"{M2}/data/{e['file']}"
    raw = open(p, "rb").read()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    nrows = len(pd.read_csv(p))
    ok = (sha16 == e["sha256_16"] and nrows == e["rows"])
    if not ok:
        issues.append(("C2", e["file"], f"sha/nrows {sha16}/{nrows} vs {e['sha256_16']}/{e['rows']}"))
    print(f"  [{'ok ' if ok else 'MISMATCH'}] {e['file']}: sha16 {sha16} rows {nrows}")

# ================================================================ C1 champion
print("\n=== C1: champion metrics from the published CSV (my own metric code) ===")
champ_pub = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
print(f"  n={len(champ_pub)} span {champ_pub.index.min().date()}..{champ_pub.index.max().date()}")
flag("C1 n", len(champ_pub), 4805, 0)
flag("C1 ann%", ann_geo(champ_pub) * 100, 37.1954, 5e-4)
flag("C1 SR", sr_d(champ_pub), 3.1810, 5e-4)
flag("C1 MDD%", max_dd(champ_pub) * 100, -6.6922, 5e-4)
flag("C1 neg_years", neg_years(champ_pub), 0, 0)

# ---- rebuild (shared harness builder + the published weight recipe, re-coded here)
df = pd.DataFrame({n: rb.load(rb.PATHS[n]).dropna() for n in rb.NAMES})
df = df[df.index >= "2008-03-31"]
isr = df[df.index < rb.IS_END]
SRv = pd.Series({n: rb.is_sr(isr[n]) for n in rb.NAMES})
relw = np.maximum(SRv, 0.0) ** rb.P
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(rb.NAMES)
Wg = d2 * (GEAR / len(rb.NAMES))
port = (df.fillna(0).values * Wg.values).sum(axis=1)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
net = pd.Series(port, index=df.index) - to * BPS / 1e4 - MARGIN_CONST
net = net.reindex(champ_pub.index)
dev = (net - champ_pub).abs().max()
print(f"  rebuild dev vs committed CSV: {dev:.3e}")
if dev > 1e-10:
    issues.append(("C1", "rebuild_dev", dev))
flag("C1 rebuild ann%", ann_geo(net.dropna()) * 100, 37.1954, 5e-4)
flag("C1 rebuild SR", sr_d(net.dropna()), 3.1810, 5e-4)

cal = champ_pub.index
champ = net.copy()

# ================================================================ C7 mechanism facts
print("\n=== C7: mechanism (dd window, covariates, trigger overlap) ===")
eq = (1 + champ).cumprod()
dd = eq / eq.cummax() - 1
peak_i = eq[: dd.idxmin()].idxmax()      # equity-curve peak preceding the trough
print(f"  max-dd {dd.min()*100:.4f}%  peak {peak_i.date()} -> trough {dd.idxmin().date()}")
flag("C7 dd peak", str(peak_i.date()), "2018-06-19", 0)
flag("C7 dd trough", str(dd.idxmin().date()), "2018-06-25", 0)
win_mask = (cal >= peak_i) & (cal <= dd.idxmin())

panel = regime_panel(cal)
q85_cpi = panel["cpi_us_y"].shift(1).expanding(min_periods=252).quantile(Q_HI)
q15_gdp = panel["gdp_yoy"].shift(1).expanding(min_periods=252).quantile(Q_LO)
q85_hicp = panel["hicp_yoy"].shift(1).expanding(min_periods=252).quantile(Q_HI)
j = cal[win_mask][-1]                    # covariate readout at the dd trough day
print(f"  in-window CPI yoy {panel['cpi_us_y'][j]:.2f} vs expanding q85 {q85_cpi[j]:.2f}")
print(f"  in-window GDP yoy {panel['gdp_yoy'][j]:.2f} vs expanding q15 {q15_gdp[j]:.2f}")
print(f"  in-window HICP yoy {panel['hicp_yoy'][j]:.2f} (q85 {q85_hicp[j]:.2f})")
flag("C7 cpi yoy", round(float(panel['cpi_us_y'][j]), 2), 1.26, 0.005)
flag("C7 cpi q85", round(float(q85_cpi[j]), 2), 3.84, 0.005)
flag("C7 gdp yoy", round(float(panel['gdp_yoy'][j]), 2), 1.82, 0.005)
flag("C7 gdp q15", round(float(q15_gdp[j]), 2), 0.11, 0.005)
flag("C7 hicp yoy", round(float(panel['hicp_yoy'][j]), 1), 1.4, 0.05)

# triggers (mine)
trig_deflev = (expanding_band_trigger(panel["cpi_us_y"], Q_HI, "hi")
               | expanding_band_trigger(panel["gdp_yoy"], Q_LO, "lo")).reindex(cal).fillna(False)
trig_deflev2 = (expanding_band_trigger(panel["hicp_yoy"], Q_HI, "hi")
                | expanding_band_trigger(panel["gdp_yoy"], Q_LO, "lo")).reindex(cal).fillna(False)
trig_deflev3 = expanding_band_trigger(panel["cpi_us_m"], Q_HI, "hi", min_obs=60) \
    .reindex(cal).fillna(False)

print(f"  trigger days in dd window: DEFLev {int(trig_deflev[win_mask].sum())}, "
      f"DEFLev2 {int(trig_deflev2[win_mask].sum())}, DEFLev3 {int(trig_deflev3[win_mask].sum())}")
if int(trig_deflev[win_mask].sum()) + int(trig_deflev2[win_mask].sum()) + int(trig_deflev3[win_mask].sum()):
    issues.append(("C7", "trigger-days-in-dd-window", "nonzero"))

top10 = champ.nsmallest(10).index
ov_overlap = sum(bool(trig_deflev[d]) or bool(trig_deflev2[d]) or bool(trig_deflev3[d])
                 for d in top10)
print(f"  top-10 worst champion days overlapped by ANY macro gate: {ov_overlap}/10")
flag("C7 top10 overlap", ov_overlap, 0, 0)

# C8 DEFLev3 span
on3 = trig_deflev3[trig_deflev3]
n3 = int(on3.sum())
print(f"  DEFLev3 span {on3.index.min().date()}..{on3.index.max().date()}, {n3} days")
flag("C8 deflev3 first", str(on3.index.min().date()), "2025-10-15", 0)
flag("C8 deflev3 last", str(on3.index.max().date()), "2026-08-27", 0)
flag("C8 deflev3 days", n3, 112, 0)

# ================================================================ C3/C4/C5/C6 grid
print("\n=== C3-C6: full 37-row grid reproduction (all 6 scales x 3 variants + controls + REGROT) ===")
their = pd.read_csv(f"{M2}/r5_overlay_results.csv")
print(f"  published rows: {len(their)}")
flag("C-grid rows", len(their), 37, 0)

net_rets = champ.diff().fillna(0.0)
variants = [
    ("DEFLev wb-cpi-hi | wb-gdp-lo", trig_deflev),
    ("DEFLev2 hicp-hi | wb-gdp-lo", trig_deflev2),
    ("DEFLev3 bls-cpi-hi (2024+ span)", trig_deflev3),
]
mid = cal[len(cal) // 2]
H1, H2 = cal[: len(cal) // 2], cal[cal.get_loc(mid):]


def sr_on(r, idx):
    x = r[idx]
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252.0))


grid_rows = []
for name, trig in variants:
    freq = float(trig.mean())
    qm = match_quantile_for_freq(net_rets, win=21, target_freq=freq, tol=0.003)
    ctrl = ownvol_trigger(net_rets, win=21, qtarget=qm)
    for label, t in [(name + " [ownvol control matched]", ctrl), (name, trig)]:
        for sc in SCALES:
            m = pd.Series(1.0, index=cal)
            m[t.reindex(cal).fillna(False).values] = sc
            ov = overlay_book(champ, m).dropna()
            ovc = champ  # baseline series for deltas
            d_ann = ann_geo(ov) - ann_geo(champ.dropna())
            d_mdd = max_dd(ov) - max_dd(champ.dropna())
            d_sr = sr_d(ov) - sr_d(champ.dropna())
            h1 = sr_on(ov, H1) - sr_on(champ.dropna(), H1)
            h2 = sr_on(ov, H2) - sr_on(champ.dropna(), H2)
            es = {}
            for y0, y1 in ERAS:
                j2 = cal[(cal.year >= y0) & (cal.year <= y1)]
                es[f"{y0}_{y1}"] = sr_on(ov, j2) - sr_on(champ.dropna(), j2)
            grid_rows.append(dict(name=label, scale=sc, on_freq=float(t.mean()),
                                  d_ann=d_ann, d_mdd=d_mdd, dSR=d_sr,
                                  dSR_H1=h1, dSR_H2=h2, **{f"era_{k}": v for k, v in es.items()},
                                  neg=neg_years(ov), control="control" in label))

mine = pd.DataFrame(grid_rows)

# compare against published rows
print("\n  per-cell max-abs-diff vs published CSV (name+scale keyed):")
tcol = {"on_freq": "on_freq", "d_ann": "d_ann", "d_mdd": "d_mdd", "dSR": "dSR",
        "dSR_H1": "dSR_H1", "dSR_H2": "dSR_H2", "era_2008_2013": "era_dSR_2008_2013",
        "era_2014_2019": "era_dSR_2014_2019", "era_2020_2026": "era_dSR_2020_2026"}
worst = {}
for _, r in mine.iterrows():
    sel = their[(their["name"] == r["name"]) & (their["scale"] == r["scale"])]
    if len(sel) != 1:
        issues.append(("C-grid", f"{r['name']} s={r['scale']}", f"match count {len(sel)}"))
        continue
    t = sel.iloc[0]
    for mc, tc in tcol.items():
        d = abs(float(r[mc]) - float(t[tc]))
        worst[tc] = max(worst.get(tc, 0.0), d)
        if d > 1e-6:
            issues.append(("C-grid", f"{r['name']} s={r['scale']} {tc}",
                           f"mine={float(r[mc]):.6g} theirs={float(t[tc]):.6g}"))
    if int(r["neg"]) != int(t["neg"]):
        issues.append(("C-grid", f"{r['name']} s={r['scale']} neg", f"{r['neg']} vs {t['neg']}"))
for k, v in sorted(worst.items()):
    print(f"    {k:22s} max|diff| = {v:.3e}")

# C3 on-frequencies (published table)
print("\n  C3 on-frequencies:")
for nm, key, tf in [("DEFLev", trig_deflev, 11.88), ("DEFLev2", trig_deflev2, 12.76),
                    ("DEFLev3", trig_deflev3, 2.33)]:
    flag(f"C3 {nm} on-freq%", float(key.mean()) * 100, tf, 0.005)

# C4 x0.6 headline deltas
print("\n  C4 x0.6 headline deltas (dAnn pp / dMDD pp / dSR):")
pub_c4 = {("DEFLev wb-cpi-hi | wb-gdp-lo", False): (-1.781, 0.000, -0.079),
          ("DEFLev2 hicp-hi | wb-gdp-lo", False): (-0.973, 0.000, -0.019),
          ("DEFLev3 bls-cpi-hi (2024+ span)", False): (-0.200, 0.000, 0.005)}
for (nm, ctl), (pa, pm, ps) in pub_c4.items():
    r = mine[(mine["name"] == nm) & (mine["scale"] == 0.6) & (mine["control"] == ctl)].iloc[0]
    flag(f"C4 {nm} dAnn pp", round(r["d_ann"] * 100, 3), pa, 0.0015)
    flag(f"C4 {nm} dMDD pp", round(r["d_mdd"] * 100, 3), pm, 0.0005)
    flag(f"C4 {nm} dSR", round(r["dSR"], 4), ps, 0.0015)

# C5 control max dSR across scales
print("\n  C5 controls max dSR across scales:")
pub_c5 = {"DEFLev wb-cpi-hi | wb-gdp-lo": 0.271, "DEFLev2 hicp-hi | wb-gdp-lo": 0.294,
          "DEFLev3 bls-cpi-hi (2024+ span)": 0.309}
for nm, pv in pub_c5.items():
    r = mine[(mine["name"] == nm + " [ownvol control matched]") & (mine["control"])]
    flag(f"C5 {nm} ctrl max dSR", round(float(r["dSR"].max()), 3), pv, 0.0015)

# C6 era-splits x0.6
print("\n  C6 x0.6 era-splits (2008-13 / 2014-19 / 2020-26):")
pub_c6 = {("DEFLev wb-cpi-hi | wb-gdp-lo", False): (-0.0393, 0.0000, -0.1897),
          ("DEFLev2 hicp-hi | wb-gdp-lo", False): (-0.0393, 0.0000, -0.0543),
          ("DEFLev3 bls-cpi-hi (2024+ span)", False): (0.0000, 0.0000, -0.0027)}
for (nm, ctl), (e1, e2, e3) in pub_c6.items():
    r = mine[(mine["name"] == nm) & (mine["scale"] == 0.6) & (mine["control"] == ctl)].iloc[0]
    flag(f"C6 {nm} era1", round(r["era_2008_2013"], 4), e1, 0.0006)
    flag(f"C6 {nm} era2", round(r["era_2014_2019"], 4), e2, 0.0006)
    flag(f"C6 {nm} era3", round(r["era_2020_2026"], 4), e3, 0.0006)

# ================================================================ REGROT
print("\n=== REGROT (slot-level rotation) ===")
med = panel["cpi_us_y"].shift(1).expanding(min_periods=252).median()
v = panel["cpi_us_y"].reindex(cal)
sgn = pd.Series(0.0, index=cal)
sgn[v < med.reindex(cal)] = 1.0
sgn[v > med.reindex(cal)] = -1.0
sgn = sgn.fillna(0.0)
M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
up = (sgn > 0).reindex(Wg.index).fillna(False)
dn = (sgn < 0).reindex(Wg.index).fillna(False)
for c in RISK_ON:
    M.loc[up, c] = 1.05
    M.loc[dn, c] = 0.95
ovr = apply_slot_overlay(Wg, df, M).dropna()
d_ann_r = ann_geo(ovr) - ann_geo(champ.dropna())
d_mdd_r = max_dd(ovr) - max_dd(champ.dropna())
d_sr_r = sr_d(ovr) - sr_d(champ.dropna())
print(f"  REGROT dAnn={d_ann_r*100:+.4f}pp dMDD={d_mdd_r*100:+.4f}pp dSR={d_sr_r:+.5f} "
      f"neg={neg_years(ovr)} sign-on-freq={float((sgn != 0).mean()) * 100:.1f}%")
flag("C4 REGROT dAnn pp", round(d_ann_r * 100, 3), -0.020, 0.0015)
flag("C4 REGROT dMDD pp", round(d_mdd_r * 100, 3), -0.001, 0.0005)
flag("C4 REGROT dSR", round(d_sr_r, 4), -0.0009, 0.0015)
t = thei = their[their["name"].str.startswith("REGROT")].iloc[0]
for mc, tc in tcol.items():
    mv = {"d_ann": d_ann_r, "d_mdd": d_mdd_r, "dSR": d_sr_r}.get(mc)
    if mv is not None and abs(float(mv) - float(t[tc])) > 1e-6:
        issues.append(("REGROT", tc, f"mine={mv:.6g} theirs={float(t[tc]):.6g}"))

# ================================================================ C9 leak probe
print("\n=== C9: V2 section-6 leak probe on the champion book (explicit sig=, leak_check=True) ===")
from bt import gates  # noqa: E402
lg = gates.run(champ, sig=Wg.sum(axis=1), leak_check=True)
lk = lg.get("leak") or {}
print(f"  leak_ok={lg.get('leak_ok')} corr={lk.get('same_period_corr')} "
      f"composite_pass={lg.get('pass')}")
flag("C9 leak_ok", int(bool(lg.get("leak_ok"))), 1, 0)
flag("C9 same_period_corr", round(float(lk.get("same_period_corr")), 4), -0.0031, 0.0005)
with open(f"{OUT}/r6_macro2_leakprobe.json", "w") as f:
    json.dump({k: lg.get(k) for k in ("leak_ok", "leak", "pass")}, f, indent=1, default=str)

# ================================================================ verdict
print("\n=== VERDICT ===")
mine.to_csv(f"{OUT}/r6_macro2_repro_grid.csv", index=False)
print(f"  saved {OUT}/r6_macro2_repro_grid.csv ({len(mine)} rows)")
print(f"  my x0.6 DEFLev  H2={mine[(mine.name.str.startswith('DEFLev ')) & (mine.scale == 0.6) & (~mine.control)].iloc[0]['dSR_H2']:+.6f} "
      f"era3={mine[(mine.name.str.startswith('DEFLev ')) & (mine.scale == 0.6) & (~mine.control)].iloc[0]['era_2020_2026']:+.6f}")
print(f"  my x0.6 DEFLev2 H2={mine[(mine.name.str.startswith('DEFLev2')) & (mine.scale == 0.6) & (~mine.control)].iloc[0]['dSR_H2']:+.6f} "
      f"era3={mine[(mine.name.str.startswith('DEFLev2')) & (mine.scale == 0.6) & (~mine.control)].iloc[0]['era_2020_2026']:+.6f}")
if issues:
    print(f"  ESCALATE: {len(issues)} mismatch(es):")
    for cid, a, b in issues:
        print(f"    - [{cid}] {a} | {b}")
    print("FRAUD-CATCH VERDICT: MISMATCH -> ESCALATE")
else:
    print("FRAUD-CATCH VERDICT: REPRODUCED (all checks within tolerance)")
