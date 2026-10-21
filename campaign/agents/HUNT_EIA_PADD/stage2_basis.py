#!/usr/bin/env python3
"""STAGE 2 — the mechanism-faithful constructions from AUDIT_R7REDO R8 7c:
regional storage dysregulation traded as LOCATIONAL BASIS, not outright.

Pre-registered engines (chosen from mechanism, before looking at results):
  E1  PADD2 (Cushing) crude deviation  -> WTI - BRENT spread   (glut => WTI discount)
  E2  PADD1a distillate deviation      -> ULSD_NYH - ULSD_GULF basis (EC draw => premium)
  E3  PADD1a gasoline deviation        -> GAS_NYH - GAS_GULF basis
  E4  relative (p1a - p3) deviation    -> each basis (cross-sectional version)
  E5  cross-sec dispersion of all PADDs (uncertainty/regime) -> outright vol-of-basis

PIT: weekly stamp Fri; print Wed 10:30 ET; signal available +5d (Thu); position from
next business day; 6.4bps full |dW| on the basis book; IS (<2017) selection only.
"""
import pandas as pd, numpy as np

D = "tools/quant/data/eia_weekly"
IS_END = pd.Timestamp("2017-01-01")

def load(name):
    s = pd.read_csv(f"{D}/{name}.csv", parse_dates=["date"]).set_index("date")["value"]
    return s[~s.index.duplicated(keep="last")].astype(float).sort_index()

PADD = ["p1a","p2","p3","p4","p5"]
CRUDE = {a: load(f"petstk_{a}_wcestp{a[1:].replace('1a','1')}1") for a in PADD}
DIST  = {a: load(f"petstk_{a}_wdistp{a[1:].replace('1a','1')}1") for a in PADD}
GAS   = {a: load({"p1a":"petstk_p1a_w_epm0f_sae_r10_mbbl","p2":"petstk_p2_w_epm0f_sae_r20_mbbl",
                  "p3":"petstk_p3_w_epm0f_sae_r30_mbbl","p4":"petstk_p4_w_epm0f_sae_r40_mbbl",
                  "p5":"petstk_p5_w_epm0f_sae_r50_mbbl"}[a]) for a in PADD}

wti, brent = load("wti_spot_daily"), load("brent_spot_daily")
ho_ny, ho_glf = load("ulsd_nyh_spot_daily"), load("ulsd_gulf_spot_daily")
rb_ny, rb_glf = load("gasoline_nyh_spot_daily"), load("gasoline_gulf_spot_daily")

def seasonal_dev(stock, years=5):
    """Robust seasonal deviation (vs trailing 5y same-ISO-week median), no lookahead."""
    vals = stock.values; dates = stock.index
    week = pd.Index(dates).isocalendar().week.astype(int).values
    out = np.full(len(vals), np.nan)
    for i in range(len(vals)):
        lo = dates[i] - pd.DateOffset(years=years)
        mask = (dates < dates[i]) & (dates >= lo) & np.isin(week, [week[i]-1, week[i], week[i]+1])
        if mask.sum() >= 6:
            h = vals[mask]; med = np.median(h)
            out[i] = (vals[i] - med) / (np.median(np.abs(h - med)) + 1e-9)
    return pd.Series(out, index=dates)

print("computing seasonal deviations (5 PADDs x 3 products)...")
DEV = {"crude": {a: seasonal_dev(CRUDE[a]) for a in PADD},
       "dist":  {a: seasonal_dev(DIST[a]) for a in PADD},
       "gas":   {a: seasonal_dev(GAS[a]) for a in PADD}}

# ---- basis books (daily log-spread returns, both legs spot; basis = leg1 - leg2) ----
grid = pd.date_range("1992-01-01", "2026-09-01", freq="B")
def daily(x): return x.reindex(grid).ffill()
books = {
    "wti_brent":  (np.log(daily(wti)) - np.log(daily(brent))).diff(),
    "ho_ny_glf":  (np.log(daily(ho_ny)) - np.log(daily(ho_glf))).diff(),
    "rb_ny_glf":  (np.log(daily(rb_ny)) - np.log(daily(rb_glf))).diff(),
}

