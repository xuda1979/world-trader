#!/usr/bin/env python3
"""HUNT_CMDT2 ROUND 3 — the two genuinely untested commodity spread-momentum books on the
new 2007-waived ETF data (fetched by HUNT_CMDT2_round3_fetch.py, provenance-verified live
vs TwelveData 2026-09-07).

Charter round-3 (b) pairs:
  USCI vs DBC : front-month basket vs broad basket (roll-profile spread).
  DBE vs DBP  : energy basket vs precious-metals basket (sector relative-value spread).
Variants: L/S dollar-neutral + long-only. Signal = sign of the trailing `win`-day change in
the log price ratio ln(A/B), taken from closes <= signal day; trade T+1 (net_of shift).
NOT the dead BNO-vs-USO location spread (DEAD_IDEAS HUNT_CMDT2) — different family.

Honesty per GATES_CONTRACT.md, via the R1/TDD-green machinery (net_of/evaluate/scramble):
 T+1; 6.4bps on FULL |dW| + 0.5%/yr borrow; vol-target 10% ann trailing (clip 3.0); scramble
 200x re-costed; halves >= 0.5; <= 2 neg years each > -5%; FULL net SR >= 1.0; |corr| < 0.15
 vs champion. Spans are INCEPTION-LIMITED (USCI 2010-08, DBC 2008-01, DBE 2007-01, DBP
 2008-01) — disclosed per config; the books are judged on their own honest span.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np
import pandas as pd
import HUNT_CMDT2_round1 as H          # reuse net_of/evaluate/trim_warmup (TDD-green R1)

trim_warmup = H.trim_warmup            # re-exported for the TDD suite + sleeve savers

ROOT = "/Users/daxu/software/world-trader"
SPREAD_GROSS = 1.0                     # max |w| per leg (L/S uses gross/2 per leg)


def load_close(sym):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/{sym}.csv",
                     index_col=0, parse_dates=True)
    return df['close'].astype(float)


def px_frame(syms):
    return pd.concat({s: load_close(s) for s in syms}, axis=1, sort=True).sort_index()


def spread_vol_scale(px, win=126, target=0.10, clip=3.0):
    """Trailing-only position damp: target / realized vol of the daily log-spread change.
    `px` is a 2-leg frame (columns used positionally: first = leg A, second = leg B).
    Uses data <= t exclusively (rolling window, shift(1) so the day-t decision sees vol <=
    t-1); 0 during the warmup. EXT-variant sizing, not part of the main sign grid."""
    A, B = px.columns[0], px.columns[1]
    sp = np.log(px[A] / px[B])
    vol = sp.diff().rolling(win, min_periods=win // 2).std() * np.sqrt(252)
    s = (target / vol.replace(0, np.nan)).clip(upper=clip)
    s = s.shift(1)
    return s.where(vol.shift(1).notna(), 0.0).fillna(0.0).rename('scale')


def run_spread_momentum(px, R, a, b, win=126, long_only=False, gross=SPREAD_GROSS,
                        vol_damp=False):
    """Spread momentum on the ln(A/B) ratio. L/S variant is dollar-neutral (gross/2 per leg);
    long-only variant goes flat when the spread trend is DOWN (never shorts either leg).
    Signal at day i uses the ratio through i-1 (T+1); no ffill pairs a fresh leg against a
    stale one — both legs share the ETF calendar and rows with any NaN are flat."""
    sp = np.log(px[a] / px[b])
    mom = sp.diff(win)
    sig = np.sign(mom).fillna(0.0)
    scale = spread_vol_scale(px, win=win) if vol_damp else pd.Series(1.0, index=px.index)
    g = gross if long_only else gross / 2.0
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    if long_only:
        W[a] = (sig > 0).astype(float) * g * scale
    else:
        W[a] = sig * g * scale
        W[b] = -sig * g * scale
    net, We, gross_r = H.net_of(W, R)
    return net, We, gross_r, W


def save_sleeve(name, net, We, res, extra_meta=""):
    """Contract item 4: sleeves/{name}.csv [date,ret] + .meta (same format as R1/R2)."""
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
    os.makedirs(d, exist_ok=True)
    net = H.trim_warmup(net, We)
    pd.DataFrame({'ret': net.values},
                 index=[t.strftime('%Y-%m-%d') for t in net.index]) \
        .to_csv(f"{d}/{name}.csv", index_label='date')
    with open(f"{d}/{name}.csv.meta", 'w') as f:
        f.write(f"name={name}\nstatus={'PASSED_ALL_GATES' if res.get('pass') else 'FAILED_NO_PROMOTION'}\n")
        f.write(f"SR={res['sr']:.3f} ann={res['ann']*100:.1f}% vol={res['vol']*100:.1f}% "
                f"H1={res['h1']:.2f} H2={res['h2']:.2f} negyrs={res['neg']} "
                f"worstyr={res['worst']*100:.1f}% scramble_p={res['p']:.3f} "
                f"corr_champ={res['corr']:.3f} n={res['n']} {res['start']}->{res['end']}\n")
        f.write("gates: a_sr " + ("PASS" if res['ok']['a_sr'] else "FAIL") +
                " c_halves " + ("PASS" if res['ok']['c_halves'] else "FAIL") +
                " d_yearly " + ("PASS" if res['ok']['d_yearly'] else "FAIL") +
                " e_scramble " + ("PASS" if res['ok']['e_scramble'] else "FAIL") +
                " f_corr " + ("PASS" if res['ok']['f_corr'] else "FAIL") + "\n")
        f.write(extra_meta + "\n")
    print(f"    saved sleeves/{name}.csv (+meta)")


# ------------------------------------------------------------------ main sweep

PAIRS = [("USCI", "DBC", "front-month basket vs broad basket (roll-profile spread)"),
         ("DBE", "DBP", "energy basket vs precious-metals basket (sector RV spread)")]


def main():
    results = {}
    print('=== (b) SPREAD MOMENTUM: USCI-vs-DBC + DBE-vs-DBP (L/S and long-only) ===')
    for a, b, why in PAIRS:
        px = px_frame([a, b])
        R = px.pct_change()
        print(f"\n--- {a} vs {b}: {why} | common span "
              f"{max(px[a].first_valid_index(), px[b].first_valid_index()).date()} -> "
              f"{px[a].index[-1].date()} (inception-limited, disclosed) ---")
        for lo in (False, True):
            tag = "LO" if lo else "LS"
            for win in [21, 63, 126, 252]:
                net, We, _, W = run_spread_momentum(px, R, a=a, b=b, win=win, long_only=lo)
                nm = f'sprd {a[:3]}-{b[:3]} {tag} {win}d'
                results[nm] = H.evaluate(nm, net, We, R)
                results[nm]['_net'], results[nm]['_We'] = net, We

    print('\n=== SUMMARY (best by SR) ===')
    rows = [(k, v.get('sr'), v.get('pass')) for k, v in results.items()
            if v and np.isfinite(v.get('sr', np.nan))]
    for k, sr, ps in sorted(rows, key=lambda x: -(x[1] if x[1] == x[1] else -9)):
        print(f"  {k:<26} SR={sr:6.2f}  PASS={ps}")
    return results


if __name__ == '__main__':
    main()
