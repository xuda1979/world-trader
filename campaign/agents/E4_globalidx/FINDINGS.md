# E4_globalidx FINDINGS — ROUND 1 (2026-09-01)

## DATA / FRED FETCH RESULTS (documented per charter)
FRED fredgraph.csv full-history fetches (saved to tools/quant/data/newdata/):
- **NIKKEI225.csv: 1949-05-16 → 2026-08-31, 19,190 obs — FULL history ✓**
- **NASDAQCOM.csv: 1971-02-05 → 2026-08-28, 14,009 obs — FULL history ✓**
- DJIA.csv, SP500.csv, DJCA.csv: **2016-09-01 only (FRED 10-year limit) — NOT full history** (charter hope "DJIA likely full-history" is wrong; the /graph/fredgraph.csv endpoint returns 10y for DJIA/SP500/DJCA, but full range for NIKKEI225 and NASDAQCOM)
- DEXJPUS.csv (JPY) already on disk 1971+. DXY (dxy.csv) 2006+ already on disk.
Loaders: `E4_lib.py`; scan repro: `scan_round1.py`. NO sleeves saved this round — everything below failed gates.

## IDEA 1 — Nikkei TSMOM (21/63/126/252d, weekly decisions, T+1, 6bps/side) — FAIL
Full history 1949+ (gross index → ETF proxy). Net results (full window):
- w=21: SR 0.36, ann 7.1%, MDD -72.9%, negy 29, H2 SR 0.05, scramble_p 1.000
- w=63: SR 0.39, ann 7.7%, MDD -71.4%, negy 32, scr_p 0.050 (marginal), corr 0.041
- w=126: SR 0.26, ann 5.2%, MDD -89.0%, negy 38
- w=252: SR 0.41, ann 8.0%, MDD -66.6%, negy 36
Sub-period autopsy: pre-1990 SR 0.61–0.80, **post-1990 SR 0.02–0.15, 2007+ SR -0.11…+0.14**.
The edge is entirely pre-1990 (pre-derivatives era); post-1990 Nikkei trend is dead.
Long/flat (clip≥0) better but still far below gates: w=63 LF SR 0.66 (ann 8.8%, MDD -36.6%, negy 29, scr_p 0.39); w=252 LF SR 0.67 (H2 0.35). Daily variants same story (w=63 daily SR 0.38).
NKY-USD TSMOM (unhedged, +DEXJPUS): SR 0.23–0.30. NKY 252×21 double-confirm: SR 0.12. NKY-NDQ rel-12m LS: SR 0.25. NKY turn-of-month: SR 0.16. EWMA cross 8/32, 5/20, 13/52: SR 0.29–0.41, H2 ≈ 0.00–0.12. **All fail full_sr≥1.0, halves, negy, scramble.**

## IDEA 2 — Nikkei→SPX overnight/lead-lag — FAIL (and the naive version is lookahead)
- Naive same-day-close version (Nikkei t close → SPX t close): lag0 SR 1.05, lag+1 SR 4.32 — **LOOKAHEAD ARTIFACT**: Nikkei day-t close is 1:00 JST t+1, i.e. ~16:00 UTC t — inside/after the US session; IC 0.43 is the same-day global-beta overlap, not tradable. NOT saved, flagged so nobody "discovers" it.
- Honest implementable version: signal = Japan session t return (known 06:00 UTC), trade SPY t OPEN→CLOSE (12bps round trip), 2006-09→2026-08, n=4697:
  **IC = -0.0387 (sign flipped vs naive!), LS day-session SR -2.07, ann -31.0%**; threshold variants th=0.5/1/1.5% all SR -1.5…-0.8. Nikkei day-session return mildly ANTI-predicts the US day session. Gate verdict: hard fail every gate.

## IDEA 3 — NASDAQCOM vs DJIA relative momentum 63d — FAIL (data-limited)
DJIA from FRED only 2016+ ⇒ full-history version uses index-proxy returns from 2016 (n=2511): w=21 SR -0.13, w=63 SR 0.02, w=126 SR -0.10, w=252 SR 0.26. All fail.
QQQ/SPY ETF version (2006+, real proxy): w=63 SR 0.18, w=126 SR 0.01, w=252 SR 0.38 (H1 0.15). All fail. Growth-vs-value relative momentum has no stable edge post-2006.

## IDEA 4 — Cross-index TSMOM basket EW vol-normalized weekly — FAIL
- NKY+NDQ (only 2 full-history indices), w=63: SR 0.49 ann 7.2% MDD -51.9% negy 17; w=126: SR 0.44; w=252: SR 0.54 ann 7.9% negy 14 H2 0.34 scr_p 0.90. Fails full_sr, negy, scramble, halves.
- 4-index basket from 2016 (adds DJIA/SPX): w=126 SR -0.24, w=252 SR 0.27, corr 0.23–0.26. Fails everything.
- 3-asset NKY-LF(252)+NDQ-LF(252)+DXY-LS(21), vt10: SR 0.51 ann 5.3% negy 5 corr 0.195; LS version SR 0.31. Fail.

## IDEA 5 — Nikkei level z-reversion — FAIL (both signs tested honestly)
z on log price, weekly, w∈{21,63,126,252}, full 1949+:
- fade (short rich): z21 SR **-0.59**, z63 -0.47, z126 -0.49, z252 -0.43 (all ~-100% MDD compounded) — fading Nikkei extremes is catastrophic; NO reversion edge.
- trend direction (same sign as momentum): SR 0.39–0.44 but MDD -75…-86%, negy 23–29, H2 SR ≤ 0.20, scr_p up to 0.99. **Nikkei level-z carries no tradable mean-reversion; chartered "check both signs" done — both fail.**

## EXTENSIONS (staying in global-idx domain)
- DXY dollar-index TSMOM (2006+, weekly, vt10): best w=21 SR 0.49 ann 4.8% MDD -18.9% negy 6 — but neighbors w=16 SR 0.19, w=26 SR 0.25, w=32 SR -0.05 ⇒ **param spike, NOT a plateau**; also full_sr ≪ 1.0 and scr_p 0.96. FAIL.
- NASDAQCOM long/flat TSMOM (full 1971+): w=252 SR 0.68 (ann 10.5%, MDD -41%, negy 15), w=126 SR 0.78 (MDD -56%, scr_p 1.0). Best-of-round but fails SR≥1.0/negy/worst-year (-25%) gates; 2007+ window SR 0.62–0.76, corr_blend 0.31–0.34 (would need corr_ok_secondary anyway).

## VERDICT
0 sleeves saved. Global index books (Nikkei, NASDAQ, DJIA, SPX, DXY) offer decorrelation (|corr| 0.01–0.34) but the SR ceiling is ~0.7 — no idea approaches the full-SR≥1.0 gate. Root causes: (1) Nikkei trend/reversion edges died after 1990; (2) index-level lead-lag at daily granularity is same-day beta overlap (lookahead trap) or mildly negative; (3) index relative-value (growth-vs-value) mean-reverts too fast to trend. Highest-value residual for future rounds: none of these paths; recommend coordinator NOT re-charter single-index TSMOM.

ROUND 1 DONE
