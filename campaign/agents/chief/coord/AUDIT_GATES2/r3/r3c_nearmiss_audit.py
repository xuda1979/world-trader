#!/usr/bin/env python3
"""AUDIT_GATES2 ROUND 3 (c): re-calibrate bt.gates on the near-miss library.

Scope discipline (charter R3): every sleeve below is a PUBLISHED artifact of an
already-DEAD family (results/DEAD_IDEAS.csv). This script does NOT re-hunt, re-tune,
or re-run any builder — it loads each published [date,ret] CSV, re-computes every
deterministic gate metric with bt.metrics/bt.gates, and compares to what the sleeve's
own .csv.meta claims. Escalation criterion: any meta number contradicted by its CSV.

The scramble claim is audited for VERIFIABILITY, not re-run: published nets carry no
positions, and gates.run fails closed (scr_p=NaN) on missing sig by design (R2). A
scramble_p in a meta whose builder output (positions) was not preserved is flagged
UNVERIFIABLE_FROM_ARTIFACT — a v2-contract finding, not a mis-statement.

Also runs the beats_passive gate (bt.beats_passive) on each sleeve's own span — the
v2 draft makes it mandatory, so the near-miss library is the calibration set for how
many dead sleeves it would also have caught.

Usage: python3 campaign/agents/chief/coord/AUDIT_GATES2/r3/r3c_nearmiss_audit.py
"""
from __future__ import annotations
import sys, json, re, glob

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")

import numpy as np
import pandas as pd
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo, max_dd
from bt.gates import run as gates_run, corr_to
from bt.beats_passive import gate as beats_passive_gate

CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# SR 0.50-0.70 published sleeves (from the meta inventory, see FINDINGS R3)
NEARMISS = [
    ("HUNT_SECTOR2",       "A_rs_ratio.csv"),
    ("HUNT_SECTOR2",       "A11_rs_ratio#lb126k4.csv"),
    ("HUNT_SECTOR2",       "B_barbell.csv"),
    ("HUNT_SECTOR2",       "D_xlu_ief.csv"),
    ("HUNT_SECTOR2",       "COMP_50_50_daily.csv"),
    ("HUNT_SECTOR2",       "COMP_50_50_monthly.csv"),
    ("HUNT_SECTOR2",       "COMP_50_50_never.csv"),
    ("HUNT_SECTOR2",       "COMP_60_40_daily.csv"),
    ("HUNT_CMDT2",         "CMDT_SectorRot_6m_h2_LS.csv"),
    ("HUNT_CRYPTO2",       "CRYPTO_VolX_20-60_EW12.csv"),
    ("HUNT_INTERNATIONAL2","INTL_R2_RS252_LS.csv"),
]

# meta parsing: key=value lines, tolerant of both 'SR=0.534' and 'sr=0.534' and inline prose
KEYMAP = dict(sr=['sr', 'SR'], h1=['h1', 'H1'], h2=['h2', 'H2'], negy=['neg_yr', 'negyrs', 'negyr'],
              worst=['worst', 'worstyr', 'worstyr'], corr=['corr_champ'], scrp=['scramble_p'],
              vol=['vol'], ann=['ann'])
NUM = r'(-?\d+(?:\.\d+)?)'


def parse_meta(path: str) -> dict:
    txt = open(path).read()
    out = {}
    for canon, keys in KEYMAP.items():
        for k in keys:
            m = re.search(rf'(?<![\w.-]){re.escape(k)}\s*=\s*{NUM}\s*(%)?', txt)
            if m:
                v = float(m.group(1))
                # unit fix: percent-style metas state ann/vol/worst in percent. '%' sign is
                # authoritative; else magnitude: a worst YEAR of |frac|>1.0 is ruin (impossible)
                # so it must be percent (A11 worst=-1.3 == -1.3%). ann/vol keep the 1.5 bound.
                bound = 1.0 if canon == 'worst' else 1.5
                if canon in ('ann', 'worst', 'vol') and (m.group(2) == '%' or abs(v) > bound):
                    v = v / 100.0
                out[canon] = v
                break
    # prose forms used by INTL_R2 metas ('7 neg years FAIL', 'corr to champion -0.033')
    if 'negy' not in out:
        m = re.search(rf'{NUM}\s*neg years', txt)
        if m:
            out['negy'] = float(m.group(1))
    if 'corr' not in out:
        m = re.search(rf'corr (?:to|vs) (?:the )?champion\s*{NUM}', txt)
        if m:
            out['corr'] = float(m.group(1))
    v = re.search(r'verdict=(\S*)', txt)
    if v:
        out['verdict'] = v.group(1)
    return out


