# CHAMP_DATA_FRESH — round-1 audit (2026-09-14, as-of 2026-09-12)

Scope: the 12 champion sleeves in `rawew13v2_build.py` POOL+NEW (brwt10/7/5, C5ng, C5ngsum,
A5r2, a6r7, QAxasts, carryv2, dualmom, diescrack, CFX4). Repro: `campaign/agents/CHAMP_DATA_FRESH/audit_freshness.py`.
No network was used (env proxy-flaky, per charter) — everything below is measured on disk.

## 1. REGRESSION (charter item 4)

- `python3 campaign/scripts/rawew13v2_build.py --verify`:
  `n_committed=4806 n_built=4806 inner=4806 max|new-old|=9.996e-17 IDENTICAL`;
  `weights max|committed-built|=6.939e-17 IDENTICAL`; `gross mean 1.600000 max 1.600000 days>1.6 0`;
  `turnover 4.7660 bp/yr; margin 2.70%/yr`. The on-disk pipeline is DETERMINISTIC and SELF-CONSISTENT.
- Byte-stability vs git HEAD (68fb355, 2026-09-13): **7 tracked files are MODIFIED and uncommitted** —
  the 4 refreshed sleeves (brwt10 3983±, brwt7 2802±, brwt5 2853±, diescrack 727± changed lines),
  the champion CSV (4806/4806), the weights CSV (11/12) and the builder (200/18). Explanation (verified
  from `git diff`): HEAD still holds the **ITER15 13-sleeve book** (weights file at HEAD contains
  `brwt15,0.09665` and 13 rows); DISK holds the **ITER19 12-sleeve champion** (brwt15 pruned, weights
  refit, `brwt10/7/5__costfix` + `diescrack` re-emitted 2026-09-09 19:08). Example drift: champion
  2026-08-27 ret HEAD −2.1614894e-4 vs disk −2.3325806e-4. Verdict: no corruption — disk is the newer,
  self-consistent champion of record; **coordinator should commit the current disk state**.

## 2. FRESHNESS / COVERAGE TABLE (as-of 2026-09-12; last completed trading day Fri 2026-09-11)

| sleeve    | rows | start      | last_row   | last_nonzero | tail_0rows | gap_cal (last_row) | rows<2017 | NaN |
|-----------|------|------------|------------|--------------|-----------:|-------------------:|----------:|----:|
| brwt10    | 6626 | 2000-01-05 | 2026-08-28 | 2026-08-27   | 1          | 15                 | 4246      | 59  |
| brwt7     | 4639 | 2008-01-03 | 2026-08-28 | 2026-08-21   | 5          | 15                 | 2259      | 59  |
| brwt5     | 4639 | 2008-01-03 | 2026-08-28 | 2026-08-24   | 4          | 15                 | 2259      | 59  |
| C5ng      | 7381 | 1997-04-02 | 2026-08-24 | 2026-08-24   | 0          | 19                 | 4963      | 0   |
| C5ngsum   | 7381 | 1997-04-02 | 2026-08-24 | 2026-08-24   | 0          | 19                 | 4963      | 0   |
| A5r2      | 4249 | 2009-09-18 | 2026-08-11 | 2026-07-01   | 28         | 32                 | 1835      | 0   |
| a6r7      | 9168 | 1990-01-04 | 2026-08-27 | 2026-08-27   | 0          | 16                 | 6754      | 0   |
| QAxasts   | 4947 | 2006-12-13 | 2026-08-12 | 2026-08-12   | 0          | 31                 | 2531      | 0   |
| carryv2   | 5179 | 2006-09-27 | 2026-08-03 | 2026-08-03   | 0          | 40                 | 2678      | 0   |
| dualmom   | 4743 | 2007-10-08 | 2026-08-12 | 2026-08-12   | 0          | 31                 | 2327      | 0   |
| diescrack | 4615 | 2008-03-28 | 2026-08-24 | 2026-07-15   | 28         | 19                 | 2209      | 0   |
| CFX4      | 1799 | 2019-09-10 | 2026-08-05 | 2026-08-05   | 0          | 38                 | 0         | 0   |

Notes: `tail_0rows` are BY-DESIGN gate-off zeros (diescrack meta: "gate-off rows exactly 0.0";
A5r2 flat-exposure days), not missing rows — that is why gap is quoted on last_row. brwt NaN=59 are
pre-2000 splice holes (brwt10 only). Coverage: every sleeve except CFX4 has ≥1,835 rows <2017 —
ample for the IS weight fit. CFX4 rows<2017 = 0 → gets relw 0 by the coverage rule (by design).

## 3. PROVENANCE + REFRESHABILITY (on-disk sources only)