def to_avail(weekly_sig):
    """Weekly Fri stamp -> available next Thu (+5d), as-of onto daily grid."""
    a = weekly_sig.dropna().copy(); a.index = a.index + pd.Timedelta(days=5)
    return a.sort_index()

def engine(name, sig_w, book, dirn=+1, deadband=0.0):
    av = to_avail(sig_w)
    s = pd.Series([av.asof(t) if len(av) and not pd.isna(av.asof(t)) else np.nan for t in grid], index=grid)
    s = s.where(s.index >= (av.index[0] if len(av) else pd.Timestamp("2100-01-01")))
    if deadband > 0:
        pos = pd.Series(np.where(s > deadband, 1.0, np.where(s < -deadband, -1.0, 0.0)), index=grid)
    else:
        pos = np.sign(s)
    pos = pos.shift(1).fillna(0.0)  # T+1 on the daily grid
    r = books[book].reindex(grid).fillna(0.0)
    cost = pos.diff().abs().fillna(0.0) * 0.00064
    net = pos * r * dirn - cost
    return net

def sr_m(x):
    x = x.dropna()
    return x.mean()/x.std()*np.sqrt(12) if len(x) > 3 and x.std() > 0 else np.nan

rows = []
def test(name, net):
    m = net.resample("ME").sum()
    isr = m[m.index < IS_END]; osr = m[m.index >= IS_END]
    rows.append(dict(engine=name, IS_SR=sr_m(isr), OOS_SR=sr_m(osr)))
    print(f"{name:<44} IS_SR={sr_m(isr):7.3f}  OOS_SR={sr_m(osr):7.3f}")

# E1: PADD2 Cushing crude glut -> WTI-Brent (glut high => spread widens negative => short)
p2d = DEV["crude"]["p2"]
test("E1 p2 crude dev -> wti_brent, dir-1", engine("e1", p2d, "wti_brent", -1))
test("E1 p2 crude dev -> wti_brent, dir+1", engine("e1", p2d, "wti_brent", +1))
# E2: East Coast distillate tightness -> NYH-Gulf ULSD basis (draw => premium widens)
p1d = DEV["dist"]["p1a"]
test("E2 p1a dist dev -> ho_ny_glf, dir-1", engine("e2", p1d, "ho_ny_glf", -1))
test("E2 p1a dist dev -> ho_ny_glf, dir+1", engine("e2", p1d, "ho_ny_glf", +1))
# E3: East Coast gasoline tightness -> NYH-Gulf gasoline basis
p1g = DEV["gas"]["p1a"]
test("E3 p1a gas dev -> rb_ny_glf, dir-1", engine("e3", p1g, "rb_ny_glf", -1))
test("E3 p1a gas dev -> rb_ny_glf, dir+1", engine("e3", p1g, "rb_ny_glf", +1))
# E4: relative tightness EC vs Gulf
rel_dist = DEV["dist"]["p1a"] - DEV["dist"]["p3"]
test("E4 (p1a-p3) dist dev -> ho_ny_glf, dir-1", engine("e4", rel_dist, "ho_ny_glf", -1))
rel_gas = DEV["gas"]["p1a"] - DEV["gas"]["p3"]
test("E4 (p1a-p3) gas dev -> rb_ny_glf, dir-1", engine("e4", rel_gas, "rb_ny_glf", -1))
rel_crude = DEV["crude"]["p2"] - DEV["crude"]["p3"]
test("E4 (p2-p3) crude dev -> wti_brent, dir-1", engine("e4", rel_crude, "wti_brent", -1))
# E5: dispersion regime
disp_c = pd.DataFrame(DEV["crude"]).std(axis=1)
disp_d = pd.DataFrame(DEV["dist"]).std(axis=1)
test("E5 crude PADD dispersion -> wti_brent, dir+1", engine("e5", disp_c, "wti_brent", +1))
test("E5 crude PADD dispersion -> wti_brent, dir-1", engine("e5", disp_c, "wti_brent", -1))

res = pd.DataFrame(rows).sort_values("IS_SR", ascending=False)
res.to_csv("campaign/agents/HUNT_EIA_PADD/stage2_results.csv", index=False)
print("\nBEST IS_SR:", round(res.IS_SR.max(), 3), "| adoption bar: 1.0")
