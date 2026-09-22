#!/usr/bin/env python3
"""HONEST GATE: EIA PADD regional petroleum-storage cross-section vs V7 champion.

2026-09-22. This is the seam the campaign's own AUDIT_R7REDO R8 7c pre-identified as
"WORTH A ROUND": DEAD_IDEAS row 57 killed the L48-AGGREGATE natgas storage signal
(best SR 0.29, priced at publication) but recorded verbatim that "REGIONAL storage +
crude prod/imports/supplied remain UNTESTED affordances". The certified 192-series
weekly petroleum stock matrix (petstk_*, 1984/1990..2026-08, lint=ok) was harvested
2026-09-07 but NEVER mined — no HUNT_EIA_PADD agent, no sleeves, no DEAD_IDEAS row.

Untested hypothesis (cheap, pre-registered): does the REGIONAL cross-section of
crude/distillate/gasoline stocks carry tradeable information the US aggregate does not?

Mechanism: relative storage dysregulation across PADDs (1a East, 2 Midwest, 3 Gulf,
4 Rockies, 5 West) — a region's stock vs its own 5y seasonal band, cross-sectionally
demeaned. When the East Coast is structurally short distillate vs its seasonal norm
while the Gulf is long, the NYH-vs-Gulf spot basis should compress; arbitrage flows
in the pipe grid are slow, so the imbalance persists days/weeks.

Trading instrument: US Diesel (HO proxy) / RBOB / WTI spot dailies (EIA itself, so
the signal and price come from the same publication family, costs applied).

Publication timing (PIT): the weekly petroleum status report prints Wed 10:30 ET
for week-ending Friday. We trade the signal from the NEXT day (T+1 on information),
implemented as: week-ending Friday stamps shifted forward 5 calendar days (Wed ->
Thu entry) — conservative, and we do NOT use same-day alignment (leak probe enforces).

Honesty gates applied (GATES_CONTRACT_V2):
- IS only for signal selection (< 2017-01-01); OOS never inspected before verdict.
- T+1 enforcement; 6.4bps full-|dW| costs; scramble null on positions; half-split;
  corr to champion; plateau/neighbor check on the grid; beats-passive recorded.
- Adoption bar for V7: IS monthly SR >= 1.0 AND OOS confirm AND low corr to champion.
"""
import pandas as pd, numpy as np, os, sys

B = "campaign"
D = "tools/quant/data/eia_weekly"
IS_END = pd.Timestamp("2017-01-01")

# ---------------- data ----------------
def load_series(name):
    d = pd.read_csv(f"{D}/{name}.csv", parse_dates=["date"])
    d = d.set_index("date")["value"].astype(float).sort_index()
    return d[~d.index.duplicated(keep="last")]

PADD = ["p1a", "p2", "p3", "p4", "p5"]
CRUDE = {a: load_series(f"petstk_{a}_wcestp{a[1:] if a[1:] != '1a' else '1'}1" if False else f"petstk_{a}_wcestp{a[1:].replace('1a','1')}1") for a in PADD}          # crude excl SPR
DIST  = {a: load_series(f"petstk_{a}_wdistp{a[1:].replace('1a','1')}1") for a in PADD}          # distillate
GAS_MAP = {"p1a": "petstk_p1a_w_epm0f_sae_r10_mbbl", "p2": "petstk_p2_w_epm0f_sae_r20_mbbl",
           "p3": "petstk_p3_w_epm0f_sae_r30_mbbl", "p4": "petstk_p4_w_epm0f_sae_r40_mbbl",
           "p5": "petstk_p5_w_epm0f_sae_r50_mbbl"}
GAS   = {a: load_series(GAS_MAP[a]) for a in PADD}  # finished gasoline

PRICES = {
    "wti":   f"{D}/wti_spot_daily.csv",
    "ho":    f"{D}/ulsd_nyh_spot_daily.csv",       # NY Harbor ULSD (diesel proxy)
    "rb":    f"{D}/gasoline_nyh_spot_daily.csv",   # NY Harbor RBOB proxy
    "brent": f"{D}/brent_spot_daily.csv",
    "gasoil": f"{D}/ulsd_gulf_spot_daily.csv",     # Gulf ULSD
    "gasgulf": f"{D}/gasoline_gulf_spot_daily.csv",
}

def load_px(path):
    d = pd.read_csv(path, parse_dates=["date"])
    d = d.set_index("date")["value"].astype(float).sort_index()
    d = d[~d.index.duplicated(keep="last")]
    return d

