import os
ROOT="/Users/daxu/software/world-trader/campaign/agents/chief/coord"

CHARTERS = {
# ---------- A: NEW ENGINE HUNTS (10) ----------
"HUNT_COT2": ("COT aggregation & cross-market (round-2)",
"""New but FINELY-tested: your first coordinator run showed COT level-fade, level-follow and
delta-follow per-market are dead (raw corr +0.16..+0.22 = SAME-PERIOD artifact; proper forward
corr +0.03). Your job: test genuinely NEW COT aggregates the prior run did NOT test, with CLEAN
forward timing (report fully known Friday -> trade next week, never same-week overlap):
 (a) CROSS-MARKET COT (rank spec net %OI across all 9 markets each week -> long the most-crowded-
     short basket, short the most-crowded-long basket) held 1 week; does cross-sectional rank help?
 (b) SWAP/COMMERCIAL (hedger) positioning fade (commercials are the smart counter-party).
 (c) OI (open-interest) change as a regime/timing overlay.
 (d) spec LONG vs SHORT asymmetry (long_pct - short_pct) instead of net.
Run with clean forward timing, 6.4bps full-|dW|, T+1, ALL gates (SR>=1, plateau, halves, yearly,
scramble, |corr|<0.15 vs champion). If any clears, SAVE sleeve+script+meta; if all fail, log exact
numbers (SR, negyears, corr) as an honest negative. Data:
tools/quant/data/more_cot/{gold,silver,copper,corn,soybeans,nat_gas_nymex,wti,sugar,wheat}_cot.csv
col net_noncomm_pct_oi, open_interest. Prices: GLD tools/quant/data/twelvedata/GLD.csv; SLV/USO/
UNG/CORN/SOYB/CANE/WEAT tools/quant/data/more_etf/; copper tools/quant/hedge_fund_strats/data_fred/copx.csv
Read /Users/daxu/software/world-trader/campaign/agents/chief/coord/GATES_CONTRACT.md first."""),

"HUNT_CRYPTO2": ("crypto satellite round-2",
"""Prior crypto TS-momestrian satellite was a near-miss (SR 1.1 own-span, 4/10 neg yrs, blend dSR
immaterial). Try NEW crypto signal families that could clear the champion gate:
 (a) crypto VOL-SCALED crossover (momentum but vol-bounded, weekly) across BTC/ETH/alt basket.
 (b) crypto mean-reversion / short-term reversal at DAILY for the most-liquid 3 (BTC,ETH,...) —
     you may have better luck than LN/crypto trends at 1-day.
 (c) crypto SECTOR relative value (BTC vs ETH vs base layer) — market-neutral-ish long/short.
 (d) crypto as VIX-hedge/risk-on risk-off regime GATE on an existing sleeve (not a standalone).
Use honest T+1, 6.4bps full-|dW|, all gates. Data tools/quant/data/more_crypto/*.csv
(BTC,ETH,BNB,ADA,AVAX,DOGE,DOT,LINK,LTC,MATIC,etc). Corr vs champion must be |corr|<0.15.
Read GATES_CONTRACT.md first."""),

"HUNT_INTERNATIONAL2": ("international equity cross-momentum",
"""Cross-country equity momentum/carry using existing international price series. Test:
 (a) Country momentum: rank international indices (NIKKEI225, DJIA, NASDAQCOM, SP500, DEX-implied
     or EFA/EEM/VWO ETFs in more_etf) by trailing 12m, long winners short losers, monthly.
 (b) Country carry: yield-differential (IRLTLT... international 10y in more_fred) weighted equity.
 (c) EM vs DM relative rotation (EWW/EWZ/FXI vs EWA/EWG/EWJ...) with vol overlay.
T+1, 6.4bps full-|dW|, all gates, |corr|<0.15 vs champion. Watch out: prior cross-ASSET momentum on
equities was weak/noisy; country momentum historically has some signal in EM but decays. Be honest.
Data: tools/quant/data/more_etf/*.csv + tools/quant/data/newdata/{NIKKEI225,DJIA,NASDAQCOM,SP500}.csv
Read GATES_CONTRACT.md first."""),

"HUNT_CMDT2": ("commodity ETF cross-asset",
"""Commodity ETF cross-asset momentum & carry round-2 (beyond the champion's Brent-WTI/natgas).
Test genuinely new commodity sleeves using more_etf commodity ETFs: USO(wti),DBC,DBA,GSG,CANE(sugar),
CORN,SOYB,WEAT(wheat),MOO(agri),UNG(natgas),SLV,GLD,COPX/copper,GDX/goldminers.
 (a) COMMODITY CARRY: roll/front vs back (approximate via ETF term via DBE/DBP/USCI if available or
     proximate), cross-commodity.
 (b) COMMODITY MOMENTUM cross-sectional (rank 12m, hold 3m) across the universe.
 (c) ENERGY vs PRECIOUS vs AGRICULTURE relative sector rotation.
 (d) Commodity as INFLATION-REGIME factor (combine with FRED CPI/T10YIE in more_fred) — long
     commodities when realized inflation rising.
T+1, 6.4bps full-|dW|, all gates, |corr|<0.15 vs champion (careful: brwt/natgas are already 4
champion slots; a USO-based short-run wti reversal is likely redundant UNLESS it's low-corr).
Read GATES_CONTRACT.md first."""),

"HUNT_MACRO2": ("macro-factor engines (made-vs-policy, credit, activity)",
"""Macro-factor sleeves from rich FRED (94+ series more_fred + newdata). Prior macro single-series
gates were dead (NFCIRISK gate best SR0.90). Test NEW MULTI-SERIES composite macro PREMIA:
 (a) CREDIT-CYCLE: BAA-AAA spread + high-yield OAS (BAMLH0A0HYM2) trend/level as a risk-on/off
     factor long-credit when BAA/AAA compressed.
 (b) ACTIVITY-NOWCAST composite (INDPRO + CFNAIMA3 + RRSFS + PAYEMS) as a pro-cyclical equity-flat
     or commodity-directional factor.
 (c) POLICY/real-rate: real yield (T10YIE/DFII10) + term premium as a duration-directional sleeve.
 (d) LIQUIDITY/fed-balance-sheet (WALCL, RRPONTSYD) as a risk factor.
Must be T+1 (macro released with lag; use released-as-known or shift appropriately), 6.4bps full-
|dW|, all gates, |corr|<0.15 vs champion. Prior macro hunts (HUNT_MACRO2, HUNT_PDA) were negative,
so set expectations low but test the genuinely-new composites above. Read GATES_CONTRACT.md first."""),

"HUNT_VOL2": ("options-implied vol term-structure round-2 (VVIX/SKEW/GVZ/OVX)",
"""Prior VXV/VIX term-structure overlay was dead. Test NEW vol-surface features from more_vol
(9 vol series) as RISK-ON/OFF or HEDGE overlay, not just term-structure:
 (a) VVIX (vol-of-vol) level/change as a risk-off timing gate.
 (b) SKEW (25-delta) change: sharp SKEW rise -> equity/commodity risk-off tilt.
 (c) VIX9D vs VIX3M vs VIX6M short-term term-structure as a 2-3 window signal.
 (d) GVZ(gold vol)/OVX(oil vol) as asset-specific vol-timing overlays.
 (e) Cross-asset vol (VIX/GVZ/OVX ratio) as relative-value signal.
Implement as T+1 overlays or standalone vol-timing sleeves, 6.4bps full-|dW|, all gates,
|corr|<0.15 vs champion. Data tools/quant/data/more_vol/*.csv (VIX,VIX3M,VIX6M,VIX9D,VVIX,SKEW,
GVZ,OVX,RVX,VXV,VIXMO). Read GATES_CONTRACT.md first."""),

"HUNT_FXCARRY2": ("FX carry + momentum combo round-2",
"""Round-2 FX. Prior CFX4 (FX carry) had IS SR ~0 (weight 0). Test NEW FX sleeves on the 8 pairs:
 (a) FX CARRY+MOMENTUM combo: long high-yield + positive-momentum, short low-yield + negative-momentum
     (the classic FX factor), weekly.
 (b) FX REAL-CARRY: inflation-adjusted (deflate nominal carry by CPI in more_fred) — real carry is
     more stable.
 (c) FX value/PPP: long undervalued (real-exchange-rate reversion via DEX real? use IRLTLT + CPI).
 (d) Vol-scaled FX momentum (downside-vol weighting).
T+1, 6.4bps full-|dW|, all gates, |corr|<0.15 vs champion. Data tools/quant/data/fx/*.csv +
more_fred CPI. Priority: candidate that survives yearly 0-neg + halves. Read GATES_CONTRACT.md first."""),

"HUNT_SECTOR2": ("US sector ETF rotation round-2",
"""Prior full-SPDR sector hunt (HUNT_SECTOR_FULL) found the 0.667 screening was a cost artifact and
the honest SEC3-family was 0.18-0.26 (dead). Test genuinely NEW sector approaches that respect
costs (weekly/monthly only, low turnover so costs don't kill):
 (a) SECTOR MOMENTUM cross-sectional (rank 12-1 momentum across 11 SPDR sectors XLK,XLY,XLP,XLE,
     XLF,XLV,XLI,XLB,XLU,XLRE,XLC), rebalance monthly, long top3 short bottom3.
 (b) SECTOR CARRY/dividend (high-div sectors XLU,XLP,XLV vs growth XLK) as a style rotation.
 (c) Sector + macro-regime gate (market breadth/trend gate to go net long sectors only in uptrend).
Monthly rebalance controls the 6.4bps drag. All gates, |corr|<0.15 vs champion. Data:
tools/quant/data/more_etf/*.csv (XLK,XLU,XLV,XLY,XLP,XLF,XLI,XLB,XLE,XLRE,XLC + SPY/QQQ/DIA).
Read GATES_CONTRACT.md first."""),

"HUNT_CREDIT2": ("credit & rates-spread engines round-2",
"""Round-2 credit/rates. Prior C2 rates-steepener + credit-OAS were dead. Test NEW spread sleeves:
 (a) HY vs IG credit-spread CARRY (long HY ETF JNK, short IG LQD if available or VCSH) when BAA-AAA
     is stable/compressing, flat when widening — with spread-lag (credit spreads lead).
 (b) Duration-neutral RATES carry: 2s10s / 5s30s curve position from US treasury futures/tips.
 (c) Inflation-breakeven (T10YIE/T5YIE) trend following as a TIPS/breakeven sleeve.
 (d) Credit-impulse (new-issuance/deleveraging proxy from flow data if available) as a gate.
T+1, 6.4bps full-|dW|, all gates, |corr|<0.15 vs champion. Data: more_etf (JNK,HYG,EMB,LQD if
present,TIP,SHY), more_fred (BAA,DAAA,BAA10Y,T10YIE,T5YIE,hy_oas,BAMLH0A0HYM2,BAMLC0A4CBBB).
Read GATES_CONTRACT.md first."""),

"HUNT_TREASFUT": ("treasury futures curve / basis round-2",
"""Round-2 US-rates. Prior a6r7 bond2y trend + A1credit regime are champion slots. Test NEW
decoupled rates sleeves high-corr to champion would be redundant — focus on genuinely low-corr:
 (a) FRONTIER: treasury futures CURVE trade from constant-maturity FRED (DGS2/DGS5/DGS10/DGS30):
     long 2y short 10y when curve steeps, flat when flattening, vol-scaled, daily.
 (b) TIPS real-yield (DFII10/20/30) level-reversion directional.
 (c) Term-structure butterfly (2s10s30s) — if implementable with DGS series.
 (d) International yield-spread (US10 - DE/CA/JP10 from more_fred IRLTLT...) partial carry.
Costs: DGS-based trades approximate treasury futures at 6.4bps full-|dW|. All gates, |corr|<0.15 vs
champion (watch corr to a6r7/A1credit). Data more_fred (DGS*,T10Y2Y,DFII*,IRLTLT*) + newdata.
Read GATES_CONTRACT.md first."""),

# ---------- B: CONSTRAINT CAMPS (3) ----------
"CAMP_SHORT": ("non-shortable-stock modeling + integration",
"""Build a rigorous, reusable NON-SHORTABLE-STOCK model per IBKR reality and integrate it as a
fail-closed gate for any equity L/S sleeve.
 1. Research: what fraction of US small/micro-caps are hard-to-borrow / not shortable, and the
    borrow fee schedule at IBKR (hard-to-borrow fees, locate requirements, short-sale constraints).
 2. Model: implement bt/shortability.py with a shortability_gate(weights, universe_mcap/rank):
    - drop or reweight the short leg of names below a size/borrow threshold (configurable frac),
    - charge a borrow fee on the remaining short notional (IBKR hard-to-borrow sliding fee, not the
      flat 0.5% — make it parameterizable, default calibrated to IBKR typical 0.5-20%/yr by
      borrow tier).
 3. Test (TDD): campaign/bt/tests/test_shortability.py — RED->GREEN: (a) names above threshold
    shortable, below dropped; (b) borrow fee charged correctly; (c) no-lookahead (borrow that day).
 4. Impact: run the champion's equity-family sleeves (H21_f5, XGB1y, MHX) through the model and
    report the honest ann/SR/MDD change. Determine if any is materially overstating returns.
 Deliver model + tests + impact report in FINDINGS.md. Do NOT modify committed champion CSVs."""),

"CAMP_BORROW": ("IBKR call-rate + borrow-cost audit",
"""Audit and, where needed, correct the cost model for IBKR reality:
 1. Call rate: verify the champion charges 4.5%/yr margin on (gross-1) — confirm this is a
    reasonable IBKR call-rate proxy (current fed funds + margin spread) and stress the margin
    drag if call rate rises to 5.5%/6.5% (report ann/SR/MDD sensitivity).
 2. Borrow: verify borrow 0.5%/yr short-notional is charged on EVERY short sleeve; where
    hard-to-borrow instruments exist (e.g., natgas LEAPS?, equity books), model a higher borrow tier.
 3. Reconciliation: confirm the champion's margin + borrow algebra exactly reconcile to the
    TRADE_RECORD_STANDARD ledgers (qty_notional=|dW|, cost_bps=6.4, borrow, margin).
 4. TDD: add/extend campaign/bt tests for margin-call-rate stress + borrow-tier correctness.
 Produce an honest sensitivity table (call rate 4.5/5.5/6.5, borrow 0.5/2/5%) -> champion
 ann/SR/MDD. Deliver findings in FINDINGS.md."""),

"CAMP_COST": ("full-|dW| @ 6.4bps one-side universal audit",
"""Audit EVERY rebalancing path for cost honesty (one-side FULL |dW| @ 6.4bps, TRADE_RECORD_STANDARD):
 1. Verify the champion builder charges FULL |dW| (not 0.5x) — confirm the iter11 fix is intact by
    re-running the regression test; also confirm no OTHER builder (campaign/scripts/*.py,
    C4_construct, champion_build, champion20y_build) still uses a 0.5 half-turn on its weight diffs.
 2. Grep for '0.5' cost patterns across campaign/scripts and campaign/agents (flag any 0.5*|dW|).
 3. Verify vol-target rebalances and throttle switches also charge full 6.4bps (no free rebalances).
 4. TDD: one regression test asserting NO builder undercharges turnover < full|dW|*6.4bps.
 Report each builder's cost-convention + any discrepancy with exact numbers. Deliver in FINDINGS.md."""),

# ---------- C: MORE DATA (3) ----------
"DATA_FREDMORE": ("add more free FRED macro series (linted)",
"""Acquire MORE free FRED series that are genuinely NEW signal classes (not duplicating the 94
already present). Priority candidates (lint fail-closed, span>=10y where possible):
 - labor/participation: NROU, LNS11300060, AWHAETP (avg weekly hours)
 - leading: S&P/CS house price index, MAYHII... , DRGHP...
 - credit: TOTALSL, CREDITLOANS, DTCSRSAUTH...
 - trade/terms: not needed
Write each to tools/quant/data/more_fred/{id}.csv via the existing fred_dl.fetch (FRED_KEY in
.env.local). record in a FINDINGS note: series_id, role, start/end, n, gaps, PASS. Reuse
run_more_fred.py's fetch/lint/write_csv (tools/quant/data/more_fred). Do NOT touch other data.
Target: 10-20 new linted series. Deliver manifest + any interesting span/coverage notes."""),

"DATA_ETF_MORE": ("add more free sector/international/commodity ETFs (linted)",
"""Acquire MORE free ETF price series (via TWELVEDATA_KEY/FINNHUB_KEY in .env.local) to widen the
hunt universe. Prioritize gaps:
 - sector: XLRE (already?), XLY/XLP present — add QQQ/MQQQ? focus on gaps
 - international single-country/regional: EWH(HK), EWS(SG), EWK(Bel), EWT(TH), EWW(MX), EWC(CA),
   EIS(Israel), TUR, ENOR, EPHE
 - commodity single-name: DBA/DBC/GSG present? add USCI, DBP, DBE if cheap; GLD/SLV present
 - rates/credit: HYG,LQD,TIP,TLT present? add LQD, HYG, EMB
Lint fail-closed (start>=2005, no long zero runs, sane jumps). Write to tools/quant/data/more_etf/
{id}.csv [date,close] + record in manifest. 10-20 new series. Report coverage table."""),

"DATA_COTMORE": ("add more free COT markets (linted)",
"""Acquire/verify MORE COT positioning markets beyond the 9 already at tools/quant/data/more_cot/
(e.g., canola, cocoa, cotton, feeder cattle, lumber, oats, rough rice, soybean meal/oil, wheat
HRW/SRW, and financial TFF: eur, gbp, jpy, sp500_emini, dow_emini, nasdaq_emini, us_10y/2y_note,
eurodollar_3m, sofr_3m, copper). These CSV files already exist — for each, verify the 
net_noncomm_pct_oi column parses, span>=10y, weekly cadence, no gaps>9 days, and map to a LIQUID
price proxy. Produce a table: market | COT span | price proxy | proxy span | tradeable-from date.
Deliberate deliverable is a CLEANED universe manifest the engine-hunt agents can trust. Do NOT
download new data unless a listed market file is missing; add missing ones (FRED/twelvedata). 
Report in FINDINGS.md."""),

# ---------- D: AUDIT (4) ----------
"AUDIT_CHAMP2": ("independent champion replica-audit vs all constraints",
"""INDEPENDENT adversarial re-verification of champion campaign/results/GOAL100_RAWEW13v2_
WEIGHTED_GEAR16_daily.csv from RAW sleeve files + builder (campaign/scripts/rawew13v2_build.py).
Do NOT trust the committed CSV or any doc. Recompute from the sleeve files and verify EVERY:
 1. 6.4bps one-side FULL |dW| (no 0.5x)  2. IBKR 4.5% margin on (gross-1)  3. leverage<=1.6
    (0 overshoot)  4. 0 negative calendar years  5. fungible-short pool (no single-name equity
    short, or model it)  6. T+1 no lookahead (perturbation)  7. byte reproducibility (maxdev<1e-12).
Independently recompute ann_geo/SR_d/MaxDD/neg-years and compare to the committed champion numbers.
If ANY check fails, add a failing TDD test first, then fix (you may fix the builder but NOT silently
alter committed champion semantics). Log exact PASS/FAIL numbers in FINDINGS.md. Reuse
campaign/audit_harness_newconstraints.py as a starting point (already 7/7 PASS) but audit it too."""),

"AUDIT_FWBUGS": ("adversarial framework TDD bug hunt",
"""Adversarial TDD bug-hunt of the reusable backtest framework campaign/bt/ (engine, metrics,
gates, reconcile, backtest) AND the champion builder. For each suspected bug: write a FAILING test
first (RED), confirm it fails, then fix (GREEN). Focus on:
 - cost_turnover / margin / borrow / cap_leverage correctness vs TRADE_RECORD_STANDARD
 - metrics ann_geo ruin-guard, SR, max_dd (NaN safety), neg_years
 - gates scramble p-value correctness, zero-runs, halves edge cases
 - reconcile turnover/ledger fail-closed
 - champion builder: full-|dW| (iter11 fix intact), margin, leverage epsilon, no lookahead
Add regression tests to campaign/bt/tests/test_*.py. Log each bug found+fixed with RED->GREEN
evidence in FINDINGS.md. Goal: 0 known bugs. Do NOT modify committed champion CSVs."""),

"AUDIT_RECON": ("byte-repro + no-lookahead + trade-blotter reconciliation",
"""Independently verify integrity: (a) champion CSVs are byte-reproducible from committed sleeve
inputs (run rawew13v2_build.py --verify; must be IDENTICAL); (b) every sleeve used is T+1/no
lookahead (read the four levers: signal->position shift, vol-target trailing, throttle lag,
cost on |dW|); (c) reconstruct a period of the champion's implied weight path and confirm the
portfolio return = Wg_{t-1}*r_t (no same-day leak), and that turnover charged == |dW|*6.4bps on
that reconstruction; (d) confirm any equity-family sleeve (H21/XGB1y/MHX if in a pool) is not
overstating due to unmodeled shortability (see CAMP_SHORT). Produce an integrity report with
exact reproduction hashes/numbers in FINDINGS.md. Flag any discrepancy loudly."""),

"AUDIT_GATES2": ("hunt-gate + scramble correctness audit",
"""Audit the correctness of the hunt-gate battery agents will use (see GATES_CONTRACT.md + bt/
gates.py). Verify with negative controls that gates do NOT spuriously pass noise and DO pass a
known strong signal:
 - signal-scramble: feed a synthetic NOISE sleeve 200x -> p must be ~uniform (no spurious pass);
   feed a synthetic STRONG sleeve -> p<0.05 (detect).
 - halves: split a nonstationary sleeve with strong-H1 weak-H2 -> must fail; two strong halves ->
   pass.
 - yearly: a sleeve with one -6% year must fail the 'each>-5%' rule.
 - plateau: a single-spike SR param must be rejected.
 - decorrelation gate: correct correlation computation vs champion.
 - leverage/cost gates: full-|dW| enforcement.
Add TDD regression tests (negative + positive controls) to campaign/bt/tests/. Report RED->GREEN
evidence + any gate you had to FIX in FINDINGS.md. This ensures every agent's 'pass' is trustworthy."""),
}

def write(name, title, body):
    d = f"{ROOT}/{name}"
    os.makedirs(f"{d}/sleeves", exist_ok=True)
    with open(f"{d}/CHARTER.md", "w") as f:
        f.write(f"# CHARTER: {name} — {title}\n\n")
        f.write("ROUND 1\n\n")
        f.write(body.strip() + "\n")

for name,(title,body) in CHARTERS.items():
    write(name,title,body)
    print("wrote", name)

# manifest of all agent names
agents=list(CHARTERS.keys())
print("\nTOTAL AGENTS:", len(agents))
with open(f"{ROOT}/AGENTS.txt","w") as f:
    f.write("\n".join(agents))