def load_ret(agent: str, fname: str) -> pd.Series:
    p = f"{ROOT}/campaign/agents/chief/coord/{agent}/sleeves/{fname}"
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    c = 'ret' if 'ret' in df.columns else df.columns[0]
    return df[c].astype(float)


def pct(x, digits=4):
    return "nan" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x*100:.{digits}f}%"


def audit_one(agent, fname, champ) -> dict:
    r = load_ret(agent, fname).dropna()
    m = parse_meta(f"{ROOT}/campaign/agents/chief/coord/{agent}/sleeves/{fname}.meta")
    sr, (h1, h2) = sharpe_d(r), half_split(r)
    neg, worst = neg_years(r)
    corr = corr_to(champ, r)
    g = gates_run(r, ref=champ)          # no sig -> scr fails closed BY DESIGN
    flags = []

    def check(label, claimed, actual, tol):
        if claimed is None:
            flags.append(f"{label}: meta does not state it (measured {actual:.4f})")
        elif abs(claimed - actual) > tol:
            flags.append(f"{label}: meta {claimed:.4f} vs CSV {actual:.4f} (|d|={abs(claimed-actual):.4f} > {tol})")

    check('sr', m.get('sr'), sr, 0.005)
    check('h1', m.get('h1'), h1, 0.02)
    check('h2', m.get('h2'), h2, 0.02)
    check('neg_years', m.get('negy'), float(neg), 0.5)
    check('corr_champ', m.get('corr'), corr, 0.003)
    if m.get('scrp') is not None:
        flags.append(f"scramble_p={m['scrp']:.3f} UNVERIFIABLE_FROM_ARTIFACT (positions not published; "
                     f"gates.run scr_p=NaN fail-closed)")
    if m.get('worst') is not None:
        cw = m['worst']
        if cw > 1.5:  # stated in percent
            cw = cw / 100.0
        if abs(cw - worst) > 0.005:
            flags.append(f"worst_year: meta {cw:.4f} vs CSV {worst:.4f}")

    # v2 preview: beats-passive on the sleeve's own span (needs SPY/IEF/CTA benchmarks)
    try:
        bp = beats_passive_gate(r)
        bp_ok, bp_why = bp['beats_passive_ok'], bp.get('detail', bp)
    except Exception as e:                   # missing benchmark data -> fail closed, note it
        bp_ok, bp_why = False, f"ERROR:{type(e).__name__}:{e}"
    return dict(agent=agent, name=fname.replace('.csv', ''), n=len(r),
                start=str(r.index[0].date()), end=str(r.index[-1].date()),
                sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, corr=corr,
                mdd=max_dd(r), ann=ann_geo(r),
                gates_pass=bool(g['pass']), g_sr_ok=g['sr_ok'], g_halves_ok=g['halves_ok'],
                g_neg_ok=g['neg_ok'], g_corr_ok=g['corr_ok'], scr_p=g['scr_p'],
                bp_ok=bool(bp_ok), bp=bp_why,
                meta_verdict=m.get('verdict', ''), flags=flags)


def main():
    champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    print(f"champion ref: SR={sharpe_d(champ):.4f} n={len(champ)}")
    rows = [audit_one(a, f, champ) for a, f in NEARMISS]
    print(f"\n{'sleeve':<34}{'n':>6}{'SR':>8}{'H1':>7}{'H2':>7}{'neg':>4}{'corr':>8}  "
          f"gates pass  bp  flags")
    for x in rows:
        fl = '; '.join(x['flags']) if x['flags'] else '-'
        print(f"{x['name'][:33]:<34}{x['n']:>6}{x['sr']:>8.3f}{x['h1']:>7.2f}{x['h2']:>7.2f}"
              f"{x['neg']:>4}{x['corr']:>8.3f}  {str(x['gates_pass']):<10} {str(x['bp_ok']):<5} {fl}")
    nflag = sum(1 for x in rows if x['flags'])
    print(f"\naudited={len(rows)} sleeves_with_flags={nflag}")
    json.dump(rows, open(f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r3/r3c_results.json", "w"),
              indent=1, default=float)
    print("saved r3c_results.json")


if __name__ == '__main__':
    main()