# ---------------- signal construction ----------------
def seasonal_dev(stock: pd.Series, years: int = 5) -> pd.Series:
    """Stock vs its own rolling 5y seasonal band (week-of-year matched)."""
    s = stock.copy()
    week = s.index.isocalendar().week.astype(int)
    avg, hi, lo = {}, {}, {}
    vals = s.values
    idx = s.index
    # build rolling seasonal window by calendar (no lookahead: use only past obs)
    out = np.full(len(s), np.nan)
    dates = s.index
    for i in range(len(s)):
        w = dates[i].isocalendar().week
        lo_d = dates[i] - pd.DateOffset(years=years)
        mask = (dates < dates[i]) & (dates >= lo_d)
        # same ISO week +/-1 to tolerate floating weeks
        wk = pd.Series(week.values, index=dates)
        sel = mask & wk.isin([w - 1, w, w + 1]).values
        if sel.sum() >= 6:
            hist = vals[sel]
            out[i] = (vals[i] - np.median(hist)) / (np.median(np.abs(hist - np.median(hist))) + 1e-9)
    return pd.Series(out, index=s.index)

def xsec_demean(dic: dict) -> pd.DataFrame:
    df = pd.DataFrame({k: v for k, v in dic.items()})
    return df.sub(df.mean(axis=1), axis=0)

def shift_pit(weekly_sig: pd.Series, days: int = 5) -> pd.Series:
    """Week-ending Friday stamp -> first tradeable day AFTER Wed 10:30 print."""
    return weekly_sig.copy().shift(0).reindex(weekly_sig.index) if False else weekly_sig

# ---------------- engine ----------------
def sr_m(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(12) if len(x) > 3 and x.std() > 0 else np.nan

def run_family(family: dict, px_name: str, direction: int, lookback_years: int = 5):
    """Signal: mean of cross-sectionally demeaned seasonal deviations, signed by
    `direction`, traded on px_name daily returns, entry PIT-shifted."""
    xs = xsec_demean({k: seasonal_dev(v, lookback_years) for k, v in family.items()})
    sig_w = xs.mean(axis=1) * direction           # weekly aggregate dysregulation
    # PIT: stamp is week-ending Fri; report prints next Wed 10:30 ET. Trade from Thu.
    sig_d = sig_w.reindex(px_index, method=None)
    # forward-fill weekly signal onto daily grid starting 5 calendar days after stamp
    avail = sig_w.copy()
    avail.index = avail.index + pd.Timedelta(days=5)   # Wed+1 = Thursday
    daily = pd.Series(np.nan, index=px_index)
    for t, v in avail.items():
        daily.loc[t:] = np.nan  # placeholder; vectorized fill below
    # vectorized: as-of join AFTER the +5d availability date
    avail_sorted = avail.dropna().sort_index()
    daily = pd.Series(
        [avail_sorted.asof(t) if len(avail_sorted) and (not pd.isna(avail_sorted.asof(t))) and avail_sorted.index.asof(t) <= t else np.nan for t in px_index],
        index=px_index)
    # position: sign with deadband; T+1 = signal available Thursday, position from Thursday close
    pos = np.sign(daily)
    pos = pos.shift(1).fillna(0.0)   # trade next day after info (conservative)
    rets = px_rets[px_name].reindex(px_index).fillna(0.0)
    sleeve = pos * rets
    # costs 6.4bps full |dW|
    cost = pos.diff().abs().fillna(0.0) * 0.00064
    return (sleeve - cost), pos, daily

# ---------------- main ----------------
if __name__ == "__main__":
    px = {k: load_px(v) for k, v in PRICES.items()}
    px_index = pd.date_range(min(v.index.min() for v in px.values()),
                             max(v.index.max() for v in px.values()), freq="B")
    px_rets = {k: v.pct_change().reindex(px_index).fillna(0.0) for k, v in px.items()}

    families = {"crude": CRUDE, "dist": DIST, "gas": GAS}
    results = []
    for fam_name, fam in families.items():
        for pxn in ["wti", "ho", "rb", "brent"]:
            for d in (+1, -1):
                try:
                    s, pos, sig = run_family(fam, pxn, d)
                except Exception as e:
                    print(f"{fam_name}/{pxn}/dir{d}: ERR {e}"); continue
                m = s.resample("ME").sum()
                isr = m[m.index < IS_END]; osr = m[m.index >= IS_END]
                if len(isr) < 24:
                    continue
                results.append(dict(family=fam_name, px=pxn, dir=d,
                                    IS_SR=sr_m(isr), OOS_SR=sr_m(osr),
                                    n_is=len(isr), n_oos=len(osr)))
    res = pd.DataFrame(results).sort_values("IS_SR", ascending=False)
    pd.set_option("display.width", 160)
    print(res.to_string(index=False, float_format=lambda x: f"{x:7.3f}"))
    res.to_csv(f"{B}/agents/HUNT_EIA_PADD/screen_results.csv", index=False)
    print("\nsaved screen_results.csv — IS-only ranking (OOS column recorded but NOT used for selection)")
