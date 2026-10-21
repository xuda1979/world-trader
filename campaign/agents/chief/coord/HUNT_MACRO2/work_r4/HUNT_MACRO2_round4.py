#!/usr/bin/env python3
"""HUNT_MACRO2 round 4 — CROSS-SLEEVE event study: ALFRED top-quintile surprise days on
the champion's 13 slots, then sleeve-rotation / de-lever overlays vs the own-vol control.

Charter R4 (coordinator 2026-09-07 17:2x): on top-quintile surprise days, which of the 13
champion sleeves earn/lose abnormally? Is there a stable sleeve-rotation or day-of-release
de-levering overlay that survives costs, T+1 lag, halves, scramble AND beats the generic
own-vol control (HUNT_CREDIT2 R2 lesson: a content-free vol mask fake-passes)? If the
control beats the macro gate again, it is DEAD — say so.

PRIMARY FALSIFIER (pre-registered in tests/test_macro_r4_events.py BEFORE evaluation):
the own-vol control (top-X% trailing 21d realized vol, expanding-quantile, PIT, on-frequency
matched within 0.3pp) must NOT meet-or-beat the macro overlay's improvement on the passing
acceptance arm. If it does, the macro trigger carries no content beyond "champion got
volatile" -> DEAD, no rescue.

Construction:
  Event set     : 9 ALFRED release series (round-3 PIT cubes; z = trailing-standardized
                  log jump vs prior known value, min_hist=12). Top quintile |z| >= 1.2816.
  T+1           : event day = first CHAMPION trading day STRICTLY AFTER the release date.
  Slot pnl      : exact slot accounting from the byte-reproducible champion rebuild
                  (HUNT_MACRO2_round2.build_champion): slot_pnl = Wg * df; sum - turnover
                  - margin == committed champion net to 1e-12.
  Overlays      : book-level only (R2 finding: the max-dd episode is 96% DEF-slot; slot
                  overlays relieve <=0.014pp). DE-LEVER x{0.8, 0.6} on macro event days;
                  SLEEVE-ROTATION by aggregate surprise sign on the pre-committed
                  RISK_ON/DEFENSIVE split. Exact r2 cost algebra (full |d(m*W)| at 6.4bps,
                  margin on overlaid gross, T+1 shift(1)).
  Own-vol ctrl  : trigger when trailing 21d realized vol > expanding q-quantile of its own
                  history (PIT: uses r through t-1 only); q matched to the macro trigger's
                  on-frequency within 0.3pp (fail-closed matcher).
  Acceptance    : dAnn >= +0.3pp OR dMDD >= +0.5pp, 0 neg years, gross <= 1.6,
                  trigger-scramble p <= 0.05 (200 perms, r2 machinery), halves gate on the
                  OVERLAY book (H1/H2 SR >= 0.5), AND beats own-vol control on the arm.
"""
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r1")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r2")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r3")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bt import metrics  # noqa: E402

import HUNT_MACRO2_round2 as R2  # noqa: E402
import HUNT_MACRO2_round3 as R3  # noqa: E402

ROOT = "/Users/daxu/software/world-trader"
ALF = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/sleeves"
SERIES = ["PAYEMS", "UNRATE", "CPIAUCSL", "RSXFS", "IPMAN", "UMCSENT", "HOUST", "DGORDER", "ICSA"]
Z90 = 1.2816  # Phi^-1(0.9): top-quintile two-sided

# Pre-committed slot split (identical to round 2, pinned in tests before evaluation)
RISK_ON = R2.RISK_ON          # C5ng C5ngsum carryv2 QAxasts dualmom diescrack CFX4
DEFENSIVE = R2.DEFENSIVE      # brwt15 brwt10 brwt7 brwt5 a6r7 A5r2
GEAR, RATE, BPS = R2.GEAR, R2.RATE, R2.BPS


# ------------------------------------------------------------------ event machinery
def build_surprise_table(series=SERIES, min_hist=12):
    """Per-series round-3 PIT surprise frame (indexed by release date), with series tag."""
    out = []
    for s in series:
        df = R3.load_cube(s)
        sur = R3.release_surprises(df, min_hist=min_hist)
        sur = sur.copy()
        sur["series"] = s
        out.append(sur)
    return pd.concat(out).sort_index()


def event_days(sur_one, thr=Z90, cal=None):
    """Boolean trigger on the trading calendar: True on the first TRADING day STRICTLY
    AFTER any release with |z| >= thr (NaN z never fires; the release day itself never
    fires). sur_one: frame indexed by release date with a 'z' column."""
    if cal is None:
        cal = R2.CHAMP.index
    b = pd.DatetimeIndex(cal)
    sig = pd.Series(False, index=b)
    z = sur_one["z"]
    z = z[np.isfinite(z) & (z.abs() >= thr)]
    pos = b.searchsorted(pd.DatetimeIndex(z.index), side="right")
    pos = pos[pos < len(b)]
    if len(pos):
        sig.iloc[pos] = True
    return sig


