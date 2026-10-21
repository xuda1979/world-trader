# RESEARCH AGENDA & SWEEP — 2026-09-17 (multi-agent research directions)

Based on the champion audit (AUDIT_DAX_2026-09-17) and a repo-state sweep. Companion to the two
reports: `CHAMPION_REPORT_INTERNAL_2026-09-17.md` (full replication) and
`CHAMPION_INVESTOR_SUMMARY_2026-09-17.md` (redacted).

Companion documents for replication & investor communication are committed alongside this memo.

---

## 1. Framing fact — where the edge (and the risk) lives
Measured from the canonical builder:
- **brwt triad (brwt5/7/10) = 76.1% of gross**, each 0.89–0.93 correlated to the champion;
  the natural-gas family (C5ng/C5ngsum) adds ~15% -> **~91% of the book is the energy complex
  (oil-spread + nat-gas), expressed as one family with a few correlated bets**.
- Champion per-gross net return = **21.2%/yr**; energy block IR 2.8–3.0 vs every decorrelated
  family at IR ~0.8–1.9. This gap is why a low-IR decorrelated sleeve cannot clear the
  capital-real dAnn>0 bar.
- This is BOTH the strength (why it earns 39.5%) and the single structural risk (a regime break
  in oil-spread behaviour hits the whole book at once).

## 2. Tier 1 findings (executed this sweep)
### 2a. De-concentration of the brwt block — NO free lunch, but a legit alternative
Capping the brwt block at 33% of gross (re-diversifying into the 6 decorrelated sleeves, fixed
1.6x, full costs + margin):
| variant | ann | SR | MaxDD | brwt share |
|---|---|---|---|---|
| BASE champion | 39.50% | 3.218 | -6.52% | 76% |
| brwt cap ~50% | ~39.4% | ~3.23 | ~-6.5% | ~75% (fit is already there) |
| brwt cap ~33% | 36.92% | **3.419** | **-5.50%** | 61% |

The max-Sharpe fit is already near-optimal for this pool; forcing diversification beyond it
trades ~2.6pp/yr ann for a materially better SR (+0.20) and MaxDD (+1.0pp). **A legitimate
risk-reduced deployment variant for conservative capital**, not a free edge. No decorrelated
sleeve currently on disk can be added to raise ann without the energy concentration.

### 2b. Fresh-data engines through the capital-real dAnn>0 gate INDIVIDUALLY (post-brwt15)
Re-tested the strongest ITER13/14/16 rejections one-by-one with a correct capital-real re-fit
(not a blend-masked overlay):
- **A5_r7_credit_composite** (real FRED credit): dAnn **-1.72pp** -> REJECT.
- **PIT_quality_daily**: dAnn **-1.60pp** -> REJECT.
- **G1_intraday** (natgas-gap, new 2026-09-16): showed +0.32pp BUT this is a **reweight
  artifact**: its corr to the champion is **0.95** (it trades the same book), its own report
  declares the edge t=0.09 (statistically zero) and **NO-GO for integration** (champ lift +0.03
  SR). NOT adoptable.
Conclusion: **ITER16's hard frontier stands even after the brwt15 prune.** The decorrelation+
  per-gross hurdle is structural; only a genuinely new, decorrelated, high-per-gross daily
  engine moves it.

## 3. Tier 1 remaining / open (recommended next)
3. **HTS-style hunt-prompt family generation** — the one avenue with the most headroom to find a
   NEW decorrelated daily engine (not re-derive from existing book). Generate a disciplined,
   pre-gated hunt family (ac1<0.5, uniqR>=0.08, scramble/block baked in) across genuinely-new
   data surfaces:
   - cross-market basis / seasonal / weekend structures beyond oil & gas (e.g. refined products
     vs crude, metals basis, freight);
   - intraday/overnight decompositions of UNDERLYING instruments we already trade (not a 17-file
     polygon gap-screen);
   - COT/CFTC open-interest regimes combined with the energy spread (needs more than the crude
     configs already rejected);
   - credit-risk premia levered to real (non-paper) HYG/LQD with an honest sr-like hurdle, since
     the current credit composite underfills per-gross.

## 4. Tier 2 (methodological closure — cheap, do next)
4. **OOS-decay monitor as a GATE**: per-sleeve rolling 2-year SR monitor with a pre-committed
   prune-if threshold (ITER19 showed pruning works; make it continuous, e.g. prune a sleeve if
   its trailing-2y SR < ~0.8x its full-sample and it's >10% of gross — pre-committed, not
   event-driven).
5. **Cost/financing stress for live deployment**: champion margin uses 4.5%/yr (pre-hike). Re-run
   `net_t = +... - max(gears-1,0)*RATE/252` for RATE=5.5/6.0/7.0% and confirm the dAnn and SR
   margins are acceptable and the 0-neg-year property holds. Cheap; directly de-risks live.
6. **CGOYS y-scramble in block-P**: settle the stranded-asset provenance question once; low
   effort, removes a lingering data-integrity unknown.

## 5. Tier 3 (skip — already at/behind frontier per ITER14/16/17)
Walk-forward refits (gain attributed to discredited CFX4), turnover micro-optimization (already
4.77bp/yr), weight-method scans (SR^0.55/correlation-aware already chosen).

## 6. Suggested prioritized "agent" rundown (if spawning parallel workers)
1. [DONE here] Concentrate / dAnn>0 / de-concentration probes (2a, 2b above).
2. HTS hunt-family generator across new surfaces (Tier 1 #3) — highest value, requires new data.
3. Financing-stress + OOS-monitor harness (Tier 2 #4/#5) — cheap, mechanical.
4. CGOYS y-scramble (Tier 2 #6) — cheap, closes provenance.
