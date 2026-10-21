"""Funding-capture backtest on Hyperliquid historical funding data.

Question (strategic thesis Pillar 1+3): is delta-neutral funding capture on a
DEX perp venue (Hyperliquid) a real, durable, net-positive structural edge for
a small-capacity operator?

The ONLY data Hyperliquid's sandboxed mirror exposes is the hourly fundingRate
history (~500 rows/coin ending a fixed 2023 cutoff). We do NOT have the perp/spot
price series for the same window, so this backtest establishes the CARRY leg:
  - Is funding predictive? Does entering on extreme funding and riding to
    reversion collect more carry than costs?
  - What net annualized yield does a selective capture rule earn on the funding
    leg alone?

Strategy (delta-neutral funding capture, carry leg):
  funding >  +enter_thr  -> SHORT the perp (longs pay shorts; shorts collect)
  funding <  -enter_thr  -> LONG  the perp (shorts pay longs; longs collect)
  exit when |funding| reverts <= exit_thr.
While in position, collect fundingRate each hour (sign-adjusted).
Costs applied as discrete round-trip events (entry+exit) — Hyperliquid taker
~4.5bps/side x2 legs (perp + spot), + slippage -> ~30bp round-trip; sweep.

NOT modeled here: basis drift (perp price converging to spot) — the material
unmodeled risk. This establishes the carry-leg upper bound; price data would be
needed to bound basis. Documented honestly.
"""
from __future__ import annotations
import pandas as pd, glob, os, numpy as np, json, argparse

DATADIR = os.path.join(os.path.dirname(__file__), "data")

def load_coin(coin):
    df = pd.read_csv(os.path.join(DATADIR, f"fund_{coin}.csv"))
    df = df.sort_values("time_ms").reset_index(drop=True)
    return df["fundingRate"].to_numpy() * 100.0  # % per hour

def run(coin, enter_thr, exit_thr, cost_rt, f):
    """f: hourly funding % array. Returns dict of results (carry leg only)."""
    n = len(f)
    pos = 0          # 0 flat, +1 long, -1 short
    side = np.zeros(n, dtype=int)
    costs_pp = np.zeros(n)     # point-in-time cost hits (%)
    for i in range(n - 1):
        fi = f[i]
        if pos == 0:
            if fi >= enter_thr:
                pos = -1; side[i] = -1
                costs_pp[i] += cost_rt / 2.0        # entry cost
            elif fi <= -enter_thr:
                pos = 1;  side[i] = 1
                costs_pp[i] += cost_rt / 2.0
        else:
            if abs(fi) <= exit_thr:
                pos = 0; side[i] = 0
                costs_pp[i] += cost_rt / 2.0        # exit cost
            else:
                side[i] = pos
    # carry at hour i payable for holding through that hour:
    #   LONG collects when funding < 0 -> carry = -funding
    #   SHORT collects when funding > 0 -> carry = +funding
    carry = np.where(side > 0, -f, np.where(side < 0, f, 0.0))
    # Funding for the hour is realized at the funding timestamp; we credit the
    # hour BEFORE we'd react (i.e., position side[i] earns funding f[i]).
    net = carry - costs_pp
    hours = n
    days = hours / 24.0
    invested = (net != 0).mean()   # fraction of hours with a position
    total_net = net.sum()
    # annualized on full capital = per-day net * 365
    ann_full = total_net / days * 365.0
    ann_inv = total_net / (invested * days) * 365.0 if invested > 0 else 0.0
    n_pos = int(((side[1:] != side[:-1]) & (side[1:] != 0)).sum() +
                (side[0] != 0))
    return {
        "coin": coin, "n_hour": int(hours), "days": round(days, 1),
        "invested_frac": round(invested, 3),
        "net_carry_%_window": round(total_net, 2),
        "ann_ret_%_full_cap": round(ann_full, 2),
        "ann_ret_%_inv": round(ann_inv, 2),
        "n_positions": int(n_pos),
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--enter", type=float, default=0.02)
    ap.add_argument("--exit", type=float, default=0.005)
    ap.add_argument("--cost_rt", type=float, default=0.30)
    ap.add_argument("--coins", nargs="*", default=None)
    args = ap.parse_args()

    coins = args.coins or sorted(os.path.basename(f)[5:-4]
                                 for f in glob.glob(f"{DATADIR}/fund_*.csv"))
    results = []
    for c in coins:
        try:
            f = load_coin(c)
        except Exception as e:
            print(f"{c}: load fail {e}"); continue
        r = run(c, args.enter, args.exit, args.cost_rt, f)
        results.append(r)
        print(f"{c:5s} inv={r['invested_frac']:.2f} ann_full={r['ann_ret_%_full_cap']:7.1f}% "
              f"ann_inv={r['ann_ret_%_inv']:7.1f}% win%={r['net_carry_%_window']:7.2f} pos={r['n_positions']}")
    dfr = pd.DataFrame(results)
    print("\n=== AVERAGE (all coins) ===")
    print(f"ann_full {dfr['ann_ret_%_full_cap'].mean():.1f}% | ann_inv {dfr['ann_ret_%_inv'].mean():.1f}% | "
          f"inv {dfr['invested_frac'].mean():.2f} | wins {dfr['net_carry_%_window'].mean():.2f}")
    out = {"enter_thr": args.enter, "exit_thr": args.exit, "cost_rt": args.cost_rt, "by_coin": results}
    rdir = os.path.join(os.path.dirname(__file__), "..", "reports"); os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, "hl_funding_capture.json"), "w") as fh:
        json.dump(out, fh, indent=2)