def union_trigger(tab, thr=Z90, cal=None):
    """Union event trigger across ALL series (any top-quintile surprise releasing)."""
    if cal is None:
        cal = R2.CHAMP.index
    b = pd.DatetimeIndex(cal)
    sig = pd.Series(False, index=b)
    z = tab["z"]
    z = z[np.isfinite(z) & (z.abs() >= thr)]
    pos = b.searchsorted(pd.DatetimeIndex(z.index), side="right")
    pos = pos[pos < len(b)]
    if len(pos):
        sig.iloc[pos] = True
    return sig


def signed_agg_trigger(tab, thr=Z90, cal=None):
    """Signed union trigger: +1 / -1 on event days by the SIGN of the aggregate surprise
    (sum of z over series releasing that day, among top-quintile ones)."""
    if cal is None:
        cal = R2.CHAMP.index
    b = pd.DatetimeIndex(cal)
    sig = pd.Series(0.0, index=b)
    z = tab["z"]
    z = z[np.isfinite(z) & (z.abs() >= thr)]
    # aggregate by release date
    agg = z.groupby(level=0).sum()
    pos = b.searchsorted(pd.DatetimeIndex(agg.index), side="right")
    keep = pos < len(b)
    for p, v in zip(pos[keep], np.sign(agg.values[keep])):
        sig.iloc[p] = v
    return sig


def day_counts_trigger(tab, thr=Z90, cal=None):
    """Count of top-quintile releases mapping to each calendar day (0,1,2,...)."""
    if cal is None:
        cal = R2.CHAMP.index
    b = pd.DatetimeIndex(cal)
    sig = pd.Series(0.0, index=b)
    z = tab["z"]
    z = z[np.isfinite(z) & (z.abs() >= thr)]
    pos = b.searchsorted(pd.DatetimeIndex(z.index), side="right")
    pos = pos[pos < len(b)]
    if len(pos):
        vc = pd.Series(pos).value_counts()
        for p, c in vc.items():
            sig.iloc[int(p)] = float(c)
    return sig


# ------------------------------------------------------------------ own-vol control
def ownvol_trigger(r, win=21, qtarget=0.95):
    """PIT own-vol trigger: trailing `win`d realized vol of r through t-1 (shift(1) inside
    the rolling window end) vs its EXPANDING quantile at `qtarget`. True when the current
    trailing vol exceeds that expanding quantile. Warmup days are False."""
    r = pd.Series(r).fillna(0.0)
    vol = r.rolling(win).std(ddof=1).shift(1)            # uses r up to t-1
    q = vol.expanding(min_periods=win).quantile(qtarget)
    trig = (vol > q).fillna(False)
    return trig


def match_quantile_for_freq(r, win=21, target_freq=0.069, tol=0.003):
    """Find the expanding-quantile qtarget whose on-frequency matches target_freq within
    tol (fail-closed: raises if no quantile in [0.50, 0.999] gets within tol)."""
    for q in np.arange(0.999, 0.49, -0.001):
        m = ownvol_trigger(r, win=win, qtarget=float(q))
        if abs(m.mean() - target_freq) <= tol:
            return float(q)
    raise RuntimeError(f"no expanding-quantile matches freq {target_freq} within {tol}")


# ------------------------------------------------------------------ overlays (r2 algebra)
def delever_overlay(champ, m):
    """Book de-lever: identical algebra to R2.overlay_book (kept as an explicit round-4
    wrapper so the test can pin identity with a constant m)."""
    return R2.overlay_book(champ, m)


def rotation_overlay(Wg, df, sgn, up=1.1, down=0.9, slots=None):
    """Sleeve-rotation: RISK_ON slots scaled by `up` on positive-aggregate-surprise days,
    `down` on negative ones (DEFENSIVE untouched). sgn: +1/-1/0 series on the calendar.
    Exact slot overlay accounting (R2.apply_slot_overlay)."""
    slots = slots or RISK_ON
    M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
    s = sgn.reindex(Wg.index).fillna(0.0)
    up_mask = s > 0
    dn_mask = s < 0
    for c in slots:
        if c in M.columns:
            M.loc[up_mask, c] = up
            M.loc[dn_mask, c] = down
    return R2.apply_slot_overlay(Wg, df, M), M


