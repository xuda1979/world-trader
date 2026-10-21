#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 3 reproducible scan (charter: every claim reproduces from a saved script).

Usage:
  python3 scripts/hunt_vol2_round3_scan.py            # main ladder + adversarial control
  python3 scripts/hunt_vol2_round3_scan.py --relever  # re-lever-to-1.6-cap variant
  python3 scripts/hunt_vol2_round3_scan.py --screen   # candidate screen only
"""
import sys
from pathlib import Path

CAMP = Path("/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, str(CAMP))
sys.path.insert(0, str(CAMP / "agents/chief/coord/HUNT_VOL2/work_r3"))

import blend_r3_lib as L  # noqa: E402

OUT = CAMP / "agents/chief/coord/HUNT_VOL2/work_r3"


def relever_scan():
    """Variant that re-levers every blend to gross exactly 1.6 (k=1.6/gross), charging the
    margin delta to the full-book convention. Closes the 'did you try re-levering to the
    cap' loophole on the no-adopt verdict."""
    from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
    ch = L.load_champion()
    out = []
    for name in L.ADMITTED:
        s = L.load_ret(L.POOL[name][0])
        f0 = L.first_nonzero_index(s)
        if s.reindex(ch.index).isna().any():
            idx = L.overlap_index(ch, s)
            net_c, net_s = ch.reindex(idx), L.sleeve_on_champion_calendar(s, idx)
        else:
            net_c, net_s = ch, s
        h1c, h2c = L._halves(net_c)
        for w in L.W_LADDER:
            g = L.blend_gross_of(w, 1.6, 1.0)
            k = 1.6 / g
            to = L.blend_drift_turnover(net_c, net_s, w)
            B = L.blend_exact(net_c, net_s, w) - to * L.BPS / 1e4
            base_margin = L.blend_margin_daily(w, 1.6, 1.0)
            full_margin = max(1.6 - 1, 0) * L.RATE / L.ANN
            Bk = k * B - (full_margin - base_margin)
            d_ann = (ann_geo(Bk) - ann_geo(net_c)) * 100
            d_sr = sharpe_d(Bk) - sharpe_d(net_c)
            d_mdd = (max_dd(Bk) - max_dd(net_c)) * 100
            neg, worst = neg_years(Bk)
            dh1 = sharpe_d(Bk.iloc[:len(Bk) // 2]) - h1c
            dh2 = sharpe_d(Bk.iloc[len(Bk) // 2:]) - h2c
            ok = (d_ann > 0 and d_sr >= 0 and dh1 > 0 and dh2 > 0 and neg == 0
                  and max_dd(Bk) > -0.07 and worst > 0)
            out.append(dict(candidate=name, w=w, k=k, d_ann_pp=d_ann, d_sr=d_sr,
                            d_mdd_pp=d_mdd, neg_years=neg, worst_year=worst * 100,
                            d_h1=dh1, d_h2=dh2, verdict="PASS" if ok else "FAIL"))
    df = pd.DataFrame(out)
    df.to_csv(OUT / "relever_scan.csv", index=False)
    return df


if __name__ == "__main__":
    import pandas as pd
    if "--relever" in sys.argv:
        df = relever_scan()
        print(df.round(4).to_string(index=False))
        print("\nPASS rows:", int((df.verdict == "PASS").sum()), "/", len(df))
    elif "--screen" in sys.argv:
        import json
        print(json.dumps(L.screen_pool(), indent=2, default=str))
    else:
        tbl, rec = L.run_round3(out_dir=OUT, quick=False, n_nulls=200, seed=20260907)
        pd.set_option("display.width", 300)
        print(tbl.round(4).to_string(index=False))
        print("\nVERDICT:", rec["verdict"], "adopt:", rec["adopt"])
        for n, g in rec["gates"].items():
            print(f"  {n:11s} {g['verdict']:24s} blocking={g['blocking']}")
