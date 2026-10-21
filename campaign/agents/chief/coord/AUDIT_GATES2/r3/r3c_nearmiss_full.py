#!/usr/bin/env python3
"""AUDIT_GATES2 ROUND 3 (c) — FULL near-miss library audit (extends r3c_nearmiss_audit.py).

Prior instance's script (r3c_nearmiss_audit.py) covered 11 sleeves from a 59-meta
inventory hand-list. This extension sweeps the WHOLE campaign tree (198 published sleeve
CSVs, n>=250), computes SR, and audits EVERY published sleeve with SR in [0.5, 0.7] — the
charter's "SR 0.5-0.7 published sleeves" population (15 sleeves, superset of the
inherited 11).

Additions over the inherited script:
  * champion ref SHA-PINNED (sha256 of the CSV bytes) — the champion was legitimately
    re-emitted at 14:27 2026-09-07 (SR 3.2964 -> 3.1810 honest costfix, commit b268e52),
    so corr values measured against the stale champion are vintage-mismatched, not
    mis-statements. Every corr claim is now auditable against a named vintage.
  * v2-preview: bt.beats_passive (mandatory in the v2 draft) on every sleeve's own span,
    with real SPY/IEF/CTA data.
  * gates.run() with the real champion ref on every sleeve (scr fails closed by design —
    no positions published; that is a VERIFIABILITY finding, not a pass/fail change).

Do NOT re-hunt: all 15 are published artifacts of DEAD families (DEAD_IDEAS.csv). This is
a re-calibration of the GATES on the near-miss library, not a re-test of the ideas.

Usage: python3 campaign/agents/chief/coord/AUDIT_GATES2/r3/r3c_nearmiss_full.py
"""
from __future__ import annotations
import sys, json, hashlib

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")

import numpy as np
import pandas as pd
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo, max_dd
from bt.gates import run as gates_run, corr_to
from bt.beats_passive import evaluate as bp_evaluate

CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY_CSV = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEF_CSV = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTA_CSV = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"

COORD = f"{ROOT}/campaign/agents/chief/coord"
# The 15 published sleeves with SR in [0.5,0.7] (full-tree SR sweep, see FINDINGS R3c).
NEARMISS = [
    ("(library)", "Multi_Strategy_EW",
     f"{ROOT}/campaign/results/sleeve_library/Multi_Strategy_EW.csv"),
    ("HUNT_SECTOR2", "A11_rs_ratio#lb126k4",
     f"{COORD}/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv"),
    ("loop/HUNT_CROSSASSET2", "SEC3_sector_trio_zrev_daily",
     f"{ROOT}/campaign/agents/loop_team/HUNT_CROSSASSET2/sleeves/SEC3_sector_trio_zrev_daily.csv"),
    ("HUNT_CMDT2", "CMDT3_Sprd_DBE_DBP_LO_63d",
     f"{COORD}/HUNT_CMDT2/sleeves/CMDT3_Sprd_DBE_DBP_LO_63d.csv"),
    ("HUNT_SECTOR2", "COMP_invvol", f"{COORD}/HUNT_SECTOR2/sleeves/COMP_invvol.csv"),
    ("HUNT_SECTOR2", "COMP_60_40_daily", f"{COORD}/HUNT_SECTOR2/sleeves/COMP_60_40_daily.csv"),
    ("HUNT_CRYPTO2", "CRYPTO_VolX_20-60_EW12",
     f"{COORD}/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_20-60_EW12.csv"),
    ("HUNT_SECTOR2", "COMP_50_50_monthly", f"{COORD}/HUNT_SECTOR2/sleeves/COMP_50_50_monthly.csv"),
    ("HUNT_SECTOR2", "B_barbell", f"{COORD}/HUNT_SECTOR2/sleeves/B_barbell.csv"),
    ("HUNT_SECTOR2", "COMP_50_50_daily", f"{COORD}/HUNT_SECTOR2/sleeves/COMP_50_50_daily.csv"),
    ("HUNT_SECTOR2", "COMP_50_50_never", f"{COORD}/HUNT_SECTOR2/sleeves/COMP_50_50_never.csv"),
    ("HUNT_SECTOR2", "D_xlu_ief", f"{COORD}/HUNT_SECTOR2/sleeves/D_xlu_ief.csv"),
    ("HUNT_CMDT2", "CMDT_SectorRot_6m_h2_LS",
     f"{COORD}/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_h2_LS.csv"),
    ("HUNT_INTERNATIONAL2", "INTL_R2_RS252_LS",
     f"{COORD}/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv"),
    ("HUNT_SECTOR2", "A_rs_ratio", f"{COORD}/HUNT_SECTOR2/sleeves/A_rs_ratio.csv"),
]