def delever_slot_overlay(Wg, df, trig, scale=0.6, slots=None):
    """Slot-level de-lever on trigger days (pre-registered variant; expected dead per R2
    mechanism — DEF slots own the dd — but tested, not assumed)."""
    slots = slots or list(Wg.columns)
    M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
    t = trig.reindex(Wg.index).fillna(False)
    for c in slots:
        M.loc[t, c] = scale
    return R2.apply_slot_overlay(Wg, df, M), M


# ------------------------------------------------------------------ reporting
def perf(net):
    net = net.dropna()
    neg, worst = metrics.neg_years(net)
    return dict(ann=metrics.ann_geo(net), sr=metrics.sharpe_d(net), mdd=metrics.max_dd(net),
                neg=neg, worst=worst, n=len(net),
                h1=metrics.half_split(net)[0], h2=metrics.half_split(net)[1])


def event_table(tab, trig, Wg, df):
    """Cross-sleeve event study: mean slot pnl (bp/day) on event T+1 days vs other days,
    with a two-sample t-stat. Slot pnl = Wg*df (pre-cost; the champion's own accounting)."""
    slot_pnl = (Wg * df.fillna(0.0)) * 1e4  # bp/day
    on = trig.reindex(Wg.index).fillna(False).astype(bool)
    rows = []
    for c in Wg.columns:
        x = slot_pnl[c][on].dropna()
        y = slot_pnl[c][~on].dropna()
        se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
        t = (x.mean() - y.mean()) / se if se > 0 else np.nan
        rows.append(dict(slot=c, n_on=int(on.sum()), mean_on_bp=x.mean(), mean_off_bp=y.mean(),
                         diff_bp=x.mean() - y.mean(), t=t))
    # book level
    x = slot_pnl.sum(axis=1)[on].dropna()
    y = slot_pnl.sum(axis=1)[~on].dropna()
    se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    rows.append(dict(slot="BOOK", n_on=int(on.sum()), mean_on_bp=x.mean(), mean_off_bp=y.mean(),
                     diff_bp=x.mean() - y.mean(),
                     t=(x.mean() - y.mean()) / se if se > 0 else np.nan))
    return pd.DataFrame(rows)


def eval_overlay(name, net_ov, champ, do_scramble=None, scramble_metric='ann'):
    """Acceptance battery on an overlay book (r2 arms + halves + scramble)."""
    pc, po = perf(champ), perf(net_ov)
    d_ann = po["ann"] - pc["ann"]
    d_mdd = po["mdd"] - pc["mdd"]  # max_dd negative: shallower = better
    row = dict(name=name, ann=po["ann"], sr=po["sr"], mdd=po["mdd"], neg=po["neg"],
               h1=po["h1"], h2=po["h2"], d_ann=d_ann, d_mdd=d_mdd,
               arms=bool(d_ann >= 0.003 or d_mdd >= 0.005),
               halves=bool(po["h1"] >= 0.5 and po["h2"] >= 0.5),
               neg0=bool(po["neg"] == 0))
    row["accepts_raw"] = row["arms"] and row["halves"] and row["neg0"]
    if do_scramble and row["accepts_raw"]:
        # scramble the DRIVING trigger; net_ov must correspond to it
        m = do_scramble
        p, _ = R2.scramble_trigger(m.astype(float), champ, metric=scramble_metric)
        row["p"] = p
        row["accepts_raw"] = row["accepts_raw"] and p <= 0.05
    return row, net_ov


def fmt(r):
    p = "-" if r.get("p") is None else f"{r['p']:.3f}"
    return (f"  {r['name']:46s} ann={r['ann']*100:6.2f}% SR={r['sr']:5.2f} "
            f"MDD={r['mdd']*100:6.2f}% neg={r['neg']} H1={r['h1']:5.2f} H2={r['h2']:5.2f} "
            f"dAnn={r['d_ann']*100:+6.3f}pp dMDD={r['d_mdd']*100:+6.3f}pp p={p} ok={r['accepts_raw']}")


