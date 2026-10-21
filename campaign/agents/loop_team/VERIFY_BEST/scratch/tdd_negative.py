"""TDD negative controls (superpowers RED discipline): EVERY gate used by VERIFY_BEST must
demonstrably FAIL on a tampered input. If any assertion fails, the gate itself is broken."""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt import reconcile as R, gates as G, metrics as M

fails = []
def check(name, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    if not cond: fails.append(name)

idx = pd.bdate_range('2020-01-01', periods=500)
rng = np.random.default_rng(1)
r = pd.Series(rng.normal(0.0005, 0.01, 500), index=idx)

# N1: repro_ok must CATCH a 1e-6 perturbation (byte-repro gate is not vacuous)
check("N1 repro_ok catches 1e-6 tamper", not R.repro_ok(r, r + 1e-6))
check("N1b repro_ok accepts identity", R.repro_ok(r, r.copy()))

# N2: ledgers_reproduce must CATCH the BLOTTER_TESTER CRITICAL bug class
# (ledger that omits charged costs must NOT reproduce the champion)
champ = pd.Series(0.0005 - 0.00002, index=idx)   # net of a 2bp/day cost
led = pd.DataFrame({'date': idx, 'pnl_contrib': 0.0005, 'cost_total': 0.00002})
check("N2 ledger WITH costs reproduces", R.ledgers_reproduce(led, champ)['ok'])
led_broken = led.copy(); led_broken['cost_total'] = 0.0   # cost-omitting ledger
res = R.ledgers_reproduce(led_broken, champ)
check("N2b cost-omitting ledger FAILS (Tester-bug class caught)", not res['ok'])
print(f"     N2b max_diff on broken ledger = {res['max_diff']:.3e} (must be ~2e-5)")

# N3: turnover_reconciles must CATCH inflated qty
w = pd.DataFrame({'a': rng.normal(0, .1, 500).cumsum(), 'b': rng.normal(0, .1, 500).cumsum()}, index=idx)
qty_led = pd.DataFrame({'sleeve': ['a']*500 + ['b']*500,
                        'qty_notional': np.r_[w['a'].diff().abs().values, w['b'].diff().abs().values]})
check("N3 turnover reconciles honestly", R.turnover_reconciles(qty_led, w)['ok'])
qty_bad = qty_led.copy(); qty_bad.loc[qty_bad.sleeve == 'a', 'qty_notional'] *= 2.0
check("N3b 2x-inflated qty FAILS", not R.turnover_reconciles(qty_bad, w)['ok'])

# N4: flattening gate — constant series must FAIL uniq, an honest noisy series must pass
const = pd.Series(1e-9, index=idx)
check("N4 constant series uniq_ratio ~0 (<0.08) -> gate flags flattening",
      not G.run(const)['uniq_ok'])
check("N4b noisy series passes uniq", G.run(r)['uniq_ok'])

# N5: degeneracy demo setup — np.roll on RETURNS preserves SR (the return-roll scramble is void)
rr = pd.Series(rng.normal(0.0004, 0.008, 2000))
sr_real = M.sharpe_d(rr)
srs = [M.sharpe_d(pd.Series(np.roll(rr.values, L))) for L in (1, 21, 252, 999)]
check(f"N5 return-roll preserves SR exactly (real {sr_real:.6f}; rolls "
      f"{['%.6f' % s for s in srs]}) -> degenerate",
      all(abs(s - sr_real) < 1e-9 for s in srs))

# N6: position-lag scramble must DESTROY a timing-dependent book (valid test)
x = pd.Series(rng.normal(0, .01, 2000)); sig = x.shift(1).fillna(0)  # honest T+1 momentum-ish
book = sig * x
p, sr_real = G.scramble_positions(sig.values, x.values, n=200, rng=np.random.default_rng(0))
sr_rolled = M.sharpe_d(pd.Series(np.roll(sig.values, 500) * x.values))
check(f"N6 position-lag: real SR {sr_real:.2f}; rolled-position SR {sr_rolled:.2f}; "
      f"scramble p={p:.3f} (<0.5 -> test has power)", sr_rolled < sr_real and p < 0.5)

print("\nRED-CONTROL VERDICT:", "ALL GATES HAVE TEETH" if not fails else f"BROKEN GATES: {fails}")
sys.exit(1 if fails else 0)
