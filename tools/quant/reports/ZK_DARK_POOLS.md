# Research: Cryptographic Execution via Zero-Knowledge Dark Pools

**Date:** 2026-08-16 (loop) | **Topic:** MEV-proof block execution for a latency-agnostic fund
**Status:** Steering / architecture scan - NOT a live-backtested edge. No capital allocated on this basis.

> NOTE: the quantum-intelligence retrieval service returned HTTP 503 (a 404 page from an
> unrelated host) on every call this firing. This report is written from stable public
> protocol knowledge rather than RAG-fetched SDK docs. Treat quantitative claims (TVL, fees)
> as order-of-magnitude; re-verify against live chain state before committing.

---

## 1. The problem this tooling solves

Public L1 mempools are fully transparent. A large pending order is visible before
confirmation, letting HFT / searcher bots:
- **front-run** (insert their own tx ahead of the fund),
- **sandwich** (buy ahead, sell after, capturing price impact).

For a fund with no speed advantage, exposing pre-trade intent in the mempool is the most
expensive leak: it converts a benign rebalance into a forced adverse-order-flow payment to
searchers (often several bps, and worse for large size where impact is quadratic).

## 2. The architectural solution: on-chain dark pools with MPC + ZKP

Renegade and Penumbra are pure on-chain dark pools that replace the central limit order
book with an **encrypted, distributed order book**:

- Order-book state lives **locally on each trader's side**, not on a central server. There
  is no public book to scrape.
- The fund submits a **cryptographic commitment** of its order (amount, token, side) to the
  protocol, not the plaintext.
- A decentralized network of **independent relayers** runs **Secure Multi-Party
  Computation (MPC)** to test matchability across encrypted orders WITHOUT ever decrypting
  the details in the clear. MPC is a cryptographic protocol that lets parties jointly
  compute a function (here: "do these two orders cross?") while each party learns only the
  output, never the other's private inputs.

### Settlement via zk-SNARK

Once matched (typically at the **oracle-derived mid-price**, eliminating the entire
bid-ask spread cost), settlement is verified on-chain via a **zk-SNARK** (Zero-Knowledge
Succinct Non-Interactive Argument of Knowledge). The proof demonstrates, without leaking
data:

- the wallet commitments are correct,
- the nullifiers prevent **double-spending** of the same value,
- the resulting state changes are valid.

The verifier on L1 learns ONLY "yes, this transition is valid" - NOT the fund's balances,
trade sizes, or directional intent. Wrapping ZKP generation inside the MPC algorithm gives
**end-to-end atomic privacy**: no party, relayer, sequencer, or chain sees the order in
plaintext, yet settlement is trustlessly verifiable.

## 3. Why this matters for THIS fund

- **Latency-agnostic**: the fund does not need to win latency races. It submits an
  encrypted intent and waits for anonymous MPC matching.
- **No bid-ask spread / no MEV tax**: crossing at oracle mid-price removes the spread;
  the ZKP+MPC stack removes front-running and sandwiching.
- **Fit to the desk's execution profile**: the system runs medium-frequency rebalances
  (momentum / pairs / CTA cross-asset). These are exactly the orders (too big for the AMM,
  too slow for the HFT war) that mempool transparency punishes most.

## 4. Reality check / limitations (steering, do not over-weight)

- **Liquidity depth is the binding constraint, not the cryptography.** MPC matching only
  helps if a counterparty with the opposite order exists on the same protocol. Current TVL
  and order flow in DeFi dark pools are a small fraction of CEX or top-tier AMM depth. For
  a fund needing institutions-scale fills, the optimal trade size here is far smaller than
  on a public AMM / RFQ venue.
- **Counterparty/order-flow risk**: anonymous MPC matching can expose the fund to
  adversarial or correlated flow; oracle mid-price settlement removes spread but not
  impact/market risk during the matching window.
- **Chain support is narrow**: Renegade (Ethereum / L2s, whitelisted counterparties via
  MPC attestation) and Penumbra (Cosmos-family, shielded-native) have specific, still-
  growing ecosystems. Cross-chain execution is immature.
- **Operational/compliance**: MPC relayer networks, ZK prover trust assumptions (trusted
  setup or updatable, prover honesty), and relayer centralization are real governance/
  failure-mode surfaces. KYC/whitelisting tension vs. the fund's own compliance needs.
- **Cost/latency of proving**: zk-SNARK generation and MPC rounds add latency vs. a plain
  swap - fine for rebalances, not for HFT.
- **Not yet a researched edge for the desk**: this report is an execution-mechanics scan,
  NOT a signal. No quant test was run; no capital should be sized on it yet.

## 5. Recommended posture