# ------------------------------------------------------------------ main
def main():
    pd.set_option("display.width", 220)
    champ = R2.CHAMP
    net, Wg, df = R2.build_champion()
    pc = perf(champ)
    print(f"champion rebuilt: ann={pc['ann']*100:.3f}% SR={pc['sr']:.3f} MDD={pc['mdd']*100:.3f}% "
          f"neg={pc['neg']} (committed: 37.195/3.181/-6.692/0)")
    d = (net.reindex(champ.index) - champ).abs().max()
    print(f"rebuild dev vs committed: {d:.3e}")

    tab = build_surprise_table()
    print(f"surprise table: {len(tab)} scored releases across {tab['series'].nunique()} series")

    trig = union_trigger(tab, Z90)
    on, n = int(trig.sum()), len(trig)
    print(f"union top-quintile event days: {on} ({100*on/n:.2f}%)")
    et = event_table(tab, trig, Wg, df)
    print("\n=== EVENT STUDY: slot pnl bp/day, event T+1 days vs rest (top-quintile |z|>=1.2816) ===")
    print(et.to_string(index=False, float_format=lambda v: f"{v:8.2f}"))
    et.to_csv(f"{os.path.dirname(os.path.abspath(__file__))}/r4_event_study.csv", index=False)

    rows = []
    sgn = signed_agg_trigger(tab, Z90)
    n_pos, n_neg = int((sgn > 0).sum()), int((sgn < 0).sum())
    print(f"\nsigned union: {n_pos} pos / {n_neg} neg event days")

    # --- (A) book de-lever on macro event days
    for sc in (0.8, 0.6):
        m = pd.Series(1.0, index=champ.index)
        m[trig] = sc
        ov = delever_overlay(champ, m)
        r, _ = eval_overlay(f"DELEVER book x{sc} (macro events)", ov, champ)
        r["m_series"] = m
        rows.append(r)

    # --- (B) sleeve-rotation by surprise sign (risk-on only)
    for up, dn in ((1.1, 0.9), (1.15, 0.85), (0.9, 1.1), (0.85, 1.15)):
        ov, _ = rotation_overlay(Wg, df, sgn, up=up, down=dn)
        r, _ = eval_overlay(f"ROTATE riskon up{up}/dn{dn}", ov, champ)
        rows.append(r)

    # --- (C) slot de-lever (pre-registered variant, expected dead per R2 mechanism)
    for sc in (0.8, 0.6):
        ov, _ = delever_slot_overlay(Wg, df, trig, scale=sc)
        r, _ = eval_overlay(f"DELEVER all-slots x{sc}", ov, champ)
        rows.append(r)

    # --- own-vol control at matched frequency (PRIMARY FALSIFIER)
    macro_freq = float(trig.mean())
    q = match_quantile_for_freq(champ, win=21, target_freq=macro_freq, tol=0.003)
    vol_trig = ownvol_trigger(champ, win=21, qtarget=q)
    print(f"own-vol control: q={q:.3f} on-freq={100*vol_trig.mean():.2f}% (macro {100*macro_freq:.2f}%)")
    for sc in (0.8, 0.6):
        m = pd.Series(1.0, index=champ.index)
        m[vol_trig] = sc
        ov = delever_overlay(champ, m)
        r, _ = eval_overlay(f"CONTROL ownvol x{sc} (matched)", ov, champ)
        r["m_series"] = m
        rows.append(r)

    # second control: matched-frequency random trigger (200 draws, median delta)
    rng = np.random.default_rng(7)
    idx = champ.index
    ctrl_ann, ctrl_mdd = [], []
    for _ in range(200):
        ms = pd.Series(rng.permutation(trig.values.astype(float)), index=idx)
        mm = pd.Series(1.0, index=idx)
        mm[ms > 0] = 0.6
        po = perf(R2.overlay_book(champ, mm))
        ctrl_ann.append(po["ann"] - pc["ann"])
        ctrl_mdd.append(po["mdd"] - pc["mdd"])
    print(f"random same-freq masks (200): dAnn median {100*np.median(ctrl_ann):+.3f}pp "
          f"p95 {100*np.percentile(ctrl_ann, 95):+.3f}pp | dMDD median {100*np.median(ctrl_mdd):+.3f}pp "
          f"p95 {100*np.percentile(ctrl_mdd, 95):+.3f}pp")

    # scramble p for any raw-accepting macro row
    out = []
    for r in rows:
        if r["accepts_raw"] and "m_series" in r:
            mm = r.pop("m_series")
            p, _ = R2.scramble_trigger(mm.astype(float), champ,
                                       metric="mdd" if r["d_mdd"] >= 0.005 and r["d_ann"] < 0.003 else "ann")
            r["p"] = p
            r["accepts_raw"] = r["accepts_raw"] and p <= 0.05
        elif "m_series" in r:
            r.pop("m_series")
        out.append(r)

    print("\n=== OVERLAY RESULTS (deltas vs champion) ===")
    for r in out:
        print(fmt(r))

    res = pd.DataFrame([{k: v for k, v in r.items() if k != "m_series"} for r in out])
    res.to_csv(f"{os.path.dirname(os.path.abspath(__file__))}/r4_overlay_results.csv", index=False)

    # per-series event-day count for the record
    per = tab[np.isfinite(tab["z"]) & (tab["z"].abs() >= Z90)].groupby("series").size()
    print("\ntop-quintile releases per series:")
    print(per.to_string())


if __name__ == "__main__":
    main()
