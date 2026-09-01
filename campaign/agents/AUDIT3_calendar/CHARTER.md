# AUDIT3_calendar — adversarial audit of natgas weekday sleeves (read-only)

The natgas weekday family (C5ng, C5ngsum, E1 variants) survived and is in the champion.
Try to BREAK it:
1. Rebuild from raw DHHNGSP (tools/quant/data/newdata/DHHNGSP.csv) with YOUR OWN code:
   weekday position map [Mon +, Wed -, Thu -, Fri +] (check the metas for exact map),
   calm filter, T+1, 6bps, expanding vt. Compare to committed sleeves (corr, diff).
2. The weekday map was chosen from data — MULTIPLE TESTING risk. Quantify: t-stats of all
   5 weekday means 1998-2026; Bonferroni for 5 tests; does Fri/Mon/Thu still pass?
3. REGIME split: compute SR by 5-year subperiods (1998-02, 03-07, 08-12, 13-17, 18-22, 23-26).
   Any 5y block negative? The sleeve claims 0 negative years — verify.
4. Calendar-scramble: circular-shift the price series by random offsets (50x), rebuild,
   p-value of real SR vs scrambled.
5. SUMMER-only window (C5ngsum): is Apr-Oct chosen post-hoc? Test all 12 rolling 7-month
   windows; report how many pass; is Apr-Oct an outlier pick or one of several?
6. ECONOMIC sense: EIA storage report Thursday 10:30 ET — is Wed/Thu short actually
   front-running? The print timing (FRED daily spot) vs report release — any lookahead
   possible in the mapping of prints to days?
Write campaign/agents/AUDIT3_calendar/FINDINGS.md with all numbers. Last line: AUDIT3 DONE
