# HUNT_MACRO2 — NEW macro block (WALCL/RRP/SOFR/T10Y3M/TED/NFCI-credit-risk/STLFSI4/JOLTS/
# debt-GDP/mortgage/OECD-CPI/global-LT-yields) as regime gates & satellites, iter8

Premise tests (all through campaign/bt, full honesty, gates + scramble):
1. Fed net-liquidity (WALCL - TGA? TGA absent -> WALCL & RRPONTSYD separately) momentum/gate on QQQ.
2. T10Y3M (recession covariate) level/z + slope-change gate on equity.
3. NFCI-risk/credit, STLFSI4 stress gates (risk-off => longflat).
4. JOLTS openings-quits spread (labor cooling) gate.
5. Global LT-yield momentum cross-country: AU/CA/CH/DE/GB/JP/US — trade QQQ/EW-intl (EFA).
6. OECD CPI surprise = CPI momentum z as inflation-regime gate.
Data: tools/quant/data/more_fred/*.csv (NEW), bis_eer for currency mom (dead already — skip).
Note dead-ledger: WALCL>median SPY gate DEAD (SR 0.22) — do NOT re-run plain WALCL median gate;
test NEW forms (RRP level-gate, net-liq momentum, multi-series combos) only.
Last line: HUNT_MACRO2 DONE
