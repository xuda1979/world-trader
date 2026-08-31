# C4 Round-2: construction research on the NEW 16-pool (champion upgrade path)

Current champion: 16-pool EW-of-vt10 + global vt + 126d DD throttle (thr .04 fr .5), vt IS-selected.
Your round-1 discovery stands: throttle lb 252 gives more headroom; the pool changed (C2fly
quarantined, 2 natgas sleeves added). Re-run your protocol on the CURRENT pool:

1. IS-protocol selection: grid (tgt .08..11, thr .025/.03/.04/.05, fr .4/.5/.6, lb 126/189/252)
   on IS 2008-2016 with sub-DD compliance; freeze argmax; single OOS reveal. Compare vs the
   GOAL80-fixed throttle (thr.04 fr.5 lb126) at the same IS rule. Which wins OOS honestly?
2. Per-sleeve throttles (round-1 idea 1) on the new pool — IS-tuned, OOS-revealed.
3. Trailing-correlation EW: weekly inverse-vol x avg-corr-adjusted weights (trailing 126d) —
   compare vs plain EW-of-vt10 on IS, OOS-reveal if IS better.
4. 2023 stress test: the pool's 2023 (+195% at vt.095) has huge throttle interactions — verify
   no config makes 2023 dominate the IS choice wrongly (2023 is IN IS for this protocol —
   document selection sensitivity by re-running IS on 2008-2019 subwindow and comparing picks).

Deliver C4_construct_v2.csv if it beats champion OOS with MaxDD<=8% everywhere. All IS/OOS
disclosure. Last line: ROUND 2 DONE