1. **Tier-0 watchlist**, not a live execution venue. Keep AMM/RFQ/CEX as execution venues;
   do not migrate rebalance flow into a dark pool until depth on the relevant pairs/sizes
   is measured.
2. **Feasibility probe (next step, if pursued)**: pick 2-3 pairs the desk actually trades,
   measure existing on-protocol depth + MPC settlement time, and compare all-in cost
   (spread + fees + impact) vs. current AMM routing. Only proceed if net saving >= ~5bps
   after all-in cost.
3. **Track, don't trade**: log MP-MEV exposure on current rebalances (how much adverse
   selection actually leaks today) so the replacement thesis is quantified, not assumed.

---

*Artifact ID: zk-dark-pools-2026-08-16. Companion tooling: none (architecture scan only).*


---

## 6. CONTINUATION (2026-08-16, 2nd firing): the broader MEV-mitigation toolkit

The MPC/ZKP dark-pool path is the most "pure" privacy solution but also the least liquid
today. A latency-agnostic startup fund should compare it against the wider, more
production-mature set of mechanisms that blunt the SAME mempool-leak problem. This is the
practical shortlist, ranked by production readiness for a startup fund (not by cryptographic
purity):

### 6a. Intent-based execution / Dutch auctions / solver auctions
- **How it works:** the fund signs an INTENT ("swap X for Y, at most Z slippage, by time T"),
  NOT a raw order. Solver/relayer bots compete in an off-chain auction to fill it; the field
  winner submits a single settlement tx. The fund's pre-trade size/intent is visible only to
  the auction participants under MEV commitments, not to the whole mempool.
- **Mature examples:** Cow Protocol (CoWSwap) batch auctions with MEV protection; UniswapX /
  Across. Auction-solved RFQs are the current industry default for mid-size flows.
- **Trade-offs:** mild trust in a small solver set; competition among solvers generally aligns
  price toward the best execution; still exposes intent to solvers (acceptable - they are
  bound by auction mechanics, not by transparency to predators).

### 6b. Private / encrypted mempools and MEV-Share (builder-led)
- **How it works:** the fund sends the tx to a **private mempool** (Flashbots Protect /
  MEV-Share, or a trusted builder/sequencer) instead of the public broadcast mempool. The
  builder keeps it out of the public queue until inclusion. MEV-Share additionally auctions
  the "MEV" the tx creates back to the fund (refund/revenue sharing).
- **Mature examples:** Flashbots relay + MEV-Share; private RPC endpoints from major wallets
  and exchanges.
- **Trade-offs:** cheap and immediate to adopt (no new venue, just a different broadcast
  path); but trusts the builder/sequencer not to leak or steal; only hides the order until
  inclusion - once mined it is public. Best "fix today," weakest long-term privacy.

### 6c. Order-Flow Auctions (OFA)
- **How it works:** a marketplace explicitly auctions the RIGHT to execute a given flow to
  the bidder who returns the most back to the flow (the fund). Institutional and CEX order
  flow is sold this way; per-flow MEV is converted into a rebate.
- **Trade-offs:** turns the MEV tax negative (you get PAID); but requires a liquid OFA market
  and counterparties that value the flow; heavier integration/negotiation.

### 6d. RFQ / off-chain bilateral venues
- **How it works:** the fund requests a firm quote from 1-n market makers off-chain, picks
  the best, and only the winning quote gets executed - no public order ever exists.
- **Mature examples:** OTC desks, RFQ DEX layers, institutional CEX RFQ.
- **Trade-offs:** the practical institutional default for size today; zero mempool exposure by
  construction; but concessions/impact are negotiated, not eliminated, and it reintroduces a
  trusted-counterparty coordination layer.

### 6e. Commit-reveal & submarine-style privacy (adjacent to 6a/6b)
- **How it works:** the fund commits to an order hash first; the reveal (actual details)
  happens only at/after inclusion, denying bots a usable pre-trade window.
- **Trade-offs:** simple primitive, but alone is awkward for matching; usually appears as an
  ingredient inside intent/RFQ systems rather than standalone.

### 6f. ZK dark pools (Renegade/Penumbra) - the earlier sections
- Strongest privacy (zero plaintext anywhere), weakest current depth.

### Comparative read for THIS fund (latency-agnostic, medium-frequency rebalances of size)
| Mechanism | Privacy of pre-trade intent | Production readiness (2026) | Institutional size | MEV outcome |
|---|---|---|---|---|
| Private mempool / MEV-Share | Partial (hidden till inclusion) | **High - adopt now** | High | Tax reduced/rebated |
| Intent/Dutch (CoW, UniswapX) | High (intent, solver-auction) | **High** | Med-High | Tax reduced |
| RFQ / bilateral | High (off-chain) | **High** | High | Spread internalized |
| Order-Flow Auction | High | Medium | Med | Turned into rebate |
| ZK dark pool (Renegade/Penumbra) | **Full (zero plaintext)** | Low-Med | Low (depth-gated) | Tax ELIMINATED but thin |
  
