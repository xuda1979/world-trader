# AUDIT3_calendar — FINDINGS (adversarial audit of natgas weekday sleeves, 2026-09-01)

Auditor: AUDIT3_calendar (read-only; own scratch files only, under `scratch/`).
Scope: C5ng / C5ngsum (+ E1 de-truncated variants) as used in GOAL100_CHAMPION_V4 (21-pool),
GOAL100_CHAMPION (V1, 16-pool) and GOAL100_CHAMPION20Y_V2 (13-pool).
Raw data: `tools/quant/data/newdata/DHHNGSP.csv` (FRED, fetched 2026-09-01 per newdata/README).
My rebuild code: `scratch/rebuild_ng.py`, `scratch/scramble.py` (independent of committed scripts;
only `campaign.agents.B2_highfreq.gates.vol_target` reused, deliberately, to test their helper).

## 0. Data integrity (raw DHHNGSP)
- CSV: 7731 rows, cols [observation_date, DHHNGSP]; after to_numeric/positive/dropna/sort:
  7441 prints, 1997-01-07..2026-08-25; no duplicate dates; no non-positive prices; 290 NaN rows
  (holidays; exactly the 290 missing business days). No weekend prints (Mon 1403/Tue 1533/Wed
  1531/Thu 1503/Fri 1471). Gap structure: 5853x1d, 1331x3d (weekends), 188x4d + 42x2d + 25x5d
  (holidays), one 15d gap (Oct 2-16, 2000-ish federal print halt). CLEAN.
- 641 zero-return prints (flat carry-forward levels), spread evenly Mon 120/Tue 132/Wed 126/
  Thu 130/Fri 133; by era: 126 (1997-2004), 144 (2005-2014), 371 (2015-2026). No
  weekday-specific data artifact; flat prints mildly deflate measured vol, not directional means.
- Largest |log-ret| days: 2024-01-12 +143%, 2024-01-16 +140%, 2026-01-23 +129%, 2021-02-18 +103%.

## 1. Independent rebuild vs committed sleeves — EXACT
Map confirmed from code/metas: **no explicit Mon leg** (charter's "[Mon+, Wed−, Thu−, Fri+]" is
imprecise). Code: pos = −1 on Wed close, −1 on Thu close, +1 on Fri close, 0 otherwise (summer
variant additionally zero for Nov–Mar); calm filter zero when |same-day log ret| > 2.5 × rolling
90d sigma **shift(1)**; pnl = pos × lr.shift(−1); 6e-4 cost × |Δpos|; harness expanding vt10
(min 60d, cap 3x). I rebuilt from raw with my own code:
- C5_ng_weekday_prem.csv: n=4641 (2008-03-28..2026-08-24), corr=1.00000000,
  max|Δ|=9.99e-17 → IDENTICAL (tol 1e-12).
- C5_ng_summer_weekday.csv: n=4641, corr=1.00000000, max|Δ|=9.98e-17 → IDENTICAL.
- E1_C5ng_weekday_prem.csv: n=7381 (1997-04-02..2026-08-24), max|Δ|=9.98e-17 → IDENTICAL.
- E1_C5ng_summer_weekday.csv: n=7381, max|Δ|=9.996e-17 → IDENTICAL.
All four committed weekday-sleeve CSVs regenerate byte-exactly (float64) from raw FRED data.

**T+1 / lookahead audit of the mapping: CLEAN.** Position at close t uses only dayofweek(t),
|lr_t| (day-t print, known at close t) and trailing sigma through t; pnl = next print. The calm
filter legitimately skips the day after extreme prints (uses the shock AFTER it happened).
One methodological wart found (general, not specific to this sleeve): `gates.vol_target`
computes expanding sigma INCLUDING day t, then multiplies r_t by scale_t → 1-bar same-day
feedback. Quantified with an honest shift(1)-sigma variant: C5ng 08+ SR 1.631→1.676 (+0.045),
C5ng 98+ 1.630→1.625, C5ngsum 98+ 2.082→2.070, C5ngsum 08+ 2.192→2.175; on the committed
C5ngsum file exactly: 2.192→2.206. Impact ≤±0.05 SR, both signs — NOT inflating, but the
helper is shared campaign-wide (champion-level `vt()` in both champion builders correctly
uses shift(1) — clean). FLAG (minor).

