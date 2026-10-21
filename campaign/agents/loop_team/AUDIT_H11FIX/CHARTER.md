# AUDIT_H11FIX — ADVERSARIAL AUDIT of the corrected champion GOAL100_HONEST11FIX_* (2026-09-02)

You are an ADVERSARIAL auditor. Assume the new "corrected" champion is WRONG until you prove
otherwise with exact numbers. The coordinator just committed:
  campaign/results/GOAL100_HONEST11FIX_{BALANCED,SAFE,AGGRESSIVE}_daily.csv
built by campaign/scripts/honest11_build.py --fixed with two claimed fixes:
  (1) calendar rows-kept (no inner-join loss; borrow charged skipna on sleeves present),
  (2) vt-overlay rebalance cost charged at 6bps/side on (sum_i |d scale_i|/N + |d global scalar|).

YOUR CHECKS (record exact numbers for each; write campaign/agents/loop_team/AUDIT_H11FIX/FINDINGS.md):
1. REPRODUCE: run `python3 campaign/scripts/honest11_build.py --verify` and `--verify-l16`.
   Do HONEST11 and HONEST11L16 reproduce byte-exactly (max|diff|<1e-12)? Then reproduce HONEST11FIX
   yourself INDEPENDENTLY (write your own code from the sleeve CSVs, do NOT import the builder)
   and compare to the committed FIX files. Report max|diff| and where any difference concentrates.
2. CALENDAR FIX VERIFICATION: n=4989 vs committed-champion 4522. Identify EVERY added row (4989-4616
   warmup + 94 dropped-day recoveries). Are any added rows non-trading days (weekends/federal holidays)?
   The builder uses USFederalHolidayCalendar — check Good Friday and any NYSE-observed-but-not-federal
   days (and vice versa) in the kept rows.
3. COST CHARGE VERIFICATION: recompute the overlay-rebalance turnover independently
   (sum_i |d scale_i|/N + |d global scalar|) and the implied drag. Is ~0.9%/yr on 2008+?
   Is it charged on the right days (T+1-consistent, no lookahead: scale_{t-1} changes are knowable)?
   Try to find a look-ahead: the global scalar is vt(blend,TGT) computed trailing — verify shift(1)
   everywhere (read champion_build.vt).
4. LEVERAGE (REAL): compute capital-real all-in gross = mean_t [sum_i |scale_i,t| * global_t] / N
   on the FIX construction (per-sleeve 0.08 + global 0.07/0.091). Report mean/p95/max per variant,
   and yearly means. State plainly whether "leverage<=1.6" holds under capital-real accounting.
5. GOAL CHECK: ann>=80%? SR>=5 (daily AND monthly)? MaxDD<=7%? profit>=0 in every year 2008+?
   On the FIX numbers: report each verdict with exact figures.
6. ADVERSARIAL SWEEPS: flatten gate (ac1, uniqR) on FIX outputs; worst single-day; T+1 extra-lag
   probe (shift returns +1d, recompute ann/SR/MDD); block-bootstrap SR p-value (200x, 10d blocks);
   leave-one-sleeve-out (11 variants): which single sleeve removal kills 0-neg-years, if any?
7. VERDICT: list every DISCREPANCY found; state PASS/FAIL of each audit gate; and answer:
   is the FIX champion MORE honest than the committed L16 (inner-join)? Any new inflation?

Honesty contract: exact numbers only, no copying coordinator claims, T+1 checks mandatory.
Last line of FINDINGS.md must be exactly: AUDIT_H11FIX DONE