### Steering update: the pragmatic adoption ladder
Do NOT jump straight to ZK dark pools - they are the end-state, not the entry point. The
desk should climb a **ladder of increasing pre-trade privacy** as depth allows:

1. **Today (no build):** route medium-frequency rebalances through a PRIVATE MEMPOOL
   (Flashbots MEV-Share / private RPC) to cut the public-mempool leak immediately, plus use
   RFQ/CEX RFQ for the largest sizes. Measure real MEV leakage on current AMM path first.
2. **Short term:** adopt INTENT-based execution (CoW/UniswapX batch auctions) for the
   mid-size tail where it has depth - captures most of the MEV reduction with a far more
   liquid venue than a dark pool.
3. **Watch/build the ZK path:** only once a pair the desk trades shows real on-protocol
   depth should it test Renegade/Penumbra-style dark-pool crossing at oracle mid, as a
   spread-free complement on the pairs where depth exists.

The ZK dark-pool thesis is CORRECT as a north-star (the only path to *eliminate* the MEV
tax on full pre-trade intent), but the fund should be execution-total-cost-cognizant, not
ideology-driven: private-mempool + intent + RFQ likely already captures 80-90% of the MEV
savings at 1/100th of the integration complexity today, and ZK dark pools are a forward
option to hold until their depth matures.

*Continuation artifact note: this section reflects the "continue research" instruction on
the 2nd firing. quantum-intelligence retrieval still returning 503, so breadth is from
protocol knowledge; production-readiness labels are directional.*


---

## 7. CONTINUATION (2026-08-16, 3rd firing): from architecture scan to an implementable plan

The prior sections answered "what are the options and which is best." This section answers
"How do we actually start using this, with a measurable exit." It converts the ladder into a
concrete execution-booking change + a gated MVP probe.

### 7.1 Booking-route decision matrix (tie to THIS fund's orders)
Classify each rebalance order by size and urgency, then route via a rule. Sizing bands are
directional - replace with the desk's actual ADV/notional distribution before using.

| Order class | Typical size | Recommended route TODAY | Why |
|---|---|---|---|
| Large / illiquid alt | > ~1-2% of pool depth | CEX RFQ / OTC bilateral | Needs firm quote + size; avoid public mempool + AMM impact |
| Mid tail | 0.2-1.5% of depth | Intent/Dutch (CoW, UniswapX) if depth present, else RFQ | Solver auction internalizes spread, MEV-reduced |
| Liquid / small | < maker-depth | Private mempool (Flashbots MEV-Share) vs AMM | Lowest-friction MEV cut; revert tolerant |
| Any that must be atomic/hidden | sensitive dirn | ZK dark pool (only where on-protocol depth exists) | Full pre-trade privacy; thin liquidity |

### 7.2 The gated MVP probe (2-3 weeks, low build)
Goal: measure whether MEV protection actually saves money AFTER all-in cost, before
committing any flow. Do NOT re-platform the whole execution stack.

1. **Baseline (week 1):** for the next ~20 live rebalance orders, log the CURRENT AMM/public-
   mempool path: actual slippage, price-impact, gas, and any observed sandwich/front-run
   (detect via tx-position-in-block + price-reversal after fill). Produce a per-order MEV-
   leakage number. This is the "before" that the replacement thesis must beat.
2. **Pilot (weeks 2-3):** route a DISJOINT subset (e.g. every 2nd order / a fixed 20% of
   notional) through the privacy-route ladder - MEV-Share private RPC for the liquid/small
   class and intent/RFQ for the mid/large class. Log the same metrics.
3. **Compare:** per-order all-in cost (fills + fees + GAS + impact) privacy-route vs baseline,
   and MEV-leakage dollars. Compute a paired t-statistic on the per-order cost delta.

### 7.3 Go / no-go thresholds (pre-committed, avoid hindsight bias)
Proceed to route the indicated class through the privacy route only if the pilot shows, on
the paired per-order comparison (n >= 15 per class):
- **GO:** median all-in cost improvement >= ~5bps/order AND no class shows a significant
  *worse* tail (p95 degradation > 5bps is a veto for that class).
- **NO-GO / fallback:** if MEV-SAVE is < 3bps after all-in cost, OR any class shows worse
  p95, keep that class on the incumbent route and treat the MEV thesis as NOT proven for
  it, and do NOT extrapolate to larger sizes without a fresh probe.
