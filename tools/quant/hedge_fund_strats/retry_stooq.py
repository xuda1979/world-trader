"""Loop-fire routine: check Stooq/Yahoo; if unblocked, fetch futures/ETF
proxies and re-run the CTA test with the expanded universe.

Run by the /loop cron each fire:
    python tools/quant/hedge_fund_strats/retry_stooq.py

If Stooq responds: downloads the 21-futures universe (fetch_stooq.py),
re-runs strat_cta_futures (which prefers Stooq data over the FRED panel),
and reports the before/after CTA Sharpe.
If Yahoo responds: downloads GLD/SLV/DBC/USO ETF proxies (fills the
metals gap for the 2000+ CTA window test).
Otherwise: prints blocked status.
"""

import sys
import time
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check_stooq() -> bool:
    """Three states: BLOCKED (timeout), GATED (PoW challenge served —
    IP unblocked but data gated), DATA (CSV returned)."""
    import urllib.request
    try:
        r = urllib.request.urlopen(
            urllib.request.Request("https://stooq.com/q/d/l/?s=es.f&i=d",
                                   headers={"User-Agent": "Mozilla/5.0"}),
            timeout=12)
        body = r.read(200).decode(errors="ignore")
        if "Date,Open" in body:
            return "DATA"
        if "challenge" in body.lower() or "javascript" in body.lower():
            return "GATED"
        return "UNKNOWN"
    except Exception:
        return "BLOCKED"


def check_yahoo() -> bool:
    try:
        import yfinance as yf
        import warnings
        warnings.filterwarnings("ignore")
        df = yf.download("GLD", start="2025-01-01", progress=False, auto_adjust=False)
        return len(df) > 0
    except Exception:
        return False


def main():
    stooq_state = check_stooq()
    print(f"Stooq: {stooq_state}", flush=True)
    if stooq_state == "DATA":
        print("  Fetching 21 futures...", flush=True)
        r = subprocess.run([sys.executable, str(HERE / "fetch_stooq.py"),
                            "es.f", "nq.f", "ym.f", "cl.f", "gc.f", "si.f",
                            "hg.f", "ng.f", "rb.f", "ho.f", "zb.f", "zn.f",
                            "zf.f", "6e.f", "6j.f", "6b.f", "6c.f", "6a.f",
                            "zc.f", "zs.f", "zw.f", "--out", str(HERE / "data_stooq")],
                           capture_output=True, text=True, timeout=600)
        print(r.stdout[-1500:])
        print("  Re-running CTA futures test...", flush=True)
        r2 = subprocess.run([sys.executable, str(HERE / "strat_cta_futures.py")],
                            capture_output=True, text=True, timeout=600)
        for line in r2.stdout.splitlines():
            if "Sharpe" in line or "Panel" in line:
                print(f"  {line.strip()}", flush=True)

    yahoo_ok = check_yahoo()
    print(f"Yahoo: {'UNBLOCKED' if yahoo_ok else 'blocked'}", flush=True)
    if yahoo_ok:
        import os
        import warnings
        import yfinance as yf
        warnings.filterwarnings("ignore")
        out = HERE / "data_yahoo"
        out.mkdir(exist_ok=True)
        for sym in ["GLD", "SLV", "DBC", "USO"]:
            try:
                df = yf.download(sym, start="2004-01-01", progress=False, auto_adjust=False)
                if len(df) > 100:
                    df["Close"].to_csv(out / f"{sym}.csv", header=["close"])
                    print(f"  {sym}: {len(df)} rows", flush=True)
            except Exception as e:
                print(f"  {sym}: {e}", flush=True)
            time.sleep(3)

    if not stooq_ok and not yahoo_ok:
        print("Both data sources still blocked; nothing to do.")


if __name__ == "__main__":
    main()
