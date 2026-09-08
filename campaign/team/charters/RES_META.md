# RES_META — research: cross-asset / meta-alloc / macro-regime engines
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## FIRST STEP (item 2 — decorrelation-first filter)
Before any backtest, run `python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15`.
If |corr| to the champion >= 0.15, REJECT immediately and move on — don't burn
tool-calls on a candidate the blend-gate can't pass.

## Mission
Find >=1 NEW decorrelated DAILY engine from cross-asset / macro-regime / meta-alloc families
(distinct from basis and calendar). Champion matches RES_BASIS.

## Ideas (decorrelation target)
- Cross-asset momentum/spillover (FX<->rates<->equity<->commodity only where T+1 causal survives).
- Regime-gated sleeves (vol/trend-filtered) that add a different, low-corr return stream.
- Rate-curve / credit-spread term effects beyond a6r7/QAxasts (must beat |corr|<0.15 to blend).
- IMPORTANT: ML/optimized-meta routinely LOSES to EW OOS (C6 finding) — only pursue if a structural
  (non-optimized) mechanism backs it. T+1 shift is mandatory (the KF OP/INV same-day trap).

## Gates (identical battery — campaign/bt/)
SR>=1.0 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_META/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_META DONE
