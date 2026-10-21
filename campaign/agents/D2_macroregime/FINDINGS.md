# D2_macroregime — ROUND 1 FINDINGS (agent log)

Mandate: weekly/monthly labor & macro regime books (claims, payroll, net liquidity, CFNAI, M2).
Method: shared lib `d2lib.py` — honest publication lags (ICSA +5d, WALCL/WRESBAL +5d, PAYEMS +8d,
M2SL +28d, CFNAI +24d, TGA n/a), signal-to-position T+1 (position.shift(1)), 6bps/side on
|Δposition|, vol-target 10% trailing expanding min-60d clip 3.0, assets: synth 2y TR from DGS2
(carry + 1.9y duration), FF Mkt-RF+RF as SPX (1926+), xau spot (2007+), synth IG corp TR from
BAMLC0A0CM.
HARNESS FIX (for all agents): `B2_highfreq/gates.scramble_pval` permutes the RETURN series →
permutation-invariant degenerate p (C2 also noted). D2 uses **position-permutation scramble**:
permute executed-position series vs fixed asset returns, recompute net (incl. costs) + same
vol-target, p = frac{SR_scrambled >= SR_real}, 200 draws, seed 7. This is the honest
"does the signal time the asset?" test. Numbers below use it (plus gates.py p shown as scramble_p).

## KEY STRUCTURAL RESULT (explains everything below)
Always-long synth-2y TR 1976-2026: ann 13.7%, SR **2.08**, mdd -19.2%, 6 neg yrs (worst 2022 -11.6%),
corr_blend 0.169. Against that baseline, ANY on/off gate evaluated as a standalone long/flat book
inherits ~half the asset's SR at best, and a RANDOM on/off gate of the same asset scores
sig-scramble SR ≈ 1.0-1.3 at 50% exposure-adjusted vol. So a claims/payroll-level gated bond book
can only pass if the gate times the asset — none do (every gate: sig_p ≈ 0.0-0.09, i.e. scrambles
tie or beat the real gate).

## Idea 1 — Claims-momentum regime → 2y book — **FAIL**
ICSA 4w-avg YoY (lag 5d), 1976-06→2026-08. Long-only 2y when claims yoy>0: SR **1.34**, ann 7.1%,
H1 1.75/H2 0.75, negy **11**, sig_p **0.000**, scramble_p 0.92, corr_blend 0.081. yoy>5%: SR 1.13
(H2 0.46), negy 8. 13w-chg>0: SR 1.52, negy 13, sig_p 0.000. L/S version: SR -0.10 (shorting 2y in
 disinflationary expansions = catastrophic, 32 neg yrs). Short-side claim is the killer: falling
claims yoy usually = mid-expansion, and 2y still returns carry. Verdict: gate carries NO timing
information vs always-long 2y (sig_p=0); fails d, e decisively.
Claims→SPX rotation (2y when yoy>0 else SPX): SR 0.65, negy 19 (1929-1974 events), sig_p 0.0.
Sahm-rule-style recession gate rotation: SR 0.67, negy 20.

## Idea 2 — Net liquidity (WALCL/WRESBAL/BOGMBASE) → SPX — **FAIL** (confirms COORD kill)
WRESBAL 13w-z long/short SPX (lag 5d): SR 0.21, worst 2008 -82% (gate was IN during crash),
sig_p 0.000. Long/flat same: SR 0.21. BOGMBASE 3m-chg (lag 30d) long/flat: SR 0.46, negy 13,
sig_p 0.000, corr 0.172. WALCL 52w-chg: SR 0.14, sig_p 0.000. TGA.csv on disk is a corrupted HTML
page (FRED fetch fail, like RRP) — net-liquidity = WALCL-TGA not constructible. The famous regime
trade is dead here too.

## Idea 3 — CFNAI 3m-avg → credit-on gate — **FAIL (data-blocked)**
BAMLC0A0CM starts 2023-08 on disk → only 3y overlap; always-long synth corp SR 1.12 (3y, bull
window, not a test). CFNAI>0 gated corp: SR 0.02, sig_p 0.000. No long sample = idea untestable
honestly; logged, not saved.

## Idea 4 — M2 growth regime → gold — **FAIL**
M2 yoy minus trailing 5y-median (lag 28d) long gold: SR **0.28**, H1 -0.06, sig_p 0.000, corr 0.165.
M2 yoy>5% abs: SR 0.12, sig_p 0.09. Always-long gold baseline itself is only SR 0.56 (6 neg yrs).
Gold's 2007-26 run was NOT a mechanical M2 phenomenon at monthly granularity. CFNAI<0→gold side
note: SR 0.73, 0 neg yrs, sig_p 0.005 (the ONLY genuinely-timing signal found) but SR < 1.0 and
H1 = 0.00 (nothing before 2013) → fails a/c/halves; flagged for round 2 refinement.

## Idea 5 — Composite of best two — **FAIL** (prerequisite not met: no solo book passed even
SR>=0.8 with clean halves) EW(claims-gated-2y, CFNAI-gated-gold): SR 1.22, mdd -11.3%, negy **11**,
worst -5.9%, sig-family p 0.28, corr 0.196. Fails d, e, f.

## Bonus event studies (logged, NOT saved)
Claims-spike shock (4w-avg yoy jump >5%/10%) hold-15d event books: short SPX SR **-0.30/-0.26**
(claims spikes mid-expansion are bullish-resolution events; shorting them bleeds), long 2y SR 1.26
(negy 5, sig_p 0.000 = just bond carry), long gold SR 0.57 (sig_p 0.98). Post-claims-peak rollover
long-SPX h65: sig_p 0.015 (real timing!) but SR 0.06 — fires early (1990/2001/2020 losses -17/-17/-54%).
Claims-shock→gold has the only sub-0.05 sig_p in the family (p=0.005, 12 events incl. 2008/2011/
2016/2019/2020/2023/2024) — weakest-link is SR 0.73 and zero pre-2013 activity.

## SAVED SLEEVES: **NONE** (0/5 ideas pass ALL gates; contract: do not save failures).
Best-fail numbers for coordinator: claims-gated 2y (SR 1.34, negy 11, sig_p 0.000 — gate is
noise vs carry); always-long 2y carry engine (SR 2.08, corr_blend 0.169) fails negy/worst gates
(2022 -11.6%) exactly like C2's steepener-carry finding — the D1/D2 rate-carry family needs a
year-2022 solution (e.g. long-frontier: 2y carry floored by bill/carry spread) before it is usable.

## Reuse notes
- d2lib.py: load_new/load_fr/to_daily(lag)/synth_tr/backtest/gates_full + position-scramble API.
- Publication lags used: weekly +5d, PAYEMS +8d, M2 +28d, CFNAI +24d.
- Assets: synth TRs (2y dur 1.9, IG-corp dur 8.0) are approximations; ETF-based dupes (SHY/LQD)
  would only add fee drag, same signals.

## ROUND 1 VERDICT
The weekly/monthly macro-regime domain (claims, payroll, income, M2, liquidity, CFNAI) contains
**no gate-passing sleeve** on free data at 6bps with honest lags. Macro level-gates do not time
rate/equity/gold carry. The one live thread for ROUND 2: claims-stress→gold event timing
(sig_p 0.005) — needs a pre-2013 activation mechanism or different sizing to clear SR 1.0.

ROUND 1 DONE