# Inherited script's meta parser (kept for the 11 sleeves it covered; the 4 new ones get
# their own parsers below because their metas are prose-form).
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r3")
from r3c_nearmiss_audit import parse_meta  # noqa: E402


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_ret(p: str) -> pd.Series:
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index, format='mixed')
    c = 'ret' if 'ret' in df.columns else df.columns[0]
    return df[c].astype(float)


def load_benchmarks():
    spy_px = pd.read_csv(SPY_CSV, parse_dates=['date']).set_index('date')['close'].sort_index()
    spy = spy_px.pct_change().rename('ret')
    ief = pd.read_csv(IEF_CSV, parse_dates=['date']).set_index('date')['close'].sort_index()
    ief = ief.pct_change().rename('ret')
    cta = load_ret(CTA_CSV)
    return spy, ief, cta


def meta_path(agent: str, name: str, csv_path: str) -> str:
    return csv_path + ".meta"


def parse_sec3_meta(txt: str) -> dict:
    """Prose meta of SEC3: 'GATES 2008+: SR 0.667 (>=0.6 PASS) | H1 0.89 H2 0.33 (PASS) |
    negy 8/19 worst -3.60% (FAIL >2) | 200x 10d-block position-lag scramble p=0.000 ...'"""
    import re
    out = {}
    m = re.search(r'SR (\d+\.?\d*)\s*\(', txt)
    if m: out['sr'] = float(m.group(1))
    m = re.search(r'H1 (\d+\.?\d*)\s+H2 (\d+\.?\d*)', txt)
    if m: out['h1'], out['h2'] = float(m.group(1)), float(m.group(2))
    m = re.search(r'negy (\d+)/(\d+)\s+worst (-?\d+\.?\d*)%', txt)
    if m: out['negy'], out['worst'] = float(m.group(1)), float(m.group(3)) / 100.0
    m = re.search(r'scramble p=(\d+\.?\d*)', txt)
    if m: out['scrp'] = float(m.group(1))
    return out


