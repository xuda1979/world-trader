# K1-KURTOV PRE-REGISTRATION (2026-09-30, locked before any result was computed)

GOAL5DIR action D: "Re-examine kurtosis-filter scaling as an overlay on K1's
existing champion sleeves, not a standalone (SR 1.06 → could lift some sleeves'
per-gross IR)."

## Question

Does scaling the V7.1 champion's 20 sleeve weights by inverse trailing excess
kurtosis (fat tails -> smaller weight) improve the champion OOS beyond noise?

## Prior evidence (both directions, honestly stated)

- K1 history (K1_tailhistory_results, 2026-09-16): the prescribed
  inverse-tail-kurtosis scaling HURT trend sizing (SR 0.26 vs 0.43 plain) on
  CORN+QQQ standalone — but that was a 2-asset standalone, not the 20-sleeve book.
- GOAL5DIR leaderboard: kurt-filter H22K-2 standalone SR 1.06, corr 0.69 —
  "slight enhancer, not a sleeve".
- F2-DDC (this session): ALL drawdown-control overlays on the champion REJECT —
  the champion is at the efficiency frontier; expect REJECT here too.

## Data (frozen)

- 20 sleeve daily return CSVs (paths = OPT_20V71_weights.csv index; column 'ret'
  or first column; campaign load convention per reproduce_v71).
- Weights: OPT_20V71_weights.csv (20 sleeves; two sleeves weight 0 — the
  A4-zeroed ones — and stay 0; overlay never resurrects a zeroed sleeve).
- Champion daily net: OPT_20V71_FULL_LEDGER.csv sum(pnl)-sum(cost) (canonical).
- Window: 2009-01-01 .. 2026-09-22; IS < 2017-01-01; OOS >= 2017-01-01.

## Pre-registered overlay (the full grid — nothing added after seeing results)

Let w_i = champion weight of sleeve i (constant vector, zeroed sleeves stay 0).
Let k_i,t = excess kurtosis of sleeve i's daily returns over the trailing
K days (K in {126, 252, 378}), computed on data <= t-1 (T+1 causal).
Scale: s_i,t = 1 / (1 + clip(k_i,t, 0, 20))    [K1's prescribed form, clipped]
Effective weight: w_eff_i,t = w_i * s_i,t / sum_j(w_j * s_j,t)   [renormalized
to gross 1 — the overlay reallocates, it never de-grosses; a de-gross variant is
a DD-control policy and was already REJECTED by F2-DDC].
Overlay return: r_ov,t = LEV * sum_i (w_eff_i,t - w_i) * r_i,t  where r_i,t is
sleeve i's day-t return (weights known at t-1).
Overlay cost: 6.4bps * LEV * sum_i |w_eff_i,t - w_eff_i,t-1| (the overlay's own
rebalancing, charged at the campaign's full-cost convention on the whole book's
deviation turnover).
Total: r'_t = r_champ,t + r_ov,t - cost_ov,t.

3 arms (K in {126, 252, 378}). No other knobs. No post-hoc grid.

## Gates (identical to F2-DDC, all on OOS)

G1. OOS monthly SR >= champion OOS monthly SR + 0.10.
G2. OOS MaxDD >= champion OOS MaxDD.
G3. OOS ann >= champion OOS ann - 1.0pp.
G4. Neg years (OOS) == 0.
G5. Overlay turnover <= 6/yr (overlay-only, book-relative).
G6. OOS SR edge >= 0 (sign consistency).

VERDICT: PROCEED only if the IS-best K clears ALL gates OOS; else REJECT and
GOAL5DIR action D is closed with a documented negative.

DONE K1_KURTOV_PREREGISTRATION
