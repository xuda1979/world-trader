# AUDIT5_data — data-layer integrity audit (read-only)

Champion sleeves rest on: twelve_big/twelvedata panel (285-440 names 2006+), FRED series,
Ken French portfolios, DHHNGSP. Audit the DATA LAYER:
1. SURVIVORSHIP: twelve_big/twelvedata — are these currently-listed names? (they are:
   static panel assembled in 2026). Quantify the bias: SPX equal-weight total return of
   the panel vs SPX index 2006-2026. Report the annual gap. Which sleeves depend on the
   panel (H21, XGB1y, MHX, QAxasts, dualmom, A1inf, carryv2)?
2. FRED series: check for silent revisions/rebases: DGS2 (1976+), DHHNGSP (1997+),
   DCOILBRENTEU, wti_full — any level discontinuities >20% day-over-day that aren't real
   market moves? (e.g., unit changes). Report outliers and their dates.
3. Ken French: portfolio returns are SAME-DAY close-to-close with formation at prior June —
   the sleeves using KF data (B3momhml) — is formation date handled PIT?
4. FRED daily spot prints (DHHNGSP): when is the daily print actually stamped? Could a
   'Wednesday close' print contain Thursday information? Check FRED documentation notes
   and any known timestamp conventions; report what you find (or that it's unverifiable).
5. twelve panel OHLCV sanity: cross-check 10 random names' close series against any other
   source on disk (twelve_extend, twelve_liq) — % mismatch.
Write campaign/agents/AUDIT5_data/FINDINGS.md with all findings. Last line: AUDIT5 DONE