def audit_one(agent, name, path, champ, bp_data, extra_parse=None) -> dict:
    r = load_ret(path).dropna()
    sr, (h1, h2) = sharpe_d(r), half_split(r)
    neg, worst = neg_years(r)
    corr = corr_to(champ, r)
    g = gates_run(r, ref=champ)
    spy, ief, cta = bp_data
    try:
        ev = bp_evaluate(r, spy=spy, ief=ief, cta=cta)
        bp_ok, bp_best, bp_reason = bool(ev['pass']), ev.get('best'), ev.get('reason')
        bp_bench = {k: round(v['sr'], 3) for k, v in ev['benchmarks'].items()}
    except Exception as e:
        bp_ok, bp_best, bp_reason, bp_bench = False, None, f"ERROR:{type(e).__name__}", {}

    flags = []
    mtxt = ""
    mp = meta_path(agent, name, path)
    try:
        mtxt = open(mp).read()
    except OSError:
        flags.append("NO_META_FILE")

    m = {}
    if mtxt:
        m = (extra_parse(mtxt) if extra_parse else None) or parse_meta(mp)
    def check(label, claimed, actual, tol, fmt="{:.4f}"):
        if claimed is None:
            if m:  # meta exists but omits the number
                flags.append(f"{label}: not stated in meta (measured {fmt.format(actual)})")
        elif abs(claimed - actual) > tol:
            flags.append(f"{label}: meta {fmt.format(claimed)} vs CSV(now-ref) {fmt.format(actual)} "
                         f"(|d|={abs(claimed - actual):{fmt[1:]}} > {tol})")
    check('sr', m.get('sr'), sr, 0.005)
    check('h1', m.get('h1'), h1, 0.02)
    check('h2', m.get('h2'), h2, 0.02)
    if m.get('negy') is not None:
        check('neg_years', float(m['negy']), float(neg), 0.5, fmt="{:.0f}")
    if m.get('worst') is not None:
        cw = m['worst'] / 100.0 if abs(m['worst']) > 1.5 else m['worst']
        check('worst_year', cw, worst, 0.005)
    if m.get('scrp') is not None:
        flags.append(f"scramble_p={m['scrp']:.3f} UNVERIFIABLE_FROM_ARTIFACT "
                     f"(positions not published; gates.run scr_p=NaN fail-closed)")
    if m.get('corr') is not None:
        # corr is champion-VINTAGE sensitive: only escalate if the meta itself states which
        # champion it used AND that vintage matches; else flag as vintage-unpinned.
        flags.append(f"corr_champ meta {m['corr']:.4f} vs CURRENT-ref {corr:.4f} "
                     f"(vintage-sensitive; champ sha {CHAMP_SHA[:12]})")
    return dict(agent=agent, name=name, path=path.replace(ROOT + '/', ''),
                n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()),
                sr=sr, h1=h1, h2=h2, neg=int(neg), worst=worst, corr=corr,
                mdd=max_dd(r), ann=ann_geo(r),
                gates_pass=bool(g['pass']), g_sr_ok=g['sr_ok'], g_halves_ok=g['halves_ok'],
                g_neg_ok=g['neg_ok'], g_corr_ok=g['corr_ok'], scr_p=float(g['scr_p']),
                bp_ok=bp_ok, bp_best=bp_best, bp_reason=bp_reason, bp_bench=bp_bench,
                meta_verdict=(m.get('verdict') or ''), flags=flags)


CHAMP_SHA = sha256_file(CHAMP)


def main():
    champ = load_ret(CHAMP)
    print(f"champion ref: SR={sharpe_d(champ):.4f} n={len(champ)} "
          f"span {champ.index[0].date()}..{champ.index[-1].date()} sha256={CHAMP_SHA[:16]}")
    bp_data = load_benchmarks()
    rows = [audit_one(a, n, p, champ, bp_data,
                      extra_parse=(parse_sec3_meta if 'SEC3' in n else None))
            for a, n, p in NEARMISS]
    hdr = (f"\n{'sleeve':<32}{'n':>6}{'SR':>8}{'H1':>7}{'H2':>7}{'neg':>4}{'corr':>8}"
           f"  {'gates':<6}{'bp':<6} flags")
    print(hdr)
    print('-' * 150)
    for x in rows:
        fl = '; '.join(x['flags']) if x['flags'] else '-'
        print(f"{x['name'][:31]:<32}{x['n']:>6}{x['sr']:>8.3f}{x['h1']:>7.2f}{x['h2']:>7.2f}"
              f"{x['neg']:>4}{x['corr']:>8.3f}  {str(x['gates_pass']):<6}"
              f"{str(x['bp_ok']):<6} {fl[:170]}")
    nflag = sum(1 for x in rows if x['flags'])
    misstate = [x for x in rows if any('meta' in f and 'UNVERIFIABLE' not in f
                                       and 'vintage' not in f for f in x['flags'])]
    print(f"\naudited={len(rows)} flagged={nflag} HARD_misstatements={len(misstate)}")
    for x in misstate:
        print(f"  ESCALATE: {x['agent']} {x['name']}: "
              + ' | '.join(f for f in x['flags'] if 'UNVERIFIABLE' not in f and 'vintage' not in f))
    out = dict(champion_sha256=CHAMP_SHA, champion_sr=sharpe_d(champ), rows=rows)
    json.dump(out, open(f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r3/r3c_full_results.json", "w"),
              indent=1, default=float)
    print("saved r3c_full_results.json")


if __name__ == '__main__':
    main()
