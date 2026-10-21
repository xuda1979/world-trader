"""Fetch free China commodity futures daily OHLC via akshare (futures_zh_daily_sina).
Main-continuous symbols (SYM0) for the universe needed by Turtle + inter-commodity strategies.
Persists each series to data/<SYM0>.csv. Rate-limited with retry.
Run: python3 scratch/fetch_futures.py
"""
import akshare as ak, pandas as pd, time, os
OUT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES/data"
os.makedirs(OUT, exist_ok=True)

# universe for Turtle + inter-commodity (main continuous)
UNIVERSE = {
 "RB0":"螺纹钢","CU0":"铜","NI0":"镍","I0":"铁矿石","M0":"豆粕","Y0":"豆油",
 "P0":"棕榈油","SR0":"白糖","MA0":"甲醇","TA0":"PTA","FU0":"燃料油","SC0":"上海原油",
 "CF0":"棉花","AU0":"黄金","AG0":"白银","RM0":"菜粕","OI0":"菜油","HC0":"热轧卷板",
 "AL0":"铝","ZN0":"锌","PP0":"聚丙烯","PG0":"液化石油气","IF0":"沪深300",
 "IH0":"上证50","IC0":"中证500",
}
def fetch(sym):
    for attempt in range(4):
        try:
            df=ak.futures_zh_daily_sina(symbol=sym)
            if df is not None and len(df)>0:
                df['date']=pd.to_datetime(df['date'])
                df=df.sort_values('date').set_index('date')
                return df[['open','high','low','close','volume','hold','settle']]
        except Exception as e:
            time.sleep(2+attempt*3)
    return None

ok, fail = [], []
for sym,name in UNIVERSE.items():
    df=fetch(sym)
    if df is not None:
        df.to_csv(f"{OUT}/{sym}.csv")
        ok.append((sym,len(df),str(df.index.min().date()),str(df.index.max().date())))
        print(f"  {sym:5s} {name:8s} n={len(df):5d} {df.index.min().date()}..{df.index.max().date()}")
    else:
        fail.append(sym); print(f"  {sym:5s} {name:8s} FAILED")
    time.sleep(1.2)
print("\nOK:", len(ok), "FAIL:", fail)
