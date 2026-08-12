"""Trigger the deep-panel pipeline the moment Twelve Data's quota opens.

Each loop pass: probe Twelve Data (1 call).  If still 429 -> report and
exit (idle).  If OK -> run in sequence:
  1. fetch_long_history.py     (84 tickers x ~4y, background-able)
  2. run_deep_retune.py twelvedata-dir   (champion + capacity grid on ~4y)
  3. summarize results to the research log

Run:  python -m tools.quant.ls.run_when_data_lands [--probe-only]
"""
from __future__ import annotations
import os, sys, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.wt import sources

TWELVE_DIR = os.path.join(ROOT, "tools", "quant", "data", "twelvedata")


def main() -> int:
    h, err = sources.twelvedata_history("AAPL", days=2000)
    if not h:
        print(f"TWELVE still blocked: {err} -- idle")
        return 0
    print(f"TWELVE QUOTA OPEN: {len(h['close'])} AAPL bars "
          f"({h['date'][0]}..{h['date'][-1]})")
    if "--probe-only" in sys.argv:
        return 0

    # 1. fetch the long panel
    print("\n=== fetch_long_history ===")
    subprocess.run([sys.executable, "-m", "tools.quant.ls.fetch_long_history"],
                   cwd=ROOT, check=False)

    # 2. champion + retune on the deep panel
    print("\n=== run_deep_retune (twelvedata) ===")
    subprocess.run([sys.executable, "-m", "tools.quant.ls.run_deep_retune",
                    "tools/quant/data/twelvedata"],
                   cwd=ROOT, check=False)
    print("\nPipeline complete. Check results/deep_retune/compare_deep_retune.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
