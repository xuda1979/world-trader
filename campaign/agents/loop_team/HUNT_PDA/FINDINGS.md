# HUNT_PDA — FINDINGS (iter9) — NEW-DATA HUNT #6

**VERDICT: NEGATIVE — 48 variants (PD-absorption / SOMA / FIMA / PD-indirect shares from the
FIXED auction panel, 1-day availability lag), best soma_share longflat 0.53-0.54 = mostly
B&H drift (B&H QQQ SR 0.77 over same span, exposure only 0.38), scramble p 0.04-0.22 (marginal),
4-6 neg years. Champion blend dSR < 0 at every weight (corr too low, own SR too weak).
The auction-demand microstructure does not carry daily timing edge at 6.4bps even with the
new dealer-basis fields. TDD: 3 tests pass (share+lag, z no-lookahead).**

Gates: ALL NO. DEAD_IDEAS += "PD/SOMA/FIMA auction-flow shares as equity gates", dead,
"best 0.54/4neg = drift (B&H 0.77); blend dSR<0 all weights".
Do not re-run: share z/longflat on Note+Bond auctions vs SPY/QQQ/DIA.
HUNT_PDA DONE
