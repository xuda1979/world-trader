#!/usr/bin/env python3
"""HUNT_MACRO2 round 3 — macro-SURPRISE standalone sleeve (charter 3b).

Data: ALFRED vintage cubes (fetch_alfred_cube.py, charter 3a — all 9 series
HTTP 200, PAYEMS anchor verified: obs 2009-11-01 first visible 2009-12-04).
CLAMPED VINTAGES: the fetch floor (realtime_start=2005-01-01) and each series'
ALFRED birth pin the FIRST vintage of early obs periods to the window floor —
those dates are not release dates and every obs whose first vintage equals the
cube's global min vintage date is dropped from the release calendar (tests pin
PAYEMS 2004-12 kept / 2003 rows dropped; ICSA 2009-05-23 is accepted collateral).

Family: release-event surprise. Expectation proxy = latest-known value of the
PREVIOUS observation period as of release day (revision chain = the honest
no-consensus fallback). Surprise z = (log print/prev) minus trailing mean of
past release-to-release log-jumps, / trailing sd, using only STRICTLY EARLIER
scored releases. Event-time positioning T+1 on the TRADING calendar (holiday-
aware: a Friday release with Monday shut holds Tuesday). Direction is the open
question the round must answer BOTH ways (follow and fade) — the charter asks
for a standalone sleeve, not a direction prior.

Standalone book (NOT a champion overlay): one ETF, sign(z) direction, 6.4bps
FULL |dW| on the held book (day-1 seed = first held position; book starts
flat), borrow 0.5%/yr shorts, VT10% trailing-only clip<=3.0.
Gates per GATES_CONTRACT.md via evaluate(): SR>=1.0, halves>=0.5, yearly, |corr|
<0.15 vs champion, and an ENFORCED position-lag scramble (bt.gates.
scramble_positions on the held positions vs per-unit returns, 200 draws,
p<0.05) — the R1 honesty probe showed a costs-only scramble is vacuous, so the
scramble judges the POSITIONS, not a permutation that churns costs.
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
ALF = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred"
ET = f"{ROOT}/tools/quant/data/more_etf"
TLQ = f"{ROOT}/tools/quant/data/twelve_liq"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/sleeves"
COST_BPS = 6.4
BORROW = 0.005
ANN = 252.0

import bt.engine as engine  # noqa: E402  (vol_target_scale)
import bt.metrics as metrics  # noqa: E402
import bt.gates as bgates  # noqa: E402

CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]


# ---------------------------------------------------------------- vintage cube
def _coerce_cube(df):
    """Normalize a cube frame: datetime obs_date/vintage_date, float value.
    Accepts string-date frames (tests) as well as parsed CSV loads."""
    df = df.copy()
    df["obs_date"] = pd.to_datetime(df["obs_date"])
    df["vintage_date"] = pd.to_datetime(df["vintage_date"])
    df["value"] = df["value"].astype(float)
    return df.sort_values(["obs_date", "vintage_date"]).reset_index(drop=True)


def load_cube(sid):
    return _coerce_cube(pd.read_csv(f"{ALF}/{sid}.csv"))


def snapshot_at(df, t):
    """Values of every obs period KNOWN at date t (vintage_date <= t), as a series
    indexed by obs_date. PIT: strict vintage filter, no other knowledge."""
    df = _coerce_cube(df)
    t = pd.Timestamp(t)
    k = df[df.vintage_date <= t]
    # latest vintage per obs period as of t
    return k.groupby("obs_date")["value"].last()


def first_prints(df):
    """First-published value per obs period (indexed by obs_date)."""
    df = _coerce_cube(df)
    return df.groupby("obs_date")["value"].first()


def release_calendar(df):
    """Publication date per obs period = min vintage_date.

    Fail-closed CLAMP FILTER: any obs period whose first vintage equals the
    cube's global minimum vintage date has its release date PINNED by the fetch
    window (realtime_start floor) or the series' ALFRED birth — not an actual
    release. Those are dropped loudly (count printed once by the caller).
    """
    df = _coerce_cube(df)
    first = df.groupby("obs_date")["vintage_date"].min()
    clamp = first == first.min()
    if clamp.any():
        n = int(clamp.sum())
        floor = first.min()
        first = first[~clamp]
        # ENGINE FIX (round 3): the log printed first.min() AFTER filtering, which
        # names a real release date as the 'floor' — misleading evidence. Print
        # the actual floor captured before the filter.
        print(f"[release_calendar] dropped {n} clamped obs periods "
              f"(first vintage == floor {floor.date()})",
              file=sys.stderr)
    return first.sort_values()


# ---------------------------------------------------------------- surprises
def release_surprises(df, min_hist=12, log_diff=True):
    """Per-release surprise: log jump vs latest-known previous obs value, z-scored
    by trailing (strictly-earlier-release) mean/sd of past jumps.

    min_hist = scored releases of PRIOR history required before mu is defined
    (sd additionally needs >=2). Returns frame indexed by RELEASE DATE with
    columns [obs, value, prev_known, jump, mu, sd, z].
    """
    df = _coerce_cube(df)
    cal = release_calendar(df)                     # obs -> release date (clamps dropped)
    rel = cal.sort_values().index.to_list()        # obs periods in release order
    rows = []
    for i, od in enumerate(rel):
        t = cal.loc[od]
        snap = snapshot_at(df, t)                  # PIT knowledge at t
        if od not in snap.index:
            continue
        v = float(snap.loc[od])
        prev_periods = snap.index[snap.index < od]
        if len(prev_periods) == 0:
            continue
        pv = float(snap.loc[prev_periods[-1]])
        if not (np.isfinite(v) and np.isfinite(pv)) or pv <= 0 or v <= 0:
            continue
        jump = np.log(v / pv) if log_diff else (v - pv) / abs(pv)
        scored = np.array([r["jump"] for r in rows if np.isfinite(r["jump"])])
        mu = scored.mean() if len(scored) >= min_hist else np.nan
        sd = scored.std(ddof=1) if len(scored) >= 2 else np.nan
        z = (jump - mu) / sd if (np.isfinite(mu) and np.isfinite(sd) and sd > 1e-12) else np.nan
        rows.append(dict(rel_date=t, obs=od, value=v, prev_known=pv, jump=jump,
                         mu=mu, sd=sd, z=z))
    out = pd.DataFrame(rows).set_index("rel_date").sort_index()
    out.index.name = "rel_date"
    return out


def release_surprises_expect_proxy(df, min_hist=2):
    """Variant expectation proxy: surprise = jump - trailing RELEASE-CALENDAR mean
    log-jump (mu only, no sd normalization). Keeps jump's sign; less normalization
    noise. NaN-safe: rows with undefined mu carry NaN (never fire)."""
    s = release_surprises(df, min_hist=min_hist)
    out = s.copy()
    out["z_mu_only"] = np.where(s["mu"].notna(), s["jump"] - s["mu"], np.nan)
    return out


# ---------------------------------------------------------------- signal -> book
def event_signal(df, z=1.0, hold=1, size=1.0, min_hist=12, use="z", cal=None):
    """Daily weight series on trading calendar `cal` (default: champion index).
    sign(z_rel)*size on the first `hold` TRADING days STRICTLY AFTER the release
    when |score| >= z (NaN scores never fire). Uses the release calendar +
    scored z AT release (PIT: z uses only earlier releases)."""
    s = release_surprises(df, min_hist=min_hist)
    zc = s[use] if use in s.columns else s["z"]
    if cal is None:
        cal = CHAMP.index
    b = pd.DatetimeIndex(cal)
    w = pd.Series(0.0, index=b)
    for rel, row in s.iterrows():
        sc = row[use] if use in s.columns else row["z"]
        if not np.isfinite(sc) or abs(sc) < z:
            continue
        d = np.sign(sc) * size
        # first trading day STRICTLY AFTER the release (holiday-aware)
        pos = int(b.searchsorted(rel, side="right"))
        if pos >= len(b):
            continue
        w.iloc[pos:pos + hold] = d
    return w


def vt_scale(r, target=0.10, minlen=60, cap=3.0):
    """Trailing-only VT: uses r up to t-1 (shift(1) inside)."""
    vol = r.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap).clip(lower=0.0)
    return s.shift(1).fillna(1.0)


def net_of(w, r, vt=True, target=0.10):
    """Standalone net returns: w decided at t, held t+1; VT scale from past only.
    Costs: 6.4bps one-side on FULL |d(held)| with day-1 seed = first held
    position (book starts FLAT — not 1.0), borrow 0.5%/yr on shorts.
    Returns (net_series, held_positions)."""
    w = w.reindex(r.index.union(w.index)).ffill().fillna(0.0).reindex(r.index).fillna(0.0)
    p = w.shift(1).fillna(0.0)                    # T+1
    sc = vt_scale(r.fillna(0.0), target=target) if vt else pd.Series(1.0, index=r.index)
    ps = p * sc
    gross = ps * r.fillna(0.0)
    to = ps.diff().abs()
    if len(ps):
        to.iloc[0] = abs(ps.iloc[0])              # day-1 seed = first held position
    cost = to * COST_BPS / 1e4
    borr = (-ps.clip(upper=0.0)) * BORROW / ANN
    return (gross - cost - borr).rename("ret"), ps


# ---------------------------------------------------------------- gates
def evaluate(name, net, ps=None, r_pu=None, verbose=True):
    """FULL gate battery per GATES_CONTRACT.md, fail-closed.

    Scramble: bt.gates.scramble_positions on the HELD POSITIONS vs per-unit
    returns (200 draws, lag >= 20d) — judges the POSITIONS, not a cost-only
    permutation (the R1 probe showed cost-only scrambles are vacuous).
    ps/r_pu missing -> p=NaN and ok['e_scramble']=False (fail-closed, no skip).
    """
    net = net.dropna()
    # ENGINE FIX (round 3): early branches used key 'pass_' while the main path
    # and every reader use 'pass' -> too-short/missing-scramble books reported an
    # UNREAD verdict key (fail-open reporting). Both paths now return 'pass': False.
    if len(net) < 500:
        return dict(name=name, **{"pass": False}, why=f"n<500 ({len(net)})", n=len(net))
    if ps is None or r_pu is None:
        return dict(name=name, **{"pass": False},
                    why="scramble inputs missing (fail-closed)", n=len(net))
    sr = metrics.sharpe_d(net)
    h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    vol = net.std() * np.sqrt(ANN)
    corr = bgates.corr_to(CHAMP, net)
    p, real_sr = bgates.scramble_positions(ps.values.astype(float),
                                           r_pu.reindex(net.index).fillna(0.0).values,
                                           n=200, block=20)
    res = dict(name=name, sr=sr, ann=metrics.ann_geo(net), vol=vol, h1=h1, h2=h2,
               neg=neg, worst=worst, corr=corr, n=len(net), p=p, real_sr_scr=real_sr,
               start=net.index[0].date(), end=net.index[-1].date())
    res["ok"] = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05),
                     f_corr=(np.isfinite(corr) and abs(corr) < 0.15),
                     e_scramble=bool(np.isfinite(p) and p < 0.05))
    res["pass"] = all(bool(v) for v in res["ok"].values())
    if verbose:
        ok = res["ok"]
        print(f"[{name}] n={res['n']} SR={sr:.2f} ann={res['ann']*100:+.1f}% "
              f"H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"corr={corr:.3f} scram_p={p:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"|corr|<0.15:{ok['f_corr']} scramble:{ok['e_scramble']} PASS={res['pass']}")
    return res


# ---------------------------------------------------------------- data
def etf_ret(e):
    """Daily returns for an ETF; live in more_etf, fallback twelve_liq."""
    for base in (ET, TLQ):
        path = f"{base}/{e}.csv"
        if os.path.exists(path):
            c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
            return c.pct_change()
    raise FileNotFoundError(f"{e}.csv not in more_etf or twelve_liq")


SERIES_ETF = {
    # release series -> tradable ETFs whose direction the surprise should move
    "PAYEMS":  ["QQQ", "TLT", "IEF"],
    "UNRATE":  ["QQQ", "TLT"],
    "CPIAUCSL": ["QQQ", "TLT", "TIP"],
    "RSXFS":   ["QQQ"],
    "IPMAN":   ["QQQ", "XLI"],
    "UMCSENT": ["QQQ"],
    "HOUST":   ["XHB", "ITB"],
    "DGORDER": ["QQQ", "XLI"],
    "ICSA":    ["QQQ", "TLT"],
}


def main():
    pd.set_option("display.width", 200)
    etfs = {e: etf_ret(e) for e in ["QQQ", "TLT", "IEF", "TIP", "XHB", "ITB", "XLI"]}
    all_rows = []
    for sid in ["PAYEMS", "UNRATE", "CPIAUCSL", "RSXFS", "IPMAN", "UMCSENT",
                "HOUST", "DGORDER", "ICSA"]:
        cube = load_cube(sid)
        s = release_surprises(cube, min_hist=12)
        scored = s["z"].notna().sum()
        print(f"\n=== {sid}: {len(s)} releases scored ({s.index[0].date()}..{s.index[-1].date()}), "
              f"{scored} with finite z |z|>1 frac={float((s.z.abs() >= 1).sum() / max(scored, 1)):.3f} "
              f"med|jump|={float(s.jump.abs().median()) * 1e4:.1f}bp ===", flush=True)
        for etf in SERIES_ETF[sid]:
            r = etfs[etf]
            for direction, sign in [("FOLLOW", 1.0), ("FADE", -1.0)]:
                # z-threshold family (sd-normalized)
                for thr, hold in [(1.0, 1), (1.0, 3), (1.5, 1), (2.0, 1), (2.0, 3)]:
                    w = event_signal(cube, z=thr, hold=hold, size=sign, min_hist=12, use="z")
                    net, ps = net_of(w, r)
                    nm = f"{sid}->{etf} {direction} thr{thr} h{hold} z"
                    res = evaluate(nm, net, ps=ps, r_pu=r, verbose=False)
                    res.update(sid=sid, etf=etf, direction=direction, thr=thr,
                               hold=hold, use="z")
                    all_rows.append(res)
                # mu-only variant (no sd normalization), one param set
                for thr in [0.0, 0.001]:
                    w = event_signal(cube, z=thr, hold=1, size=sign, min_hist=12,
                                     use="z_mu_only")
                    net, ps = net_of(w, r)
                    nm = f"{sid}->{etf} {direction} mu thr{thr} h1"
                    res = evaluate(nm, net, ps=ps, r_pu=r, verbose=False)
                    res.update(sid=sid, etf=etf, direction=direction, thr=thr,
                               hold=1, use="z_mu_only")
                    all_rows.append(res)
        # full-grid verbose echo for the log (best SR row per series)
    df = pd.DataFrame(all_rows)
    df.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/round3_results.csv",
              index=False)
    npass = int(df["pass"].fillna(False).astype(bool).sum())
    print(f"\n=== SUMMARY: {npass}/{len(df)} pass ALL gates ===", flush=True)
    cols = ["name", "n", "sr", "ann", "h1", "h2", "neg", "worst", "corr", "p", "pass"]
    print(df[cols].sort_values("sr", ascending=False).head(40).to_string(index=False))


if __name__ == "__main__":
    main()
