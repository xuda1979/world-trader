#!/usr/bin/env python3
"""HUNT_SECTOR2 ROUND 5 — data-admission audit + the one still-evaluable sleeve.

Charter corner (a): sector-rotation covariates from Nasdaq historical + PIT-safe
news/social aggregates (GoogleNews / Reddit). PIT discipline is the game: publication
lag per source documented; any series whose history cannot be proven prior -> drop it
and say so.

VERDICT THIS ROUND: the corner dies on data admission. GoogleNews RSS and Reddit Atom
are rolling snapshots (~1h / ~6d windows, no archive — probed live). Nasdaq quote/
historical silently serves only ~10y (2514 bars to 2016-09-06; explicit 2000/2007
fromdate AND hard 2010-2012 windows return identical/0 rows). wiki_attention is PIT-
safe with a real archive but starts 2015-07-01 -> span_class inception_fail (V2 9a).

The wiki_attention attention-covariate sleeve below is still evaluated THROUGH the
full V2 battery (leak probe + beats-passive trio, explicit sig=, leak_check=True) so
the negative is measured, not assumed — labeled NOT_HUNT_ELIGIBLE per V2 9a.

Construction discipline (own R3 precedent, honored): the base leg is the PUBLISHED
A11_rs_ratio#lb126k4 net series (artifact of record, sha-pinned) — no signal re-
construction. The attention covariate enters at the ALLOCATION level only: scale
0.25 when trailing attention z > +1 else 1.0, lagged TWO days (day-D pageviews
publish D+1 UTC; T+1 execution -> effective D+2). Allocation turnover |dScale|
charged 6.4bps one-side to the OVERLAY book only (the published base is already
costed). Adversarial control (V2 8h logic): 200 random de-risk gates matched on
fire-fraction AND flip count — a lift the placebo reproduces is de-risk arithmetic,
not attention.

Run: python3 hunt_sector2_r5.py            # admission audit + sleeve + artifacts
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work_r5")
os.makedirs(WORK, exist_ok=True)
for p in (ROOT, f"{ROOT}/campaign", f"{ROOT}/campaign/scripts"):
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------------ V2 machinery
import bt.gates as bgates          # noqa: E402
import bt.metrics as bmetrics      # noqa: E402
import hunt_sector2_lib as L       # noqa: E402

INCEPTION_BOUND = pd.Timestamp("2013-01-01")   # V2 9a: first bar after this = fail


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ================================================================== 1. ADMISSION
# Pre-registered roster (BEFORE evaluation). probe numbers are LIVE probe results
# captured 2026-09-08 05:4x-05:5x CST (see FINDINGS for the exact probe commands).
# Live-probe discipline: a feed whose window is shorter than the signal horizon
# cannot backtest at all, let alone prove prior publication.
ROSTER = [
    dict(
        name="google_news",
        source="news.google.com/rss/search (altdata5 google_news, keyless)",
        pit_lag="items stamped pubDate at crawl time; TWO live crawls 2026-09-08: "
                "crawl1 100 items spanning ~1h (15:45-16:45 GMT same day), crawl2 "
                "100 items spanning 495h/20.6d (one stale item at the window edge). "
                "Either way: bounded rolling window, NO archive endpoint.",
        history_available=False,
        probe_window_days=20.6,
        first_bar=None, rows=100, span_class="inception_fail",
        admission="DROP_NO_HISTORY",
        note="rolling RSS snapshot, no archive endpoint, cannot construct a series",
    ),
    dict(
        name="reddit_top",
        source="reddit.com/r/wallstreetbets/top/.rss (altdata5 reddit_top, keyless)",
        pit_lag="items stamped 'updated' at crawl time; crawl1 ~25 items spanning "
                "~4d (oldest 2026-09-02, newest 2026-09-06), crawl2 15 items spanning "
                "~5h. Bounded rolling window, NO archive endpoint.",
        history_available=False,
        probe_window_days=4.0,
        first_bar=None, rows=25, span_class="inception_fail",
        admission="DROP_NO_HISTORY",
        note="rolling Atom snapshot, no archive endpoint; no price-grid overlap either",
    ),
    dict(
        name="nasdaq_hist",
        source="api.nasdaq.com/api/quote/{sym}/historical (wt.sources.nasdaq_history, "
               "keyless; the rviv-fixed 2026-09-07 route)",
        pit_lag="official close published after 16:00 ET same day; usable t+1. BUT the "
                "archive itself is ~10y: fromdate silently ignored beyond it (live "
                "probe: fromdate=2000/2007 both return 2514 rows back to 2016-09-06; "
                "hard windows 2010-2012 / 2004-2006 / 2012-2013-06 return 0 rows)",
        history_available=True,
        probe_window_days=3652.0,
        first_bar="2016-09-06", rows=2514, span_class="inception_fail",
        admission="DROP_INCEPTION_FAIL",
        note="more_etf price files (XLK back to 1998-12) supersede it for price; the "
             "unique loss is VOLUME, which hits the same 10y cap",
    ),
    dict(
        name="wiki_attention",
        source="tools/quant/data/wiki_attention/*.csv (Wikimedia REST pageviews, "
               "keyless CC0; D+1 UTC publication documented in its README)",
        pit_lag="day-D views aggregated in UTC, served from ~00:00-04:00 UTC D+1 -> "
                "usable D+1 (PIT-safe, documented in wiki_attention/README.md)",
        history_available=True,
        probe_window_days=4086 / 365.25,
        first_bar="2015-07-01", rows=4086, span_class="inception_fail",
        admission="DROP_INCEPTION_FAIL",
        note="the ONLY charter-named source with a real PIT-safe archive; still misses "
             "the 2013-01-01 admission bound by 2.5 years",
    ),
]


def by_name(n):
    for e in ROSTER:
        if e["name"] == n:
            return e
    raise KeyError(n)


def admission_summary():
    n_adm = sum(1 for e in ROSTER if e["admission"].startswith("KEEP"))
    return dict(
        n_sources=len(ROSTER),
        n_admissible=n_adm,
        verdict="CORNER_DEAD_ON_DATA_ADMISSION" if n_adm == 0 else "PROCEED",
    )


# ================================================================== 2. THE SLEEVE
# Pre-registered construction (ONE spec, no tuning): allocation-level attention
# de-risk overlay on the published R2 A11 rotation. ATTENTION = cross-nick mean of
# trailing-252d z-scores of daily Wikipedia pageviews (aapl,nvda,tsla,spx,vix,fomc,
# cpi), then a 252d z of that mean (double-standardized). Gate: z > +1 -> scale 0.25.
ATT_NICKS = ["aapl", "nvda", "tsla", "spx", "vix", "fomc", "cpi"]


def load_attention():
    """Panel of daily pageviews for the 7 nicks, union of dates, no silent fill."""
    frames = {}
    for k in ATT_NICKS:
        p = os.path.join(ROOT, "tools/quant/data/wiki_attention", f"{k}.csv")
        s = pd.read_csv(p, parse_dates=["date"]).set_index("date")["views"]
        s.name = k
        frames[k] = s
    df = pd.DataFrame(frames).sort_index()
    assert df.index.is_monotonic_increasing
    return df


def attention_z(panel, window=252):
    """Cross-nick mean of per-nick trailing z-scores, then a 252d z of THAT mean
    (double-standardized so no single nick dominates). All trailing-only."""
    z = (panel - panel.rolling(window).mean()) / panel.rolling(window).std()
    cross = z.mean(axis=1, skipna=True)
    out = (cross - cross.rolling(window).mean()) / cross.rolling(window).std()
    return out.rename("att_z")


def vintage_pins(paths):
    """V2 9d/10b: pin every consumed file's sha + row count. Values are paths (str,
    hashed+counted) or already-computed counts (int, passed through)."""
    out = {}
    for tag, p in paths.items():
        if isinstance(p, str) and p.endswith(".csv"):
            with open(p) as f:
                rows = sum(1 for _ in f) - 1
            out[tag] = dict(sha256_16=sha256_16(p), rows=rows)
        else:
            out[tag] = dict(sha256_16=None, rows=p)
    return out


def eval_attention_sleeve():
    """Full V2 battery on the attention-scaled A11 rotation. Labeled NOT_HUNT_ELIGIBLE
    (span_class inception_fail, V2 9a) — a MEASURED negative, not a submission."""
    rng = np.random.default_rng(0)
    att_csv = os.path.join(ROOT, "tools/quant/data/wiki_attention/aapl.csv")
    panel = load_attention()
    a11_csv = os.path.join(HERE, "sleeves", "A11_rs_ratio#lb126k4.csv")

    # --- covariate: attention z (trailing-only, double-standardized)
    att = attention_z(panel)

    # --- base: published net, artifact of record (already carries its own costs)
    net_base = pd.read_csv(a11_csv, parse_dates=["date"]).set_index("date")["ret"]
    sr_base = bmetrics.sharpe_d(net_base)

    # --- allocation-level overlay scale, strict PIT shift(2)
    gate = (att > 1.0).astype(float)
    scale = pd.Series(np.where(gate.reindex(net_base.index).fillna(0.0) > 0, 0.25, 1.0),
                      index=net_base.index)
    scale = scale.shift(2).fillna(1.0)

    def alloc_cost(sc):
        dsc = sc.diff().abs().fillna(0.0)     # day-0 entry of an all-1.0 scale is free
        return dsc * L.COST / 1e4

    cost_on = alloc_cost(scale)
    net_on = net_base * scale - cost_on
    sr_overlay = bmetrics.sharpe_d(net_on)

    # per-unit underlying for the gates contract, EXACT: sig*r_pu must equal the
    # delivered book (scale never hits 0, so cost_on/scale is well-defined).
    r_pu = net_base - cost_on / scale

    # --- V2 battery on the OVERLAY (Step-1 explicit: sig=, leak_check=True; trio in).
    # The BASE is the published artifact — its R2 battery verdict (FAIL_SR only,
    # scramble 0.000, plateau PASS) is already on record; re-judging it with sig=1.0
    # would only fail-closed the leak probe (constant sig is unmeasurable) and add
    # nothing. Its number here (SR 0.679) is recomputed directly from the artifact.
    champ = L.champion()
    spy_ret = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv",
                          parse_dates=["date"]).set_index("date")["close"].sort_index().pct_change()
    ief_ret = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv",
                          parse_dates=["date"]).set_index("date")["close"].sort_index().pct_change()
    cta_ret = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv",
                          parse_dates=["date"]).set_index("date")["ret"]
    g_on = bgates.run(r_pu, ref=champ, sig=scale, leak_check=True, beats_passive=True,
                      spy=spy_ret, ief=ief_ret, cta=cta_ret)

    # --- adversarial placebo: 200 random gates matched on fire-fraction + flip count
    fire = (scale < 1.0).to_numpy()
    frac = fire.mean()
    nflip = int(np.abs(np.diff(fire.astype(int))).sum())
    dsr = sr_overlay - sr_base
    beats = 0
    for _ in range(200):
        g = (rng.random(len(net_base)) < frac).astype(int)
        for _try in range(50):     # resample until flip count is close to matched
            if abs(int(np.abs(np.diff(g)).sum()) - nflip) <= max(2, nflip // 20):
                break
            g = (rng.random(len(net_base)) < frac).astype(int)
        gs = pd.Series(g, index=net_base.index).shift(2).fillna(0.0)
        sc = pd.Series(np.where(gs > 0, 0.25, 1.0), index=net_base.index)
        sr_p = bmetrics.sharpe_d(net_base * sc - alloc_cost(sc))
        if sr_p >= sr_overlay:
            beats += 1
    placebo_p = beats / 200

    # --- honesty probes on the DELTA (R4 TimesFM lesson: a lift concentrated in one
    # episode is not a sleeve). dSR per half + single-episode exclusion: recompute the
    # dSR excluding the best calendar year of the delta and see whether it survives.
    d = net_on - net_base
    k = len(d) // 2
    dsr_h1 = bmetrics.sharpe_d(d.iloc[:k])
    dsr_h2 = bmetrics.sharpe_d(d.iloc[k:])
    yr_delta = d.groupby(d.index.year).apply(lambda x: x.sum())
    best_yr = int(yr_delta.idxmax())
    d_ex = d[d.index.year != best_yr]
    dsr_ex = bmetrics.sharpe_d(d_ex) if len(d_ex) > 60 else float("nan")

    # --- spans
    span_start = net_base.index.min().date().isoformat()
    span_end = net_base.index.max().date().isoformat()
    span_class = ("inception_fail"
                  if pd.Timestamp(span_start) > INCEPTION_BOUND else "2007plus")

    rationale = (
        "Attention-de-risk overlay on the PUBLISHED R2 A11 rotation (SR 0.679, "
        f"FAIL_SR only). span_class={span_class} (window {span_start}..{span_end} "
        "starts after the 2013-01-01 bound, V2 9a) -> NOT_HUNT_ELIGIBLE regardless "
        "of numbers. Measured anyway per charter: overlay SR vs published base, leak "
        "probe on the scale path (V2 6 Step-1, explicit), beats-passive trio, and a "
        "200-draw matched fire-fraction/flip-count placebo separating ATTENTION from "
        "generic de-risk timing."
    )

    res = dict(
        name="ATT_DE_RISK_A11",
        span_class=span_class,
        hunt_eligible=False,
        acceptance_track="NONE_NOT_HUNT_ELIGIBLE",
        n=len(net_base),
        span=f"{span_start}..{span_end}",
        gate_fire_frac=round(float(frac), 3),
        gate_flips=nflip,
        base_SR=round(sr_base, 3),
        overlay_SR=round(sr_overlay, 3),
        dSR=round(dsr, 3),
        placebo_p=placebo_p,
        dSR_halves=(round(dsr_h1, 3), round(dsr_h2, 3)),
        dSR_excl_best_yr=round(dsr_ex, 3),
        excl_year=best_yr,
        gates=g_on,
        net=net_on,
        vintage_pins=dict(
            **vintage_pins({"A11_rs_ratio#lb126k4.csv": a11_csv,
                            "wiki_attention.csv": att_csv,
                            "wiki_panel_rows": len(panel)}),
        ),
        rationale=rationale,
        verdict=("FAIL_SR|NOT_HUNT_ELIGIBLE" if sr_overlay < 1.0
                 else "SR_MET_BUT_NOT_HUNT_ELIGIBLE"),
    )
    return res


# ================================================================== 3. artifacts
def save_artifacts(res):
    """Sleeve + .meta per contract item 4. The .meta carries the FULL V2 disclosure:
    admission verdicts, span_class next to every number, leak dict, trio, pins."""
    net_meta = dict(
        name=res["name"],
        label="NOT_HUNT_ELIGIBLE (V2 9a span_class=inception_fail)",
        acceptance_track=res["acceptance_track"],
        span_class=res["span_class"], span=res["span"], n=res["n"],
        base_SR=res["base_SR"], overlay_SR=res["overlay_SR"], dSR=res["dSR"],
        placebo_p=res["placebo_p"],
        dSR_halves=res["dSR_halves"], dSR_excl_best_yr=res["dSR_excl_best_yr"],
        excl_year=res["excl_year"],
        gate_fire_frac=res["gate_fire_frac"], gate_flips=res["gate_flips"],
        gates_overlay=dict(sr=res["gates"]["sr"], pass_=res["gates"]["pass"],
                           leak=res["gates"]["leak"], leak_ok=res["gates"]["leak_ok"],
                           beats_passive=res["gates"]["beats_passive"],
                           corr_to_champion=res["gates"]["corr"],
                           scr_p=res["gates"]["scr_p"]),
        rationale=res["rationale"],
        admission_summary=admission_summary(),
        roster=[{k: e[k] for k in ("name", "admission", "span_class", "first_bar",
                                   "rows", "pit_lag")} for e in ROSTER],
        vintage_pins=res["vintage_pins"],
        champion_ref=dict(file="GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"),
        honest_negative=True,
    )
    p_meta = os.path.join(WORK, "ATT_DE_RISK_A11.csv.meta")
    with open(p_meta, "w") as f:
        json.dump(net_meta, f, indent=1, default=str)
    # sleeve net series (contract item 4: artifacts on disk, not just prose)
    p_csv = os.path.join(WORK, "ATT_DE_RISK_A11.net.csv")
    res["net"].to_frame("ret").to_csv(p_csv, index_label="date")
    return p_meta, p_csv


if __name__ == "__main__":
    print("=" * 100)
    print("ADMISSION AUDIT (charter-named corner sources)")
    print("=" * 100)
    for e in ROSTER:
        print(f"  {e['name']:15s} hist={e['history_available']!s:5s} "
              f"first={str(e['first_bar']):12s} rows={e['rows']:5d} "
              f"class={e['span_class']:14s} -> {e['admission']}")
    s = admission_summary()
    print(f"  => {s['n_admissible']}/{s['n_sources']} admissible: {s['verdict']}")

    print("\n" + "=" * 100)
    print("SLEEVE (measured, NOT_HUNT_ELIGIBLE): ATT_DE_RISK_A11")
    print("=" * 100)
    res = eval_attention_sleeve()
    g = res["gates"]
    print(f"  span={res['span']} n={res['n']} span_class={res['span_class']}")
    print(f"  gate: fire_frac={res['gate_fire_frac']} flips={res['gate_flips']}")
    print(f"  base    SR={res['base_SR']:.3f} (published artifact, R2 verdict FAIL_SR only)")
    print(f"  overlay SR={res['overlay_SR']:.3f}  dSR={res['dSR']:+.3f}  "
          f"placebo_p={res['placebo_p']:.3f}")
    print(f"  delta honesty: dSR halves={res['dSR_halves']} "
          f"excl-{res['excl_year']}: {res['dSR_excl_best_yr']:+.3f}")
    print(f"  gates battery: SR={g['sr']:.3f} pass={g['pass']} leak_ok={g['leak_ok']} "
          f"bp_ok={g['beats_passive_ok']} corr_champ={g['corr']:.3f} scr_p={g['scr_p']}")
    print(f"  verdict: {res['verdict']}")
    meta, csvp = save_artifacts(res)
    print(f"\n  meta -> {meta}\n  net  -> {csvp}")
