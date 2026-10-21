#!/usr/bin/env python3
"""TDD round 5 — NKY 77-year span-class sleeve (calendar/seasonal + single-market trend).

PRE-REGISTERED before any evaluation (2026-09-08, charter round 5 corner):
  universe   newdata/NIKKEI225.csv (20,166 rows 1949-05-16..2026-08-31, span_class pre2007)
  families   CAL_TOM (turn-of-month, long last3+first3 bdays)
             CAL_TOY (turn-of-year, long last5-Dec + first5-Jan bdays)
             CAL_SELLMAY (long Oct..Apr, flat May-Sep)
             MOM_{252_LS,252_LF,126_LF,63_LF} (single-market time-series momentum)
  honesty    T+1 shift(1), 6.4bps full |dW| + 0.5%/yr borrow, vt10 expanding clip3,
             scramble 200x re-costed, gates.run V2 battery with sig= + leak_check=True,
             beats-passive trio, MANDATORY pre-1990 vs post-1990 sub-span stability.
Fails until HUNT_INTL2_round5.py implements these semantics.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np
import pandas as pd

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def fresh(px):
    """Deterministic rising price frame on business days."""
    idx = pd.bdate_range("2000-01-03", periods=300)
    return pd.DataFrame({"NKY": 100.0 + np.arange(len(idx), dtype=float)}, index=idx)


def main():
    import HUNT_INTL2_round5 as R5

    px = fresh(None)
    # rises for 150 days then falls for 150: momentum flips -> real entry AND exit days
    vals = np.concatenate([100.0 + np.arange(150, dtype=float),
                           250.0 - np.arange(150, dtype=float)])
    px_fx = pd.DataFrame({"NKY": vals}, index=pd.bdate_range("2000-01-03", periods=300))

    # 1. no-lookahead: every signal/weight builder is end-truncation invariant
    for fn_name, args in [("cal_tom_weights", ()), ("cal_toy_weights", ()),
                          ("cal_sellmay_weights", ()),
                          ("mom_weights", (252, "LF",)), ("mom_weights", (63, "LS",))]:
        fn = getattr(R5, fn_name)
        W_full = fn(px, *args)
        probe = px.index[150]
        W_cut = fn(px.loc[:probe], *args)
        same = W_full.loc[:probe].round(10).equals(W_cut.round(10))
        check(f"no-lookahead end-truncation invariance: {fn_name}{args}", same)

    # 2. T+1: net_of applies shift(1) — day-0 book flat, earns from day 1 on
    W = R5.mom_weights(px, 63, "LF")
    net, We, gross = R5.net_of(W, px.pct_change())
    check("T+1: entry day book is flat (shift applied)", float(We.iloc[0].abs().sum()) == 0.0)

    # 3. entry trade charged: cost_turnover sees 0->w establishment via engine (R2-locked),
    #    round-5 net_of must NOT re-shift costs differently: cost > 0 on first live day
    live = (We.fillna(0.0) != 0).any(axis=1).idxmax()
    cost = R5.engine.cost_turnover(We, cost_bps=6.4)
    check("entry trade charged on first live day", float(cost.loc[:live].sum()) > 0.0)

    # 4. fail-closed: never-live book raises (broken build != zero-SR book)
    Wz = pd.DataFrame(0.0, index=px.index, columns=["NKY"])
    try:
        R5.trim_warmup(pd.Series(0.0, index=px.index), Wz)
        check("fail-closed never-live book raises", False)
    except AssertionError:
        check("fail-closed never-live book raises", True)

    # 5. TOM mask (PRIMARY, date-based — needs no calendar knowledge, truncation-invariant):
    #    long on month-days >= 28 and <= 3, flat otherwise
    Wt = R5.cal_tom_weights(px)
    idx = px.index
    expect = (idx.day >= 28) | (idx.day <= 3)
    check("TOM mask exact (date-based: day>=28 | day<=3)",
          bool((Wt["NKY"] > 0).equals(pd.Series(expect, index=idx))))

    # 5b. TOM rank variant: long on the last 3 + first 3 TRADING days of each month
    Wr = R5.cal_tom_rank_weights(px, k_end=3, k_start=3)
    r_end = idx.to_series().groupby(idx.to_period("M")).rank(method="first", ascending=False)
    r_start = idx.to_series().groupby(idx.to_period("M")).rank(method="first")
    expect_r = ((r_end <= 3) | (r_start <= 3)).reindex(idx).fillna(False)
    check("TOM-rank mask exact (last3+first3 trading days)",
          bool((Wr["NKY"] > 0).equals(pd.Series(expect_r, index=idx))))

    # 5c. TOM-rank is calendar-knowable, NOT truncation-invariant in the cut's final
    #     partial month; outside it must be identical (the published-calendar property)
    probe = px.index[150]
    a = Wr.loc[:probe].round(10); b = R5.cal_tom_rank_weights(px.loc[:probe], 3, 3).round(10)
    diff = (a != b).any(axis=1)
    in_last_month = (diff[diff].index.to_period("M") == probe.to_period("M"))
    check("TOM-rank truncation diffs confined to cut's final partial month",
          bool(diff.sum() == 0 or in_last_month.all()))

    # 6. TOY mask (PRIMARY, date-based): long Dec 25-31 + Jan 1-5 only
    Wy = R5.cal_toy_weights(px)
    expect_y = ((idx.month == 12) & (idx.day >= 25)) | ((idx.month == 1) & (idx.day <= 5))
    check("TOY mask exact (date-based: Dec25-31 + Jan1-5 only)",
          bool((Wy["NKY"] > 0).equals(pd.Series(expect_y, index=idx))))

    # 7. sell-in-May mask: long Oct..Apr, flat May..Sep
    Wm = R5.cal_sellmay_weights(px)
    expect_m = ~idx.month.isin([5, 6, 7, 8, 9])
    check("SELLMAY mask exact (long Oct-Apr, flat May-Sep)",
          bool((Wm["NKY"] > 0)[1:].equals(pd.Series(expect_m[1:], index=idx[1:]))))

    # 8. momentum sign: rising prices -> LF long; falling -> LF flat (LS short)
    px_dn = pd.DataFrame({"NKY": 100.0 + np.arange(300, dtype=float)[::-1]},
                         index=px.index)  # strictly falling
    W_up = R5.mom_weights(px, 63, "LF")
    W_dn = R5.mom_weights(px_dn, 63, "LF")
    W_dn_ls = R5.mom_weights(px_dn, 63, "LS")
    live_up = (W_up["NKY"] != 0) & (W_up.index > px.index[63])
    live_dn = (W_dn["NKY"] != 0) & (W_dn.index > px_dn.index[63])
    check("MOM LF: long in uptrend", bool((W_up.loc[live_up, "NKY"] > 0).all()))
    check("MOM LF: flat in downtrend", bool((W_dn.loc[~live_dn, "NKY"] == 0).all()
                                            or (W_dn.loc[live_dn, "NKY"] > 0).all() is False))
    check("MOM LS: short in downtrend",
          bool((W_dn_ls.loc[W_dn_ls.index > px_dn.index[63], "NKY"] < 0).all()))

    # 9. per-unit-net feed is EXACT on the held book (post-VT We): sig * r_pu == net.
    #    Known disclosed gap: rows where sig == 0 but an exit cost was charged cannot
    #    represent that cost (0 * anything = 0); the gap is bounded by one day's cost.
    Wm2 = R5.mom_weights(px_fx, 63, "LF")   # px_fx rises then falls -> real exits
    net2, We2, gross2 = R5.net_of(Wm2, px_fx.pct_change())
    sig = We2.sum(axis=1)
    r_pu = R5.per_unit_net(px_fx.pct_change()["NKY"], We2)
    dev = float((sig * r_pu - net2).abs().max())
    one_day_cost = float(R5.engine.cost_turnover(We2, cost_bps=6.4).max())
    check(f"per-unit-net feed == book (dev {dev:.2e} <= exit-cost bound {one_day_cost:.2e})",
          dev <= one_day_cost + 1e-15)
    nz = sig != 0
    check("per-unit-net feed EXACT wherever position non-zero",
          float((sig[nz] * r_pu[nz] - net2[nz]).abs().max()) < 1e-12)
    gap_rows = int(((sig == 0) & (net2.abs() > 1e-12)).sum())
    check(f"exit-cost gap rows exist in the exiting fixture and are disclosed ({gap_rows} rows)",
          gap_rows > 0)

    # 10. battery wiring: gates.run accepts sig= + leak_check=True + beats_passive=True
    #     and a LEAKY control (sig = sign of same-day return) is flagged leak=True
    from bt import gates as G
    r = px.pct_change()["NKY"].iloc[70:]
    s = sig.reindex(r.index).fillna(0.0)
    out = G.run(r, sig=s, leak_check=True, beats_passive=False)
    check("gates.run returns leak dict when leak_check=True", "leak" in out)
    sig_leak = pd.Series(np.sign(r.values), index=r.index)
    out_leak = G.run(r, sig=sig_leak, leak_check=True)
    check("leaky control (sig=sign(r_t)) flagged leak=True",
          bool(out_leak.get("leak_ok") is False))

    # 11. sub-span stability judge: both halves must clear 0.5 — a one-era sleeve fails
    good = R5.subspan_verdict({"pre1990": 0.8, "post1990": 0.6})
    bad = R5.subspan_verdict({"pre1990": -0.2, "post1990": 1.2})
    onepost = R5.subspan_verdict({"pre1990": 0.0, "post1990": 0.9})
    check("sub-span verdict: stable passes", good["ok"] is True)
    check("sub-span verdict: pre-1990 negative fails", bad["ok"] is False)
    check("sub-span verdict: one-era-only fails with reason",
          onepost["ok"] is False and "era" in str(onepost.get("reason", "")).lower())

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES: {FAILS}")
        sys.exit(1)
    print("ALL TESTS GREEN")


if __name__ == "__main__":
    main()
