#!/usr/bin/env python3
"""pairs_vplus.py -- improve pair portfolio Sharpe using (a) LONGER history and
(b) a risk-off (SPY realized-vol) entry filter.

Root cause of the 6.96 collapse: only ~509 bars/pair (polygon).  The same
tickers exist in twelvedata with ~2001 bars.  We relocate the pair engine onto
the long history AND gate entries with a vol threshold, then validate honestly
on a rolling walk-forward + lag-scramble control.  Cost = 3.8 bps RT.

Usage:
  python pairs_vplus.py            # rolling + scramble on long data, no filter
  python pairs_vplus.py --vlt 0.5  # add SPY 21d-vol risk-off filter
"""
import os, sys, math, time, json, statistics, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import pairs_portfolio_sim as P
import pairs_research_v4 as v4

# ---- (1) redirect _load_series to prefer twelvedata (2001 bars) ----
_ORIG_LOAD = v4._load_series
def _load_long(sym, provider="polygon"):
    td = os.path.join(v4.TD_DIR, sym + ".csv")
    if os.path.exists(td):
        return v4._load_csv(td)
    return _ORIG_LOAD(sym, provider)
v4._load_series = _load_long
P.v4._load_series = _load_long

COST = 3.8
Z = 2.0


def spy_vol21(dates):
    """Realized 21d vol of SPY <- risk-off filter series (point-in-time)."""
    r = _load_long("SPY")
    if not r:
        return None
    d, c = r
    cdate = set(dates)
    rets = [0.0]
    for i in range(1, len(c)):
        rets.append((c[i] - c[i-1]) / c[i-1] if c[i-1] > 0 else 0.0)
    vol = {}
    for i in range(20, len(c)):
        w = rets[i-20:i+1]
        m = sum(w)/len(w)
        v = math.sqrt(sum((x-m)**2 for x in w)/len(w)) * math.sqrt(252)
        vol[d[i]] = v
    return vol


def gated_replay(pair, z_entry, vol_series, vlt_cut, open_from=0,
                 lookback=None, horizon=None):
    """Like sim replay_pair but blocks ENTRIES on days where SPY 21d-vol is
    above `vlt_cut` (annualized vol threshold).  Exits are not gated."""
    spread = pair["spread"]; dates = pair["dates"]; N = len(spread)
    if lookback is None:
        lookback = max(v4.HL_LOOKBACK_MIN, min(v4.HL_LOOKBACK_MAX, int(pair["hl"]*3)))
    if horizon is None:
        horizon = max(v4.HL_HORIZON_MIN, min(v4.HL_HORIZON_MAX, int(pair["hl"]*1)))
    trades = []; pos = None
    for i in range(lookback, N-1):
        m, sd = P._roll(i, lookback, spread)
        if sd <= 0: continue
        z = (spread[i]-m)/sd
        blocked = (vol_series is not None and vlt_cut is not None and
                   dates[i] in vol_series and vol_series[dates[i]] >= vlt_cut)
        if pos is None:
            if (i >= open_from and abs(z) >= z_entry and not blocked):
                pos = (1 if z < 0 else -1, i, sd, spread[i])
            continue
        side, ei, esd, entry_val = pos
        if i == ei: continue
        d_stdev = (spread[i]-entry_val)/esd
        exit_idx = None
        if side*d_stdev >= 1.0: exit_idx = i
        elif side*d_stdev <= -2.0: exit_idx = i
        elif i - ei >= horizon: exit_idx = i
        if exit_idx is not None:
            daily = [side*(spread[k]-spread[k-1])/esd for k in range(ei+1, exit_idx+1)]
            trades.append({"side":side,"entry_idx":ei,"exit_idx":exit_idx,
                           "sigma_net":sum(daily),"daily":daily,"entry_sd":esd})
            pos = None
    return trades, lookback, horizon


def build_long_data():
    """Rebuild all_data on the LONG twelvedata history."""
    all_data = {}
    ok = 0
    for p in P.build_universe():
        label, ac, sym_a, sym_b, kind, provider = p
        try:
            d = P._pair_data(label, ac, sym_a, sym_b, kind, provider)
        except Exception:
            d = None
        if d and len(d["spread"]) > 400:
            all_data[label] = d; ok += 1
    return all_data, ok