- **Guardrails:** every pilot order still goes through the desk's existing risk/trade gates
  (trade_qualifies etc.); the pilot is additive execution routing, NOT a strategy change.

### 7.4 Explicit non-goals (prevent scope creep)
- Not replacing the signal/portfolio layer; shape changes are independent of booking route.
- Not building an in-house ZK/MPC stack; this is a *consumption* decision - use mature venues.
- Not chasing the lowest achievable fill at the expense of the fund's risk gates.

### 7.5 What "done" looks like
A one-page routing policy (size/urgency -> venue) with the pilot's measured per-order cost
delta, the MEV-leakage baseline, and a dated go/no-go for each order class. ZK dark pools
remain a watch-only forward option re-evaluated only when on-protocol depth on a traded pair
appears.

*3rd-firing continuation note: quantum-intelligence still 503; figures are directional and
must be replaced with the desk's own ADV/slippage data before the GO gate is applied.*


---

## 8. CONTINUATION (2026-08-16, 3rd continue): the skeptic's audit - can this thesis be falsified?

Every prior section assumed MEV-leak is materially hurting THIS fund. That premise is UNTESTED
locally, and this desk's own culture (e.g. the "overlap SR>3 was autocorrelation" correction)
rightly demands the counter-case be written down before engineering effort is spent. This
section steelmans the view that the execution work may be premature, misdirected, or moot.

### 8.1 The thesis' falsifiable prediction
If MEV-avoidance is economically real FOR THIS FUND, then on its current AMM/public-mempool
path it should observe, over a sample of rebalances:
- **P1: material leakage** - a measurable adverse-selection / sandwich / front-run cost
  (e.g. fills systematically worse than post-trade fair value + fees) that the privacy ladder
  would remove.
- **P2: net-positive saving** - routing through MEV-Share / intent / RFQ yields >= ~5bps/order
  all-in improvement (Section 7.3), not just in gross terms but AFTER venue fees, gas, and any
  worse price concessions.
- **P3: depth is NOT the binding constraint** - i.e. the reason the fund does not use these
  venues today is inertia, not that the venues lack the fund's order sizes.

Falsify ANY of these and the migration is not worth doing now.

### 8.2 Steelman: why the migration may be WRONG or PREMATURE for this fund
1. **The leakage may be immaterial at this fund's true scale.** A startup fund's rebalance
   notionals, spread thin across liquid mid-caps, may be too small to attract sandwich bots at
   all. If untouched orders already fill near mid + fees, there is nothing to save - the whole
   premise of a "fatal mempool exposure" may be a large-institutional problem, not THIS fund's.
   The baseline probe (7.2 week 1) exists precisely to settle this; it MUST run first.
2. **Execution is downstream of a bigger unsolved constraint.** The desk's own logs show
   signal alpha that is thin and, at times, within noise (capacity-tier momentum IC within ~1
   SE; PEAD short is a net loser). If per-trade edge before costs is small, then saving a few
   bps on execution does not move the PnL needle; effort may be misallocated vs. improving the
   signal or acquiring true micro-cap data (the recurring data gate). MEV-saving is a second-
   order lever when the alpha itself is the binding constraint.
3. **Adoption adds new risk surfaces.** Private mempools/MEV-Share trust a builder; intent
   execution adds solver counter-party concentration; RFQ adds CEX/OTC counterparty risk. For a
   small fund these introduce operational and trust dependencies that can be net-negative even
   when gross savings are positive.
4. **ZK dark pools are not a near-term lever at all.** Low depth means a small fund cannot get
   real size without moving the market inside the dark pool anyway - "spread-free at mid" is
   only meaningful if there is a counterparty of matching opposite size, which is rare today.

### 8.3 The disciplined ordering (matches the desk's gate-first culture)
Do NOT pick a venue until (7.2 week-1) baseline has quantified leakage. If P1 fails (leakage
within fee noise), the honest conclusion is: **the mempool thesis does not apply at this
scale; no routing change needed; revisit only if size grows.** That is a valid, publishable
result, not a failure. Only if P1 (and then P2/P3) hold does the Section-7 ladder become
operationally relevant.

### 8.4 Bottom line
The architecture is sound and the ZK dark pool is the correct industry north-star. But the
desk's own evidence-gating means the FIRST deliverable is a leakage baseline, not a venue
migration. The research arc is now complete: problem -> architecture -> toolkit -> ladder ->
route matrix -> gated MVP -> falsifiability. Recommend STABILIZING this report (no further
breadth) and, if pursued, running the Week-1 baseline probe on live rebalances to test P1.

*4th continue note: quantum-intelligence still 503 (7th attempt); falsification thresholds are
directional. This section is the capstone; further "continue research" on this prompt should
prompt a live measurement, not more writing.*