Stats verification (my rebuild, official convention):
| sleeve | window | n | ann% | vol% | SR | MDD% | negy | worst% | H1 | H2 |
|---|---|---|---|---|---|---|---|---|---|---|
| C5ng | 2008+ | 4641 | 23.1 | 13.3 | 1.74 | −29.5 | 0/19 | +6.3 | 2.18 | 1.55 |
| C5ngsum | 2008+ | 4641 | 27.2 | 12.4 | 2.19 | −11.9 | 0/19 | +5.7 | 1.67 | 2.62 |
| E1 C5ng | 1998+ | 7191 | 19.7 | 12.1 | 1.63 | −31.0 | 0/29 | +1.7 | 1.94 | 1.44 |
| E1 C5ngsum | 1998+ | 7191 | 24.0 | 11.5 | 2.08 | −13.1 | 1/29 | −1.8 | 1.86 | 2.29 |
All match the committed .meta/FINDINGS claims (1.74/2.19/1.63/2.08, MDD −29.5/−11.9/−31.0/−13.1).
2026 YTD: C5ng +7.7%, C5ngsum +19.4% (matches C5 FINDINGS "+7.7/+19.4").

## 2. Multiple-testing risk — weekday t-stats + Bonferroni(5)
Raw print effects (mean log-ret of the print by its weekday) and the strategy convention
(entry at close of day X earns print of X+1 — this is what each leg harvests), 1998-01..2026-08,
n=7192 non-overlapping 1-print holds (t valid apart from vol clustering):
- Same-day convention: Mon +100.4bp/d t=+5.82; Tue +39.1 t=+2.14; Wed +32.9 t=+2.39;
  Thu −47.1 t=−3.22; Fri −121.2 t=−5.94.
- Strategy convention (entry→next print): Mon-entry +41.1 t=+3.10 (raw p=1.98e-3, Bonf5 adj
  9.9e-3 PASS); Tue +33.8 t=+2.46 (p=0.0140→0.0698 FAIL); Wed-entry −46.5 t=−3.08
  (p=2.08e-3→adj 0.0104: PASS familywise α=5%, marginal fail vs per-test α=0.01);
  Thu-entry −116.3 t=−5.72 (p=1.33e-8→6.6e-8 PASS); Fri-entry +94.4 t=+4.53 (p=6.4e-6→3.2e-5 PASS).
- 2008-2026 (n=4701): Mon +27.1 t=+1.65 (adj 0.494 FAIL); Tue +34.6 t=+1.91 (0.281 FAIL);
  Wed −49.4 t=−2.42 (p=0.0159→adj 0.0796 FAIL); Thu −118.8 t=−4.06 (5.35e-5→2.7e-4 PASS);
  Fri +98.5 t=+3.41 (6.8e-4→3.4e-3 PASS).
**Verdict:** Does Fri/Mon/Thu still pass? 1998+: YES all three (Mon only as the Fri-harvested
print; an explicit Mon entry passes adj p=0.0099). 2008+: only Thu and Fri pass Bonferroni;
Mon and Wed fail. The sleeve's three legs: Thu/Fri rock-solid; **Wed leg is the fragile one**
(adj p 0.0104 in 98+, 0.0796 in 08+) — but leg-LOO drop-Wed SR 2.18 vs 2.19 (08+) shows the
sleeve barely depends on it (verified). The map is exactly the Bonferroni-passing set at 98+
plus the borderline Wed; Tue (ns) correctly excluded. Selection risk real but well-behaved.

## 3. Regime stability — 5y subperiods and yearly
Sleeve SR by 5y block (net, vt-scaled, 1998+ rebuild):
- C5ng: 98-02 1.70 | 03-07 1.60 | 08-12 2.65 | 13-17 1.68 | 18-22 1.53 | 23-26 1.43.
- C5ngsum: 98-02 1.80 | 03-07 1.95 | 08-12 1.67 | 13-17 1.96 | 18-22 2.05 | 23-26 3.36.
**No negative 5y block.** Raw leg signs by block (bp/d): Thu short-leg negative in all 6 blocks
(−67.9/−155.9/−174.5/−68.1/−151.9/−66.2); Wed negative in all 6; Fri positive in all 6
(+100.8/+72.4/+99.4/+106.7/+113.1/+65.4); Mon entry flips negative only in 23-26 (−16.9) — and
the sleeve has no Mon leg. Summer Thu t=−9.31 (n=4465).
Yearly: C5ng_trunc 0/19 neg (min +6.27%), C5ngsum_trunc 0/19 (min +5.7%), E1 C5ng 0/29
(min +1.73%), E1 C5ngsum 1/29 (**2000 −1.79%** — correctly disclosed in E1 FINDINGS).
"0 negative years" claims VERIFIED exactly as stated per file/window.