def rolling(long_data, vol_series, vlt_cut, is_bars, step, seed=None):
    """Rolling WF on long data. seed -> scramble (lag) via _pair_data."""
    if seed is not None:
        P._SCRAMBLE_SEED = seed
        all_data, _ = build_long_data()
        P._SCRAMBLE_SEED = None
    else:
        all_data = long_data
    lens = sorted(len(pr["dates"]) for pr in all_data.values())
    med = lens[len(lens)//2]
    med_dates = sorted({d for pr in all_data.values() for d in pr["dates"]})
    # use first large pair calendar as med proxy
    ks = sorted(all_data.keys(), key=lambda l: -len(all_data[l]["dates"]))
    med_dates = all_data[ks[0]]["dates"]
    if len(med_dates) < is_bars + 10:
        return None
    n_eps = max(1, (len(med_dates) - is_bars)//step)
    recs = []
    for e in range(n_eps):
        q0 = med_dates[is_bars + e*step]
        q1 = med_dates[min(is_bars + (e+1)*step, len(med_dates)-1)]
        ql = []
        for label, pr in all_data.items():
            n_is = sum(1 for d in pr["dates"] if d < q0)
            if n_is < 100: continue
            q = P.wf_qualify(pr["spread"][:n_is],
                             [math.log(v) for v in pr["a"][:n_is]],
                             [math.log(v) for v in pr["b"][:n_is]],
                             n_tests=len(all_data))
            if q:
                all_data[label]["lookback"]=q["lookback"]; all_data[label]["horizon"]=q["horizon"]
                ql.append(label)
        for label in ql:
            pr = all_data[label]
            of = next((i for i,d in enumerate(pr["dates"]) if d>=q0), len(pr["dates"]))
            ou = next((i for i,d in enumerate(pr["dates"]) if d>=q1), len(pr["dates"]))
            tr,_,_ = gated_replay(pr, Z, vol_series, vlt_cut, of,
                                  lookback=pr.get("lookback"), horizon=pr.get("horizon"))
            for t in tr: recs.append((label,t))
    if not recs:
        return None
    by = {}
    for label,t in recs: by.setdefault(label,[]).append(t)
    prs = [{**all_data[label], "dates": all_data[label]["dates"], "trades": trs}
           for label,trs in by.items()]
    agg = P._aggregate(prs, COST)
    if agg is None: return None
    cal = agg["cal"]; i0 = next((i for i,d in enumerate(cal) if d>=med_dates[is_bars]), len(cal))
    return {"cal": cal[i0:], "net": agg["net"][i0:], "gross": agg["gross"][i0:],
            "per_pair": agg["per_pair"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vlt", type=float, default=None, help="SPY 21d-vol cutoff (annualized)")
    ap.add_argument("--is-bars", type=int, default=400)
    ap.add_argument("--step", type=int, default=120)
    ap.add_argument("--nscram", type=int, default=6)
    args = ap.parse_args()

    t0 = time.time()
    long_data, n_ok = build_long_data()
    vol = spy_vol21(list(long_data[list(long_data)[0]]["dates"]))
    print(f"long-history pairs with data: {n_ok}  (twelvedata ~2001 bars)")
    print(f"SPY 21d-vol: {len(vol) if vol else 0} days trackable | vlt_cut={args.vlt}")

    real = rolling(long_data, vol, args.vlt, args.is_bars, args.step)
    mg = P.metrics(real["net"], len(real["net"]), cal=real["cal"])["ALL"]["sharpe"] if real else None
    mgr = P.metrics(real["gross"], len(real["gross"]), cal=real["cal"])["ALL"]["sharpe"] if real else None
    print(f"\n=== ROLLING (IS={args.is_bars} step={args.step}) net={mg:.3f} gross={mgr:.3f} "
          f"days={len(real['cal']) if real else 0} ===")

    scram = []
    for seed in range(1, args.nscram+1):
        sr = rolling(long_data, vol, args.vlt, args.is_bars, args.step, seed=seed)
        if sr:
            s = P.metrics(sr["net"], len(sr["net"]), cal=sr["cal"])["ALL"]["sharpe"]
            scram.append(s)
    if scram:
        mu=statistics.fmean(scram); sd=statistics.stdev(scram) if len(scram)>1 else 0
        print(f"scramble n={len(scram)} mean={mu:.3f} sd={sd:.3f} max={max(scram):.3f}")
        if mg is not None and sd>0:
            print(f"real z vs scramble = {(mg-mu)/sd:.2f}")
    print(f"\nWrote / elapsed {time.time()-t0:.0f}s")
    # save
    json.dump({"vlt_cut":args.vlt,"is_bars":args.is_bars,"step":args.step,
               "real_net_sharpe":mg,"real_gross_sharpe":mgr,
               "n_long_pairs":n_ok,"n_scramble":len(scram),
               "scram_mean":round(statistics.fmean(scram),3) if scram else None,
               "scram_sd":round(statistics.stdev(scram),3) if len(scram)>1 else None,
               "scram_max":round(max(scram),3) if scram else None,
               "real_z":round((mg-statistics.fmean(scram))/statistics.stdev(scram),2)
                 if (mg is not None and len(scram)>1 and statistics.stdev(scram)>0) else None},
              open("tools/quant/reports/pairs_vplus.json","w"),indent=1,default=str)


if __name__ == "__main__":
    main()
