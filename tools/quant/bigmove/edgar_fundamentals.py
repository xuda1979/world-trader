"""Parse SEC EDGAR companyfacts -> point-in-time monthly fundamental
characteristics (GKX-style), FREE data. Uses 'filed' dates so a value is only
known once filed -> no lookahead. Output: long frame (month, ticker, chars)."""
from __future__ import annotations
import os, json, glob
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
FACTS=os.path.join(HERE,"data","edgar_facts")

# us-gaap tag -> characteristic
TAGS={
 "book_equity":"us-gaap:StockholdersEquity",
 "assets":"us-gaap:Assets",
 "net_income":"us-gaap:NetIncomeLoss",
 "revenue":"us-gaap:Revenues",
 "oper_income":"us-gaap:OperatingIncomeLoss",
 "gross_profit":"us-gaap:GrossProfit",
 "cfo":"us-gaap:NetCashProvidedByUsedInOperatingActivities",
 "shares":"dei:EntityCommonStockSharesOutstanding",
 "div_paid":"us-gaap:PaymentsOfDividendsCommonStock",
 "rd":"us-gaap:ResearchAndDevelopmentExpense",
 "capex":"us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
 "lt_debt":"us-gaap:LongTermDebtNoncurrent",
 "cur_assets":"us-gaap:AssetsCurrent",
 "cur_liab":"us-gaap:LiabilitiesCurrent",
 "tax":"us-gaap:IncomeTaxExpenseBenefit",
}

def parse_facts(fp):
    """Return dict tag -> DataFrame(period=filed? both) of quarterly values."""
    try:
        d=json.load(open(fp))
    except Exception:
        return None
    us=d.get("facts",{}).get("us-gaap",{})
    dei=d.get("facts",{}).get("dei",{})
    out={}
    for key,tag in TAGS.items():
        src=us if tag.startswith("us-gaap") else dei
        node=src.get(tag.split(":")[1] if tag.startswith("us-gaap") else tag.split(":")[1])
        if not node: continue
        units=node.get("units",{})
        # find USD units (and pure for ratios)
        vals=None
        for u,vlist in units.items():
            if u in ("USD","USD/shares") or "USD" in u or u=="shares":
                vals=vlist; break
        if vals is None: continue
        rows=[]
        for v in vals:
            period=v.get("end"); filed=v.get("filed")
            if not period: continue
            try:
                val=float(v.get("val"))
            except (TypeError,ValueError):
                continue
            rows.append((pd.Timestamp(period),pd.Timestamp(filed) if filed else pd.Timestamp(period),val))
        if rows:
            df=pd.DataFrame(rows,columns=["period","filed","val"]).drop_duplicates(["period","filed"]).sort_values("filed")
            out[key]=df
    return out if out else None

def build_monthly_chars(close_index, min_filed_lag=45):
    """Per-ticker: for each month-end, most recent filed fact (filed <= month-end)."""
    tickers=[os.path.basename(fp)[:-5] for fp in glob.glob(os.path.join(FACTS,"*.json"))]
    out={}
    for t in tickers:
        facts=parse_facts(os.path.join(FACTS,f"{t}.json"))
        if not facts: continue
        out[t]=facts
    # monthly grid
    idx=pd.to_datetime(close_index)
    mclose_idx=idx.resample("ME").last()
    results={k:{} for k in ["size","bm","roe","gp_a","op_a","inv","acc","mom12","ret_1m","ret_next"]}
    # price panel needed for size & bm; handled by caller - here return facts
    return out

def facts_to_panel(facts_all, month_index):
    """Given per-ticker facts, build (month,ticker) characteristic frame.
    Chars computed from ratios of the most-recent-filed quarterly values."""
    rows=[]
    for t,facts in facts_all.items():
        # asof lookup: for each month, last filed <= month end
        def asof(key, month):
            df=facts.get(key)
            if df is None or len(df)==0: return np.nan
            m=df[df["filed"]<=month]
            if len(m)==0: return np.nan
            # latest by filed then period
            return float(m.sort_values(["filed","period"]).iloc[-1]["val"])
        for m in month_index:
            be=asof("book_equity",m); a=asof("assets",m); ni=asof("net_income",m)
            rev=asof("revenue",m); oi=asof("oper_income",m); gp=asof("gross_profit",m)
            cfo=asof("cfo",m); sh=asof("shares",m)
            rd=asof("rd",m); capex=asof("capex",m); ltd=asof("lt_debt",m)
            ca=asof("cur_assets",m); cl=asof("cur_liab",m); tax=asof("tax",m); dvp=asof("div_paid",m)
            if a is np.nan or a<=0: gp_a=oi_a=acc=np.nan
            else:
                gp_a=gp/a if gp==gp else np.nan
                oi_a=oi/a if oi==oi else np.nan
                acc=(ni-cfo)/a if (ni==ni and cfo==cfo) else np.nan
            rows.append((m,t,be,a,ni,rev,oi,gp,cfo,sh,rd,capex,ltd,ca,cl,tax,dvp,gp_a,oi_a,acc))
    df=pd.DataFrame(rows,columns=["month","ticker","book_equity","assets","net_income","revenue",
        "oper_income","gross_profit","cfo","shares","rd","capex","lt_debt","cur_assets","cur_liab",
        "tax","div_paid","gp_a","op_a","acc"])
    return df

if __name__=="__main__":
    import sys; sys.path.insert(0,HERE)
    from union_panel import load_union
    P=load_union(); c=P["close"]
    print("parsing facts...",flush=True)
    facts_all={}
    for fp in glob.glob(os.path.join(FACTS,"*.json")):
        t=os.path.basename(fp)[:-5]
        f=parse_facts(fp)
        if f: facts_all[t]=f
    print(f"parsed {len(facts_all)} tickers",flush=True)
    idx=c.index.resample("ME").last()
    df=facts_to_panel(facts_all, idx)
    df.to_parquet(os.path.join(HERE,"data","edgar_chars.parquet"))
    print("saved edgar_chars.parquet:", df.shape)
    for k in ["book_equity","assets","net_income"]:
        print(f"  {k}: {int(df[k].notna().sum()):,} non-null")
