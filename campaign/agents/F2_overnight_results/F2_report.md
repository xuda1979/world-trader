# F2_overnight — INTRADAY DECOMPOSITION (open/close vs overnight)

## VERDICT: REJECT — no sleeve passes gates (SR>=1.5 AND corr<0.5 to champion)
Best honest candidate post-cost: **SR 0.731** (M7 overnight-drift-gated long SPY, 5d hold, ann 10.0%, MaxDD -26.8%) — less than half the SR>=1.5 gate. Corr gate passes everywhere (0.09–0.23) but SR gate fails on **every** variant. No F2_sleeve.csv emitted (no gate pass). Structural cause: any overnight-capture sleeve needs 2 one-side turns/night = 12bps/day ≈ **30.2%/yr cost floor** at 6bps/one-side; SPY overnight drift is only **6.27%/yr gross** (t=2.37). The overnight anomaly cannot clear this cost model at daily frequency.

## DATA (offline, all local)
- Brief specified `more_etf/SPY.csv` — **does not exist** (more_etf has no SPY; QQQ there is close-only). SUBSTITUTION (logged): `tools/quant/data/twelvedata/SPY.csv` (date,open,high,low,close,vol), 2006-09-26..2026-08-12, n=5000. QC: 0 dups, 0 NaN, 0 weekend rows, 0 zero prices; gap profile = normal weekends/holidays. Dropped final partial session 2026-08-12 (vol 807k vs ~40M typical).
- `tools/quant/data/polygon_intraday/`: **17 names** (brief said 18 — discrepancy logged), 5-min close snapshots 04:00–20:00 ET, only **68 sessions 2024-12-02..2025-03-12** per name (n=26–101 usable per name). Used as qualitative cross-check only (too short for a gated backtest).
- Champion recomputed from `campaign/results/GOAL100_CHAMPION_daily.csv` col ret, n=4696 (2008-09-01..2026-08-28): ann **61.67%**, SR **5.182**, vol 9.36%, MaxDD **-7.31%** — matches brief (SR~5.18, ann~61%). ✓

## (a) DECOMPOSITION (SPY, n=4998, 2006-09-27..2026-08-11)
| component | mean/yr | t-stat | ann vol | var share of daily |
|---|---|---|---|---|
| overnight O_t/C_{t-1}-1 | **+6.27%** | 2.37 | 11.79% | 36.4% |
| intraday C_t/O_t-1 | +4.39% | 1.30 | 15.02% | 59.2% |
corr(on,id)=**0.045**. Halves: 2006-16 on=3.1%/yr id=3.8%; 2016-26 on=9.4%/yr id=4.9% — overnight premium concentrated post-2016. Finding replicates the known anomaly (directionally confirmed cross-sectionally: 17-name mean on=+5.9%/yr vs id=-10.3%/yr, but only 8/17 names individually on>id — small-n noise, no tradable cross-section there).

## (b) T+1 ON/ID L/S MOMENTUM SLEEVES (net of full cost stack) — ALL REJECT
Signals use only info ≤ close t (rolling means shift(1)), position earns day t+1. Cost: 6bps·|dW| (+2×6bps for overnight entries+exits, 4.5%/yr margin on gross>1, 0.5%/yr borrow on shorts).
| sleeve | ann | SR | MaxDD |
|---|---|---|---|
| M1 sign(mean(on-id),K=5/10/21/63), full day | -1.1/-3.6/-0.4/-0.2% | 0.04/-0.09/0.08/0.09 | -59..-74% |
| M2 same signal, overnight-only (12bps/nt) | -25.9..-27.9% | -2.47..-2.72 | -99%+ |
| M3 always-LONG overnight (anomaly harvest) | **-21.87%** (gross +6.27% vs 30.2%/yr cost) | -2.03 | -99.3% |
| M4 diag: sign(on_t)×id_t at open (continuation) | -24.91% | -1.83 | -99.7% |
| M4b diag: reversal | -28.52% | -2.16 | -99.9% |
| M6a/b conditional ON (drift>0 × vol regime) | -9.9%/-6.3% | -2.58/-1.03 | -73..-88% |
| M6c vol-targeted ON-only (w≤1) | -19.56% | -2.54 | -98.7% |

## (c) VOL SLEEVE (exposure ∝ 1/realized vol) — REJECT
| sleeve | ann | SR | MaxDD |
|---|---|---|---|
| M5a long SPY T+1 baseline | +9.23% | 0.550 | -56.5% |
| M5b vol-target 8%/10%, cap1.5 (21d realized, shift(1)) | +4.99%/+5.92% | **0.585/0.573** | -22.2%/-27.1% |
| M7 ON-drift gate (21d mean>0), 5d hold — best overall | +10.01% | **0.731** | -26.8% (9.4 turns/yr) |
| M7b/c/d ID-gate / ON+ID-gate variants | +3.3..+6.6% | 0.30..0.54 | -35..-53% |
M7 subperiod stability: SR 0.359 (07-12) / 0.581 (13-18) / 1.277 (19-26) — regime-dependent (2019+ only), never ≥1.5 over any full-period test. Vol targeting lifts SR 0.55→0.585 only; underlying gross SR ~0.55 bounds the family.

## CORR TO CHAMPION (n=4513 common dates) — gate corr<0.5 PASSES
M5a long SPY 0.226 · M1_K63 0.094 · M3 longON 0.119. Gate was never the binding constraint; SR≥1.5 fails with margin ≥0.77 SR everywhere.

## FAIL-CLOSED LOG
- REJECT M1–M4 (ON/ID momentum L/S): best SR 0.088 < 1.5 (deficit 1.412), ann ≤ -0.19% net.
- REJECT M3/M6 (overnight harvest family): cost floor 12bps/night = 30.2%/yr vs gross ON drift 6.27%/yr (t=2.37) — impossible by construction under mandated costs.
- REJECT M5/M7 (vol/gated full-day): best SR 0.731 < 1.5 (deficit 0.769); unstable by third (max third SR 1.277).
- Data deviations logged: SPY source substitution (twelvedata); 17 not 18 polygon names; polygon window only 68 sessions.
- All stats: ann=(1+r).prod()**(252/n)-1; SR=mean/std·√252; MaxDD negative from (1+r).cumprod(). No check was uncomputable; nothing masked.

## CONCLUSION
Decomposition is economically real (overnight carries the premium; corr(on,id)≈0.05) but **not monetizable at 6bps full-turnover costs with daily-bar instruments**: the entire sleeve family caps at SR 0.73 vs gate 1.5, and champion (SR 5.18) remains untouched. Recommend no adoption; F2_sleeve.csv intentionally not written (gate FAIL).

DONE F2_overnight