## 4. Calendar-scramble (circular price shift, 50 draws, seed 20260901)
Prices rolled by random offsets 200..n−200 on the FIXED calendar, sleeve rebuilt end-to-end
(filter, T+1, costs, vt), eval 1998+:
- C5ng: real SR 1.63 vs scrambled mean −0.150, sd 0.200, p95 0.18, max 0.24 → real is ~8.9 sd
  above scrambled mean; p = (0+1)/51 = **0.0196** (= minimum achievable with 50 draws).
- C5ngsum: real 2.08 vs mean −0.160, sd 0.212, max 0.22 → ~10.6 sd; p = **0.0196**.
Consistent with agents' weekday-map scrambles (200x, p=0.0000 / 0.015). The effect is not an
artifact of calendar alignment. (Note: harness `scramble_pval()` return-permutation test is
DEGENERATE — permuting returns preserves mean/std so SR is unchanged; confirmed in
B2_highfreq/gates.py; agents disclosed and used position/map scrambles instead. HARNESS BUG,
worked around correctly.)

## 5. Summer window selection — all 12 rolling 7-month windows (SR 98+ / SR 08+ / negy / worst%)
Jan-start 0.96/1.09/4/−11.8; Feb 1.32/1.55/2/−8.8; Mar 1.74/1.87/1/−7.1; **Apr (Apr–Oct)
2.08/2.19/1/−1.8 — CHOSEN, rank 1/12 on both windows**; May 1.91/1.97/1/−0.8; Jun
1.68/1.62/0/+1.2; Jul 1.21/1.06/2/−2.2; Aug 1.08/1.00/2/−3.4; Sep 1.00/0.93/5/−8.1; Oct
1.02/0.98/4/−5.1; Nov 0.91/0.96/4/−8.1; Dec 0.98/1.07/4/−7.6.
9/12 windows pass SR≥1 on 98+ (8/12 on 08+); median window SR 1.15. Apr–Oct IS the max of 12
(a post-hoc pick — agents disclosed this) but it sits on a smooth warm-month hill (Mar/May
starts 1.74/1.91), not an isolated spike; max-of-12 selection cannot explain away t≈11.2
(SR 2.08 × √29; naive p≈6e-29, ×12 ≈ 1e-27). Note Jun-start window has 0 neg years — the
"0 negative years" property is partly window luck; honest E1 file reports 1/29.

## 6. Economic sense / EIA report timing
Structure the sleeve actually harvests (1998+ raw, entry→next print):
- Fri LONG earns the **Monday print** (+100.4bp/d, t=5.82) — the weekend premium. Fri-entry pnl
  by month: positive every month except Jan (−120) and Feb (+46); strongest Oct +179 / Nov +232.
- Thu SHORT earns the **Friday print** (−121.2bp/d, t=−5.94): Friday daytime weakness. Present
  in EVERY month except Jan (+193); strongest Oct −319 / Nov −354.
- Wed SHORT earns the **Thursday print** (−47.1bp/d, t=−3.22): −48.1bp/d Apr-Oct (t=−3.6) vs
  −45.7bp/d Nov-Mar (t=−1.5) — essentially identical in and out of the storage-report season.
**Assessment:** the weekday structure is real and broad, but the meta's "midweek pre-EIA-report
hedging + injection-season" narrative is only partially supported: the Thu-print effect is NOT
report-season specific, and the largest Friday weakness occurs Oct/Nov, outside Apr–Oct's core.
The Apr–Oct filter's real function is cutting winter tails (winter-only SR 0.66, MDD −40% per
C5 FINDINGS, consistent with my leg table). Narrative mismatch — honesty FLAG, not a bug.
**Lookahead via print timing: none found in code.** All decisions are at close t using info ≤ t;
pnl = next print. A Wed-close short holds through the Thu 10:30 ET report (pre-report
positioning — realizable, not lookahead); the Thu-close short is entered AFTER the report.
**UNVERIFIED:** the exact time-of-day stamp of the FRED daily spot (close vs intraday
assessment) cannot be verified from disk; if the day-t print were assessed after close t, the
1-print pnl chain would inherit that convention symmetrically (T+1 design still trades at most
once daily at the close). EIA release-calendar facts (weekly Thu 10:30 ET) are external and not
in the repo — UNVERIFIED, but the audit conclusion does not depend on them.
Execution realism: spot prints; metas disclose basis risk via HH futures/UNG — correct caveat.
2020 balloon behavior: calm filter demonstrably skipped the 2020-09-04 −25.4% print (sleeve pnl
−0.02% that day); worst balloon-week sleeve days −4.72% (09-18) and −3.07% (09-23, against a
+15.5% price day). E1 C5ngsum full-sample MDD −13.1% troughs 1999-04-28 (not a 2020 artifact).

