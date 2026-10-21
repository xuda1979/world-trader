# CFX4 DATA-CORRUPTION VERDICT (chief independent verification, 2026-09-09 ~11:4x CST)

KILLS the c4fa930 supplement's "CFX4 is the Sharpe lever" proposal AND the 11:09 in-flight
rebuild (CFX4_long1999_dtf2163_net.csv + cfx4_long_rebuild.py). Do NOT adopt either.

## What was verified
1. Blend arithmetic (supplement proposal 2) REPRODUCED independently: champ+CFX4-carry constant
   mix 2019-09-10..2026-08-05, w=0.5 -> SR 3.266 (claimed 3.08; mine slightly better), MDD
   improves -5.33%->-3.15%, 0 neg yrs, corr(champ,CFX4)=0.052. The MATH is honest.
2. But the SLEEVE is not tradeable. Same construction (c11_deliver.py spec, faithful: dual-tf
   z(21,63), T+1, 6bps/side, 0.5%/yr borrow), same 2019+ window:
   - committed CFX4 built from tools/quant/data/fx/ (twelvedata): SR +1.91
   - rebuilt on tools/quant/data/fx_hist/ (ECB-corroborated): SR -0.76 (all 4 books negative
     individually: -0.45/-0.72/-0.58/-0.61)
   The "edge" inverts with the data source -> it is a property of the vendor feed, not the market.

## Evidence the fx/ (twelvedata) feed is corrupt
- Daily returns of the SAME pair from fx/ vs fx_hist/ correlate only 0.52-0.56 (should be >0.99).
- 31.6% of overlapping days (2338/7408 across GBP/NZD/AUD/EUR_USD) move in OPPOSITE directions.
- fx_hist vs official ECB reference rates (tools/quant/data/ecb_fx, 1999+): return corr 0.9999.
  fx/ vs ECB: ~0.52. Two official sources agree; twelvedata is the outlier.
- Long rebuild on the corrupt-free source: full SR -0.84 (26/28 negative years), IS<2017 SR -0.82
  -> would earn ZERO solver weight anyway. Proposal 1 (pre-2019 extension) is dead with it.

## Champion impact: ZERO
RAWEW13v2_IS_SR_weights.csv -> CFX4 relw = 0.0. The corrupt feed touches nothing live.
Champion of record stands: ann 37.20%, SR 3.181, MDD -6.69%, 0/19 neg yrs (verified 07:18,
bytes unchanged since Sep 7 11:24).

## Standing instruction to all research agents
tools/quant/data/fx/ (twelvedata) is QUARANTINED for any new sleeve construction or blend
argument. Use tools/quant/data/fx_hist/ (554 pairs, 1999+, ECB-verified) as the FX source of
record. Any historical claim that depends on fx/ data must be re-derived before it is trusted.
