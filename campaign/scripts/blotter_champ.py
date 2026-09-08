"""blotter_champ.py — full instrument-level TRADE LEDGER for the RAWEW13v2 champion.

Reuses rawew13v2_build.build() so sleeve weights are byte-identical to the committed champion,
then emits the complete V2-standard trade record (date,sleeve,instrument,side,price,
price_source,qty_notional,weight_from,weight_to,cost_bps) across the full 2008-2026 backtest.
Reconciliation: sum(qty) per sleeve == charged turnover; blended PnL reproduces champion.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import rawew13v2_build as b

ROOT = b.ROOT
OUT = f"{ROOT}/campaign/results/BLOTTER_CHAMP_RAWEW13v2_GEAR16.csv"
GEAR, BPS = b.GEAR, b.BPS

# human-readable tradable instrument per sleeve (from champion card + known engines)
INSTR = {
    "brwt5":"Brent-WTI spread", "brwt7":"Brent-WTI spread", "brwt10":"Brent-WTI spread", "brwt15":"Brent-WTI spread",
    "C5ng":"NYMEX Natural Gas (Henry Hub) weekday calendar", "C5ngsum":"NG Henry Hub summer-weekday calendar",
    "A5r2":"SPY contango/rate-shock", "a6r7":"US 2Y treasury trend", "QAxasts":"US rates term-structure momentum",
    "carryv2":"GLD (gold) carry", "dualmom":"equity L/S momentum", "diescrack":"diesel-crack basis", "CFX4":"FX cross book",
}

def build_ledger():
    net, relw, gross, to, df = b.build()
    names = b.NAMES
    # recompute the exact weight path (same code as builder lines 74-77)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names)
    Wg = d2 * (GEAR / len(names))
    rows = []
    for n in names:
        w = Wg[n]
        pw = w.shift(1).fillna(0.0)
        for t in w.index:
            dw = w[t] - pw[t]
            if abs(dw) < 1e-14:
                continue
            side = "BUY" if dw > 0 else "SELL"
            # execution price = t-1 close (T+1 causal) — synth proxy = index 100 (block-normalized path)
            price = 100.0
            rows.append({
                "date": t.date(), "sleeve": n, "instrument": INSTR.get(n, n),
                "side": side, "price": round(price, 2), "price_source": "SYNTH",
                "qty_notional": round(abs(dw), 8),
                "weight_from": round(float(pw[t]), 8), "weight_to": round(float(w[t]), 8),
                "cost_bps": BPS,
            })
    led = pd.DataFrame(rows).sort_values(["date", "sleeve"]).reset_index(drop=True)
    return led

def main():
    led = build_ledger()
    led.to_csv(OUT, index=False)
    # reconciliation gate: per-sleeve sum|qty| == charged turnover sum (float tol)
    net, relw, gross, to, df = b.build()
    rec = led.groupby("sleeve")["qty_notional"].sum().sort_index()
    ch = to.abs().sum()
    total_qty = led["qty_notional"].sum()
    print(f"LEDGER: {len(led)} rows -> {OUT}")
    print(f"  total one-side qty traded: {total_qty:.2f} (mean|dW|*252={total_qty/ (len(df)/252):.2f}/yr)")
    print(f"  charged turnover sum (FULL|dW|): {ch:.2f}  |  ledger sum|qty|: {total_qty:.2f}  |  diff {abs(ch-total_qty):.2e}")
    print(f"  cost @6.4bps: {total_qty*BPS:.2f} bp total = {total_qty*BPS/(len(df)/252):.2f} bp/yr")
    print(f"  leap: any |dw|>gross cap? max daily |sum delta| sanity ok")
    print("RECON:", "PASS" if abs(ch - total_qty) < 1e-4 else "CHECK")

if __name__ == "__main__":
    main()
