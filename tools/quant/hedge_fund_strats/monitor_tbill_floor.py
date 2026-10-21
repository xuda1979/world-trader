"""Monitor: floored flagship no-losing-year guarantee (T-bill floor).

The floored flagship (h3+AP 50/50 floored 50% in T-bills) guarantees no losing
year WHILE the T-bill yield stays above the floor. Floor = 3.4%/yr (worst
historical bare-book year was -3.4% in 2022; 0.5*year + 2% >= 0 iff year >= -4%,
needs T-bill >= ~3.4%). Reads the FRED 3-month T-bill series we already fetch
(data_fred/tbill3m.csv), prints health, and exits non-zero if the floor is at
risk so a launcher/scheduler can page.

Usage: python tools/quant/hedge_fund_strats/monitor_tbill_floor.py
Exit: 0 = healthy, 2 = floor breached, 1 = warning buffer.
"""
from pathlib import Path
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
TRILL = HERE / "data_fred" / "tbill3m.csv"
FLOOR = 3.4      # %/yr, the no-losing-year guarantee floor
WARN_BUF = 0.5   # %: start warning when within this buffer above floor

def main() -> int:
    if not TRILL.exists():
        print("MISSING T-bill data:", TRILL, "- cannot verify floor. Treat as WARNING.")
        return 2
    df = pd.read_csv(TRILL)
    latest = df.sort_values("date").iloc[-1]
    val = float(latest["value"]); dt = latest["date"]
    n = len(df)
    # trailing low: min over last 12 months
    last12 = df.sort_values("date").tail(12)["value"].astype(float)
    low12 = float(last12.min())
    print(f"T-bill 3m (FRED): {val:.2f}% as of {dt}  ({n} monthly obs)")
    print(f"12-mo floor check: min = {low12:.2f}% ; guarantee floor = {FLOOR:.2f}%")
    ok_curr = val >= FLOOR
    ok_low = low12 >= FLOOR
    margin = val - FLOOR
    print(f"margin above floor: {margin:+.2f}pp   floor health = {'OK' if ok_curr else 'BREACHED'}")
    if not ok_curr or not ok_low:
        print("!! FLOOR BREACH RISK: no-losing-year guarantee may not hold. Review allocation.")
        return 2
    if margin <= WARN_BUF:
        print(f"WARNING: within {WARN_BUF}pp of floor. Re-check monthly.")
        return 1
    print("Guarantee healthy. Next refresh: FRED DGS3MO monthly.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
