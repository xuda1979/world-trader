#!/usr/bin/env python3
"""CAMP_SHORT R2(b): measure per-slot short-fraction streams for the RAW-EW13v2 champion.

Method: reconstruct each slot's POSITION stream from its committed builder, derive
short_notional_t = |pos_t| * scale_t (vt applied), and VALIDATE the reconstruction by
re-netting and comparing to the committed sleeve CSV (max|diff| < 2e-4 tolerance for
float/CSV round-trip; exact match required for mtimes/floors where applicable).

Slots whose builder is NOT byte-exact reconstructable get a bounded upper-bound treatment
instead (documented per slot). Output: work_r2/short_frac_<slot>.csv (+ a summary dict).
"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader')
import numpy as np, pandas as pd

ROOT = '/Users/daxu/software/world-trader'
sys.path.insert(0, f'{ROOT}/campaign')
sys.path.insert(0, f'{ROOT}/campaign/agents/B2_highfreq')
sys.path.insert(0, f'{ROOT}/campaign/agents/A3_xs_quality')

OUT = f'{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r2'


def load_sleeve(p):
    df = pd.read_csv(f'{ROOT}/{p}', index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)


def save(name, s):
    s.to_frame('short_frac').to_csv(f'{OUT}/short_frac_{name}.csv')


def report(name, sn, committed=None):
    ann_frac = sn.mean()
    days_on = int((sn > 1e-9).sum())
    if committed is not None:
        print(f"  {name}: mean_short_frac={ann_frac:.6f} days_on={days_on} "
              f"({100*days_on/len(sn):.1f}%) n={len(sn)}")
    else:
        print(f"  {name}: mean_short_frac={ann_frac:.6f} days_on={days_on} "
              f"({100*days_on/len(sn):%})" if False else
              f"  {name}: mean_short_frac={ann_frac:.6f} days_on={days_on} n={len(sn)}")


# ---- slot: brwt15/brwt10/brwt7/brwt5 — Brent-WTI spread z-rev, pos in {-1,0,+1}, vt-scaled
def brwt_short_frac(lookback, gate, min_start):
    from campaign.harness.data import fred
    from campaign.agents.B2_highfreq.gates import vol_target
    BR = fred('brent').dropna(); WT = fred('wti_full').dropna()
    sp = (np.log(BR) - np.log(WT)).dropna()
    sp = sp[sp.index >= min_start]
    z = (sp - sp.rolling(lookback, min_periods=lookback).mean()) / \
        sp.rolling(lookback, min_periods=lookback).std().replace(0, np.nan)
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0
    pos[z > gate] = -1.0
    ret = sp.diff().shift(-1)
    gr = pos * ret
    tup = (pos.diff().abs() / 2.0).reindex(gr.index).backfill  # placeholder line, replaced below
    return None


def brwt_reconstruct(lookback, gate, min_start, name):
    """Full reconstruction returning (net, short_frac_stream) + validation print."""
    from campaign.harness.data import fred
    from campaign.agents B2_highfreq.gates import vol_target  # syntax guard, replaced
    return None


def committed_match(net, committed, tol=2e-4):
    j = pd.concat([committed.rename('c'), net.rename('n')], axis=1, join='inner').dropna()
    if len(j) == 0:
        return None, 0
    return float((j.c - j.n).abs().max()), len(j)


def main():
    print("== CAMP_SHORT R2(b): per-slot short-fraction measurement ==")
    # NOTE: this script is a scratch recon harness; final numbers in FINDINGS are produced
    # by the TDD-pinned ladder arithmetic on these streams.


if __name__ == '__main__':
    main()
