"""pull_rates.py — CN+US treasury yields (bond_zh_us_rate, 1990+) + policy rates.
Run: python3 pull_rates.py"""
import sys, os, time, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import akshare as ak
from fetch_all import save_series, retry, SLEEP, ROOT

warnings.filterwarnings("ignore")
os.makedirs(os.path.join(ROOT, "rates"), exist_ok=True)
rows, log = [], []

def add(row, msg):
    print(msg); log.append(msg)
    if row: rows.append(row)

df = retry(lambda: ak.bond_zh_us_rate())
CNYIELD = {"中国国债收益率2年": "cn_2y", "中国国债收益率5年": "cn_5y",
           "中国国债收益率10年": "cn_10y", "中国国债收益率30年": "cn_30y"}
for cn, en in CNYIELD.items():
    sub = df[["日期", cn]].rename(columns={"日期": "date", cn: "rate"}).dropna()
    r, m = save_series("rates", en, sub, max_gap=120)
    add(r, m); time.sleep(SLEEP)
USY = {"美国国债收益率2年": "us_2y", "美国国债收益率10年": "us_10y",
       "美国国债收益率30年": "us_30y"}
for cn, en in USY.items():
    sub = df[["日期", cn]].rename(columns={"日期": "date", cn: "rate"}).dropna()
    r, m = save_series("rates", en, sub, max_gap=120)
    add(r, m); time.sleep(SLEEP)

for name, fn in [("usa_policy", ak.macro_bank_usa_interest_rate),
                 ("india_policy", ak.macro_bank_india_interest_rate)]:
    ev = retry(fn)
    sub = ev[["日期", "今值"]].rename(columns={"日期": "date", "今值": "rate"}).dropna()
    # event dates -> daily step series (policy rate is constant between decisions)
    sub["date"] = sub["date"].astype(str)
    r, m = save_series("rates", name, sub, min_span=365, max_gap=180)
    add(r, m); time.sleep(SLEEP)

import csv
with open(os.path.join(ROOT, "rates", "manifest.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["family", "symbol", "start", "end", "rows", "max_gap_days"])
    w.writeheader(); w.writerows(rows)
print("manifest rows:", len(rows))
open(os.path.join(ROOT, "rates", "PULL_LOG.txt"), "w").write("\n".join(log) + "\n")
