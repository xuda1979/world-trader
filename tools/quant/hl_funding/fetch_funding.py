"""Fetch Hyperliquid funding history for a set of coins.

The sandboxed Hyperliquid /info mirror returns up to 500 fundingHistory rows
per coin (1h cadence) ending at a fixed historical cutoff. We pull the
available 500-row window for each coin and cache to CSV.

This is the raw data to VALIDATE (not just scan) the funding-capture edge:
the strategic-thesis "capacity-constrained DeFi structural alpha" (Pillar 1+3).
"""
from __future__ import annotations
import urllib.request, json, time, os, datetime, sys

UA = {"User-Agent": "curl/8", "Content-Type": "application/json"}
API = "https://api.hyperliquid.xyz/info"

def post(body, timeout=20):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=UA, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def fetch_available(coin, start_time=0):
    """Return all available funding rows (num <= 500)."""
    rows = post({'type': 'fundingHistory', 'coin': coin, 'startTime': start_time})
    merged = {r['time']: r['fundingRate'] for r in rows}
    # try to walk further back if the query returns a full 500 window
    guard = 0
    while len(rows) == 500 and guard < 5:
        st = min(r['time'] for r in rows) - 1
        more = post({'type': 'fundingHistory', 'coin': coin, 'startTime': st})
        merged.update({r['time']: r['fundingRate'] for r in more})
        rows = [{'time': t, 'fundingRate': v} for t, v in sorted(merged.items())]
        guard += 1
        time.sleep(0.2)
    return rows

if __name__ == "__main__":
    coins = sys.argv[1:] or ["BTC", "ETH", "SOL", "DOGE", "XRP", "SUI", "ARB",
                             "OP", "AVAX", "LINK", "NEAR", "ADA", "WIF", "AAVE"]
    outdir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(outdir, exist_ok=True)
    for coin in coins:
        path = os.path.join(outdir, f"fund_{coin}.csv")
        if os.path.exists(path):
            print(f"skip {coin} (exists)")
            continue
        try:
            rows = fetch_available(coin)
        except Exception as e:
            print(f"{coin}: ERROR {e}")
            continue
        with open(path, "w") as f:
            f.write("time_ms,fundingRate\n")
            for r in rows:
                f.write(f"{r['time']},{r['fundingRate']}\n")
        if rows:
            d0 = datetime.datetime.fromtimestamp(rows[0]['time']/1000, datetime.UTC)
            d1 = datetime.datetime.fromtimestamp(rows[-1]['time']/1000, datetime.UTC)
            print(f"{coin}: {len(rows)} rows  {d0:%Y-%m-%d} -> {d1:%Y-%m-%d}")
        time.sleep(0.3)