| sleeve (relw)        | underlying source                                    | source tail on disk           | refresh possible |
|----------------------|------------------------------------------------------|-------------------------------|------------------|
| brwt10/7/5 (51.04%)  | FRED wti/brent spliced w/ EIA spot daily (R3-proven, CAMP_COST/work_r6/refresh_sleeves.py) | eia_weekly/wti,brent_spot_daily → 2026-09-01 | +2 td (08-28→09-01) |
| C5ng, C5ngsum (20.76%) | DHHNGSP Henry Hub spot weekday prem                 | eia_weekly/natgas_HH_spot_daily → 2026-09-01 | +6 td (08-24→09-01) |
| diescrack (9.26%)    | newdata/DJFUELUSGULF vs wti_full log-spread z-rev    | DJFUELUSGULF → 2026-08-25 (wti_full 08-11; EIA ulsd_gulf 09-01 = alt source) | +1 td (or +6 with EIA-source swap, needs validation) |
| a6r7 (5.06%)         | FRED DGS2 synthetic 2y TR                            | data_fred/DGS2.csv → 2026-08-27 | **at bound** |
| A5r2 (3.46%)         | SPY + VIX/VIX3M + us10y rate-shock gate              | spx 08-11, vix 08-10, VIX3M 09-09, DGS10 08-27 | bound 08-11 (no newer SPX/VIX on disk) |
| QAxasts (4.65%)      | twelve_big 5-leg TSMOM MA189                         | twelve_big 294/298 files → 2026-08-12 | **at bound** |
| dualmom (3.34%)      | twelve_big xs tercile + FF-MKT 200d MA gate          | twelve_big 08-12; ff_factors daily stale 2026-06-30 | at bound (panel); FF gate file itself stale |
| carryv2 (2.43%)      | GLD/xau seasonal-carry + brent floor                 | xau 08-13; twelve_big has no GLD.csv; data_fred/brent 08-03 | +7 td (08-03→~08-12) |
| CFX4 (0.00%)         | twelvedata FX GBPNZD/AUDGBP/AUDEUR/EURNZD            | **books ABSENT from disk** (fx, more_fx, fx_hist, twelvedata all checked) | unrefreshable |
| champion blend       | 12 sleeves                                           | last row 2026-08-28           | on-disk max common tail = 2026-09-01 |

Weight accounting: 81.06% of relw (brwt 51.04 + C5ng 10.87 + C5ngsum 9.89 + diescrack 9.26) is
extendable on-disk; 16.51% (a6r7/A5r2/QAxasts/dualmom/carryv2) is at/near its on-disk bound; 0% CFX4.
Even fully refreshed without network, the blend tail reaches only 2026-09-01 — still 8 td short of
2026-09-11. Closing the last gap requires network fetches (twelvedata equity panel, FRED DGS2/DGS10/
SPX/VIX, EIA) — documented, NOT attempted per charter.

## 4. VERDICT — does any visibly-stale sleeve threaten the champion's tail?

NO CORRUPTION THREAT. All 12 sleeves simply STOP (08-03…08-28); none carries wrong values into the
champion (`--verify` IDENTICAL at 9.996e-17 proves the committed NAV is exactly what the disk sleeves
produce). The exposure is a COVERAGE gap: the champion of record is blind for the last 15 calendar
days (08-28→09-12) and carries a stale 08-12-08-11 tail on 12.9% of relw (QAxasts+dualmom+A5r2) and
08-03 on carryv2 (2.4%). Because the stale tail is dominated by the 51% brwt block whose EIA sources
already run to 09-01, the cheap fix is mechanical: re-run `CAMP_COST/work_r7/rawew15_refresh_candidate.py`
against the 09-01 EIA files + extend C5ng/diescrack the same way, then re-fit/re-verify; CFX4 stays
zero-weight (unrefreshable AND vendor-artifact-discredited — data absence independently confirms the
decision). Priority for coordinator: (a) commit the uncommitted ITER19 disk state (regression risk if
lost), (b) on-disk refresh to 09-01, (c) network refresh to 09-11 when the env allows, then re-emit
the champion and re-run --verify.

## 5. NUMBERED SUMMARY (idea, numbers, verdict)

1. **Freshness audit of the 12 champion sleeves** — last trading rows 2026-08-03 (carryv2) … 2026-08-28
   (brwt10/7/5); gaps to 2026-09-12: 15–40 cal days (blend tail 15d); tail zeros are by-design gate-off
   (diescrack 28, A5r2 28 rows). ALL 12 FLAGGED stale vs 2026-09-12. Verdict: coverage gap, not corruption;
   refresh machinery already exists on disk (CAMP_COST/work_r6/work_r7).
2. **Coverage audit (IS window <2017)** — rows<2017: a6r7 6,754 / C5ng 4,963 / brwt10 4,246 / carryv2 2,678 /
   brwt7=brwt5 2,259 / diescrack 2,209 / QAxasts 2,531 / dualmom 2,327 / C5ngsum 4,963 / A5r2 1,835 — all
   sufficient; CFX4 0 (no IS coverage → relw 0 by rule, by design). Verdict: no coverage threat to the weight fit.
3. **Data provenance / refreshability** — 81.06% of relw extendable from on-disk sources (EIA wti/brent/HH
   → 09-01; DJFUEL 08-25; xau 08-13); a6r7/QAxasts/dualmom/A5r2 at on-disk bounds (08-11…08-27); ff_factors
   daily itself stale (2026-06-30); CFX4's 4 FX books ABSENT from disk → unrefreshable, zero-weight justified.
   Verdict: on-disk refresh lifts blend tail 08-28→09-01 only; 09-11 needs network (documented, not fetched).
4. **Regression / byte-stability** — `--verify` IDENTICAL (champion max|new-old|=9.996e-17; weights 6.939e-17;
   gross exactly 1.6, 0 days>1.6; turnover 4.766 bp/yr, margin 2.70%/yr). BUT 7 files uncommitted vs HEAD
   68fb355: HEAD = 13-sleeve ITER15 book (brwt15 0.0967 in weights), disk = 12-sleeve ITER19 champion
   (brwt15 pruned; e.g. 08-27 ret −2.1614894e-4 → −2.3325806e-4). Verdict: disk state is the true,
   self-consistent champion of record — MUST BE COMMITTED; champion not currently reproducible from git alone.

CHAMP_DATA_FRESH DONE
ROUND 1 DONE
