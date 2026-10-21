"""Portfolio-of-strategies: combine strategy daily returns, compute the
combined OOS Sharpe (user target: portfolio Sharpe >= 3), 2026-08-05.

Strategies:
  A  L/S CAPM-alpha GBRT (tw320_d4, 8y panel)   -> results/live_signal/daily_returns.csv
  B  US pairs mean-reversion (v4 Kalman, WF)     -> reports/pairs_portfolio_sim.json (daily.net)
  C  RV curve/FX spreads                         -> EXCLUDED (OOS Sharpe -2.02)

Portfolio: vol-parity (target vol = 10% ann) and equal-weight on the
overlapping calendar; correlation matrix reported.  Allocation is a pure
ex-post combination of walk-forward streams (each strategy's own OOS
discipline is inside its stream).
"""
from __future__ import annotations
import os, sys, json

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LS_RES = os.path.join(ROOT, "tools/quant/ls/results")
REPORTS = os.path.join(ROOT, "tools/quant/reports")


def shp(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return 0.0
    return r.mean() / r.std() * np.sqrt(252)


def main() -> int:
    # A: L/S champion daily returns (deep-panel live signal run)
    ls = pd.read_csv(os.path.join(LS_RES, "live_signal", "daily_returns.csv"),
                     index_col=0, parse_dates=True)["daily_return"].rename("ls_equities")

    # E: FX momentum (honest stream; SR ~0.16, corr ~0)
    fx_path = os.path.join(LS_RES, "fx_momentum", "daily_real.csv")
    if os.path.exists(fx_path):
        fx = pd.read_csv(fx_path, index_col=0, parse_dates=True)["daily_return"].rename("fx_momentum")
    else:
        fx = None

    # B: pairs MR daily net returns (risk-scaled: net[i] = sigma * risk_frac)
    sim = json.load(open(os.path.join(REPORTS, "pairs_portfolio_sim.json")))
    run = sim["runs"][0]
    daily = run["daily"]
    pairs = pd.Series(daily["net"], index=pd.to_datetime(daily["dates"]),
                      name="pairs_mr")

    # C,D: cross-asset trend legs (3.8bps one-side cost already baked in)
    tsmom = pd.read_csv(os.path.join(LS_RES, "cross_asset_tsmom", "daily_real.csv"),
                        index_col=0, parse_dates=True)["daily_return"].rename("tsmom")
    gold = pd.read_csv(os.path.join(LS_RES, "gold_trend", "daily_real.csv"),
                       index_col=0, parse_dates=True)["daily_return"].rename("gold_trend")

    streams = [ls]
    if fx is not None:
        streams.append(fx)
    df = pd.concat(streams, axis=1, sort=True)
    df = df[df.notna().all(axis=1)]
    print(f"overlapping days: {len(df)}  ({df.index[0].date()}..{df.index[-1].date()})")
    print("\ncorrelation matrix:")
    print(df.corr().round(3))
    print("\nindividual ann. Sharpe (overlap):")
    for c in df:
        print(f"  {c}: {shp(df[c]):.2f}  vol={df[c].std()*np.sqrt(252):.2%}")

    # ---------------------------------------------------------------
    # Fix (2026-08-06): pairs_mr was built but NEVER appended to the
    # stream list, so it was silently dropped from the portfolio.
    # Now included as a diversifier with proper handling of its sparse
    # (many zero) daily book. Gate: only hold legs with positive OOS
    # Sharpe over the common overlap.
    # ---------------------------------------------------------------
    def _portfolio(streams_df, label):
        gate = {c: shp(streams_df[c]) for c in streams_df.columns}
        keep = [c for c, s in gate.items() if s > 0.0]
        if not keep:
            print(f"[{label}] no OOS-positive legs; empty")
            return None
        g = streams_df[keep]
        vols = g.std().replace(0, np.nan)
        w_inv = (1.0 / vols) / (1.0 / vols).sum()
        comb = g.mul(w_inv, axis=1).sum(axis=1)
        comb = comb / comb.std() * 0.10  # target 10% ann vol
        # equal weight for comparison
        we = pd.Series(1.0 / len(g.columns), index=g.columns)
        combe = g.mul(we, axis=1).sum(axis=1)
        combe = combe / combe.std() * 0.10
        print(f"\n[{label}] n_days={len(streams_df)} windows={list(g.columns)}")
        print(f"  OOS gate (sharpe)>0 : { {c: round(s,2) for c,s in gate.items()} }")
        print(f"  vol-parity w        : {dict(round(w_inv,3))}")
        print(f"  portfolio Sharpe (vol-parity) : {shp(comb):.2f}")
        print(f"  portfolio Sharpe (equal-wt)   : {shp(combe):.2f}")
        return {"n_days": len(streams_df), "corr": streams_df.corr().round(3).to_dict(),
                "sharpe_individual": {c: round(gate[c], 3) for c in gate},
                "sharpe_portfolio_volparity": round(shp(comb), 3),
                "sharpe_portfolio_equal": round(shp(combe), 3),
                "w_volparity": dict(round(w_inv, 3)), "w_include": keep}

    # (1) Clone of the ORIGINAL buggy behavior is NOT used; we always
    #     include pairs in the diversified book on the common overlap.
    df3 = pd.concat([ls, fx, pairs], axis=1, sort=True)
    df3 = df3[df3.notna().all(axis=1)]
    core = _portfolio(df, "core (ls+fx)")
    all3 = _portfolio(df3, "diversified (ls+fx+pairs)")

    # Window-consistent full book: all 5 legs on the LONGEST common window,
    # non-trading padded to 0 (honest book view -- avoids 508-day selection bias).
    full = pd.concat([ls, fx, tsmom, gold, pairs], axis=1, sort=True)
    full = full.ffill().fillna(0.0)
    book = _portfolio(full, "full-book (ls+fx+tsmom+gold+pairs, padded-0)")

    # SCRAMBLE-VALIDATED book (2026-08-06): NO candidate leg other than equity
    # L/S beats a price-lag noise control:
    #   tsmom/gold/fx  -> P(noise>real) ~44-52% (fail, already logged)
    #   pairs_mr       -> scrambled OOS SR 4.0-4.8 vs real 6.96 (FAILS as well)
    # So no genuinely independent multi-leg portfolio can yet be validated.
    vdf = pd.concat([ls], axis=1, sort=True).ffill().fillna(0.0)
    vbook = _portfolio(vdf, "VALIDATED book (ls only - only scramble-ok leg)")

    out = {"overlap_core": core, "overlap_diversified": all3, "full_book": book,
           "validated_book": vbook, "scramble_note":
           "ONLY ls_equities passes price-lag noise control; tsmom/gold/fx "
           "P~44-52% (fail), pairs scrambled SR~real (fails). No multi-leg "
           "diversifier is scramble-validated; standalone champion is the "
           "only honest high-Sharpe asset today."}
    with open(os.path.join(LS_RES, "strategy_portfolio.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"\nsaved -> {LS_RES}/strategy_portfolio.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
