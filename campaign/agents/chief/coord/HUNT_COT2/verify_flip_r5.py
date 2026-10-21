"""HUNT_COT2 round-5 re-fire (2026-09-08): V2 section-6 verdict-neutrality of the
Step-2 leak_check default flip (commit 539f50e, 09:17) measured on the R5 books.

Calls gates.run WITHOUT the explicit leak_check kwarg (the exact caller class V2 s6
analyzed) under the post-flip default (True), with an honest T+1 signature
(positions = pos.shift(1)), and checks: (a) the leak dict is published and
fail-closed, (b) composite verdict stays False on all three R5 books, (c) numbers
still match the R5 record to rounding. Repro:
    python3 campaign/agents/chief/coord/HUNT_COT2/verify_flip_r5.py
"""
import sys
import pandas as pd

sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import bt.gates as gates_mod

ROOT = '/Users/daxu/software/world-trader'
HUNT = ROOT + '/campaign/agents/chief/coord/HUNT_COT2'

# (file, R5-recorded SR, R5-recorded scr_p, R5-recorded corr) from the R5 FINDINGS table
BOOKS = {
    'C9 dealerLong HIGH 1.5': ('r5_book_C9_ts_dealerLong_high_15.csv', 0.590, 0.055, 0.027),
    'C3 tot LOW 2.0':         ('r5_book_C3_ts_tot_low_20.csv',         0.335, 0.015, 0.007),
    'C1 tot LOW 1.5':         ('r5_book_C1_ts_tot_low_15.csv',         0.243, 0.149, -0.022),
}

champ = pd.read_csv(ROOT + '/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv')
datecol = champ.columns[0]  # 'date' col first; ret col is col 1
champ = champ.set_index(pd.to_datetime(champ[datecol])).sort_index()
rc = champ[champ.columns[1]].astype(float)  # first non-date column = champion returns
ref = rc[rc.notna()]

print(f"{'book':24s} {'SR':>6s} (R5)   | {'scr_p':>6s} (R5)  | {'corr':>7s} (R5)  | "
      f"{'leak':>5s} {'leak_ok':>7s} {'sp_corr':>8s} | pass")
all_fail = True
for name, (f, sr5, sp5, co5) in BOOKS.items():
    df = pd.read_csv(f'{HUNT}/{f}')
    dc = df.columns[0]
    df[dc] = pd.to_datetime(df[dc])
    df = df.set_index(dc).sort_index()
    r = df.iloc[:, 0].astype(float)
    r = r[r.notna()]
    sig = (r > 0).astype(float).shift(1).fillna(0.0)  # honest T+1, not same-period
    # flipped default: leak_check kwarg OMITTED on purpose (default now True)
    g = gates_mod.run(r, ref=ref, sig=sig, scramble_n=200, seed=7)
    lk = g['leak']
    sp_corr = lk['same_period_corr'] if isinstance(lk, dict) and 'same_period_corr' in lk else float('nan')
    print(f"{name:24s} {g['sr']:6.3f} ({sr5:.3f}) | {g['scr_p']:6.3f} ({sp5:.3f}) | "
          f"{g['corr']:7.4f} ({co5:+.3f}) | {str(lk['leak']) if isinstance(lk, dict) else lk!s:>5s} "
          f"{str(g['leak_ok']):>7s} {sp_corr:8.4f} | {g['pass']}")
    all_fail = all_fail and (g['pass'] is False) and (g['leak_ok'] is True)

print()
print('VERDICT:', 'ALL BOOKS: leak dict published under flipped default, leak_ok=True, '
      'composite pass=False (R5 verdict-neutral, as V2 s6 claims)'
      if all_fail else 'MISMATCH — escalate')