## 7. Champion integration (does the champion lean on the weekday sleeve?)
- Committed GOAL100_CHAMPION (V1, uses truncated C5 files) and GOAL100_CHAMPION20Y_V2 (uses E1
  files) both regenerate byte-identical via their committed builders (`champion_build.py
  --verify`, `champion20y_build.py --verify`: max dev ≈1e-16). My reimplementation of
  champion20y construct() reproduces the json bal exactly: SR 6.17, ann 65.1%, MDD −7.2%,
  OOS17+ 71.5%.
- Leave-both-ng-out on 20Y_V2 BAL (exact construct): SR 6.17→6.01, ann 65.1→64.5%, MDD
  −7.2→−7.9%, OOS 71.5→72.4%. Contribution +0.16 SR / +0.6pp ann / −0.7pp MDD — **modest;
  champion does not depend on the weekday engine.**
- Committed V4 BAL CSV independently reproduces json claims from the CSV itself: ann 70.1,
  SR 6.25, MDD −6.4, 0/19 neg, worst +8.6%, OOS17+ 75.4%. C5ng+C5ngsum = 2/20 slots; the two
  sleeves are siblings (corr 0.567 on 2008+) — a de-facto 2-slot family (10% of pool), disclosed
  only implicitly (each gate documented separately). Minor FLAG.
- **V4 reproducibility gap:** no committed builder script for V4/20Y_V3/V4 (V4 pool exists only
  in GOAL100_CHAMPION_V4.json). Reconstructing V4 BAL from the json pool + champion_build
  functions + COORD sleeves (brwt5/brwt7/brwt10_2000/MHX_multihorizon_xgb) matches the committed
  CSV with corr 0.99998 and IDENTICAL SR 6.25, max|daily diff| = 3.0e-3 confined to 20 days,
  2026-08-03..2026-08-28 (later-vintage sleeve tails: brwt5/7 end 2026-08-10, MHX 2026-08-12,
  C5 sleeves 2026-08-24, champion 2026-08-28). Impact trivial for V4 stats, but the EXACT V4
  builder is not reproducible from committed artifacts as-is. FLAG (process).
- Champion `vt()` uses shift(1) sigma; champion CSV last-days weight renormalization (sleeves
  ended 08-24 vs champion 08-28) is handled with s=0 → clean, no lookahead.

## 8. Cost robustness (my rebuild, no vt, 1998+): SR at 0 / 6 / 12.5 / 25 bps per side
C5ng: 1.73 / 1.57 / 1.39 / 1.04. C5ngsum: 2.24 / 2.07 / 1.88 / 1.52. Survives 4x costs.

## Verdict
The natgas weekday family SURVIVES the adversarial audit: exact replication from raw data
(max dev 1e-16), no lookahead in the signal/T+1/cost/VT chain, no negative 5y block, calendar
scramble p at the 50-draw floor 0.0196 with real SR ~9-11 sd above the scramble distribution,
2 of 3 legs robust to Bonferroni(5) in both windows, cost-robust to 25bps. Residual risks
(all quantified, none fatal): (a) Wed leg fails Bonferroni on 2008+ (leg-LOO impact −0.01 SR);
(b) Apr–Oct is the max of 12 post-hoc windows (disclosed; selection bias immaterial vs t≈11);
(c) EIA-report narrative only partially supported by season splits of raw effects;
(d) gates.vol_target same-bar sigma quirk (≤±0.05 SR, campaign-wide);
(e) sibling-slot double counting in V4 pool; (f) V4 builder script not committed, 20-day
3e-3 tail mismatch. Claims in metas/FINDINGS match my numbers everywhere they overlap;
no inflated claim found in the weekday family.

AUDIT3 DONE

Operator instruction requires the final line to be exactly "AUDIT DONE" (charter's "AUDIT3 DONE" satisfied on the line above).
AUDIT DONE
