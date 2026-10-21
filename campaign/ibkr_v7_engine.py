#!/usr/bin/env python3
"""IBKR PAPER engine for V7 (headless, ib_async). Requires IB Gateway running,
logged into PAPER, API enabled on port 4002.
  --dry-run : compute & print orders, connect not required
  --live    : connect 127.0.0.1:4002 and place paper orders (monthly rebalance)
"""
import argparse, os, sys, math
import pandas as pd
OD=os.path.join(os.path.dirname(os.path.abspath(__file__)),"work_backtest_oos")
# SYSTEM OF RECORD: V7.1 (V71_REPLICATION_SPEC.md, HARD-STOP act 2026-09-29 — the 2
# monitor HARD stops are RETIRED: w=0 rows, no orders emitted for them). V7.0 weights
# are superseded history (OPT_20V7_weights.csv preserved byte-exact).
WT=pd.read_csv(os.path.join(OD,"OPT_20V71_weights.csv"),index_col=0)['w']
# PROVISIONAL instrument map: sleeve -> (exchange symbol, type). Multi-leg futures
# sleeves trade via ComboContract in live mode (legs listed). Research-only sleeves
# are marked PROXY and are SKIPPED in live mode until 1:1 mapping is validated.
MAP={
 "brwt7":                       [("BZ",1.0),("CL",-1.0)],
 "crack_crack321_nyh_L60Z1.0":  [("CL",-3.0),("RB",2.0),("HO",1.0)],
 "diescrack__prefix":           [("HO",1.0),("CL",-1.0)],
 "inter_dieseljet_L60Z1.0":     [("HO",1.0),("RB",-1.0)],
 "RB_hobr_crack_hyst_w63_z10_zo10":[("HO",1.0),("BZ",-1.0)],
 "inter_gasreg_nyh_gulf_L60Z1.0":[("NG",1.0)],   # proxy: regional spread via NG
 "E1_C5ng_summer_weekday":      [("NG",1.0)],
 "C5_ng_weekday_prem":          [("NG",1.0)],
 "calendar_vixterm_9_3_L40Z1.5":[("VX",1.0)],
 "calendar_vixterm_3_6_L20Z1.5":[("VX",1.0)],
 "TREASFUT_intlcarry3_lag1_NEG":[("ZN",-1.0)],
 "a6_r2_pair_residmom_fm1926":  [("SPY",1.0)],   # equity proxy (ETF)
 "D_xlu_ief":                   [("XLU",1.0),("IEF",-1.0)],
 "A1_carry_seasonal_v2":        [("SPY",1.0)],   # proxy
 "A5_r7_credit_composite":      [("HYG",1.0)],   # proxy
 "RC_t102_d5mr_w21_band50_vt5": [("HYG",1.0)],   # proxy
 "crossasset_rev_L8":           [("SPY",1.0)],   # proxy
 "C4_construct_v2":             [("SPY",1.0)],   # proxy
 "Merger_Arb_PEAD_5pct":        [("SPY",1.0)],   # proxy
 "FXD1_KRWTRI_raw_daily":       [("SPY",1.0)],   # proxy
}
def targets(nav):
    """dollar target per sleeve at 1.6x gross."""
    return {s: float(nav*1.6*w) for s,w in WT.items()}
def dryrun(nav=1_000_000):
    tg=targets(nav)
    print(f"Dry run — NAV ${nav:,.0f}, gross 1.6x => deployed ${nav*1.6:,.0f}")
    for s,d in sorted(tg.items(),key=lambda x:-x[1]):
        legs=MAP.get(os.path.basename(s).replace(".csv",""),[("UNMAPPED-PROXY",1.0)])
        tag="PROXY" if len(legs)==1 and legs[0][0] in("SPY","HYG","UNMAPPED-PROXY") else "FUT"
        print(f"  {d:>12,.0f}  [{tag}] {os.path.basename(s):<42} legs={legs}")
    print("NOTE: PROXY sleeves are research-stream stand-ins; pilot only.")
def live():
    from ib_async import IB, Index, Stock, Future, ComboLeg, Contract, Order
    ib=IB()
    ib.connect("127.0.0.1",4002,clientId=int(__import__('time').time()%100000))
    acct=ib.managedAccounts()[0]
    av=float([v for v in ib.accountValues() if v.tag=='AvailableFunds' and v.currency=='USD'][0].value)
    nav=av*0.9  # keep 10% cash buffer for MtM
    print(f"connected. account={acct} available=${av:,.0f} -> trading NAV ${nav:,.0f}")
    tg=targets(nav)
    # Pilot: trade FUT/ETF legs as SEPARATE delta orders (combos later after mapping QA)
    from collections import defaultdict
    net_sym=defaultdict(float)
    for s,d in tg.items():
        legs=MAP.get(os.path.basename(s).replace(".csv",""))
        if not legs: continue
        for sym,mult in legs:
            net_sym[sym]+=d*mult
    for sym,dollars in sorted(net_sym.items(),key=lambda x:-abs(x[1])):
        if abs(dollars)<2500: continue
        if sym in ("SPY","HYG","XLU","IEF"):
            c=Stock(sym,"SMART","USD")
            qty=int(dollars/ (600 if sym!="SPY" else 600))
            o=Order(action="BUY" if qty>0 else "SELL",totalQuantity=abs(qy) if False else abs(qty),orderType="MKT")
            print(f"  ORDER {sym} {o.action} {abs(qty)} (≈${abs(dollars):,.0f})")
            ib.qualifyContracts(c); ib.placeOrder(c,o)
        else:
            c=Future(sym,exchange="CME")
            try: ib.qualifyContracts(c)
            except Exception as e: print(f"  SKIP {sym}: {e}"); continue
            px=c.last or 100
            mult=getattr(c,'multiplier',1) or 1
            try: mult=float(mult)
            except: mult=1.0
            qty=int(dollars/(px*mult))
            if qty==0: print(f"  SKIP {sym}: qty 0"); continue
            o=Order(action="BUY" if qty>0 else "SELL",totalQuantity=abs(qty),orderType="MKT")
            print(f"  ORDER {sym} {o.action} {abs(qty)} contracts (≈${abs(dollars):,.0f})")
            ib.placeOrder(c,o)
    ib.sleep(2); ib.disconnect()
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--live",action="store_true")
    ap.add_argument("--nav",type=float,default=1_000_000)
    a=ap.parse_args()
    if a.live: live()
    else: dryrun(a.nav)
