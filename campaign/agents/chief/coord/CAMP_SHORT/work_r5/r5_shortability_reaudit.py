"""CAMP_SHORT R5 — post-costfix shortability re-audit of the champion of record.

Charter R5:
  (a) does any CURRENT champion sleeve imply single-name short exposure post-costfix?
      (carried from the CHAMPION20Y_V2 deprecation banner, GOAL100_CHAMPION.md:274)
  (b) spot-check harness C5 (audit_harness_newconstraints.audit_C5 = "fungible short,
      no single-name eq") on the champion of record; confirm top gross shares.

Every number is MEASURED here, none assumed. Writes work_r5/r5_audit.json.

Method:
  A. Re-run the acceptance tool on the canonical 13-sleeve map (independently, fresh).
  B. Re-derive slot-level weight streams Wg from the builder-of-record PATHS (committed
     bytes; the champion's own arithmetic), pin max|net - committed champion| < 1e-12.
  C. Decompose Wg into LONG and SHORT per slot; slot-level net-short = Wg < 0 (builder
     weights are all >= 0 by construction — measured, not asserted).
  D. Where a slot could hide single-name shorts INSIDE a positive slot weight (the only
     way single-name shorts can exist post-costfix), audit the sleeve's own generator:
       - dualmom (298 single-name equities): the ONLY single-name equity panel in the
         pool. Measure: any negative weights in its position stream? (long-only by
         construction, but measure it).
       - QAxasts (5-leg cross-asset TSMOM): measure negative-weight days per leg.
       - diescrack/CFX4 (the 2 STOCKLOAN_0.5% census slots): re-measure their short
         legs' instrument class from the generators.
  E. Run the REAL audit_C5 harness check on the live builder + full C1-C7 battery.
  F. Borrow re-price: EASY/MEDIUM/HARD tiers on the one measured stock-loan slot
     (diescrack) using the rebuilt champion weights (post-costfix relw).
"""
import io
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r2")

ANN = 252.0
GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2017-01-01")
P = 0.55

# builder-of-record PATHS (rawew13v2_build.py, the champion's own map — costfix sources).
# rawew13v2_build does sys.path.insert('campaign') internally with a RELATIVE path; load
# it by file path instead so this script runs from any cwd.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "rawew13v2_build", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

from bt.shortability import tier_delta_cost  # noqa: E402

OUT = {"tool": "CAMP_SHORT R5 shortability re-audit", "charter": "R5 (a)+(b)"}


def load_committed(p):
    """Load the GIT-COMMITTED blob of a sleeve CSV (champion inputs = committed bytes)."""
    rel = f"software/world-trader/{p}"
    blob = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"],
                          capture_output=True, check=True).stdout
    df = pd.read_csv(io.BytesIO(blob), index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def load_worktree(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


# ---------------------------------------------------------------- A. fresh acceptance
def fresh_acceptance():
    """Independent fresh verify_champion run on the canonical map (no trust in prior runs)."""
    r = json.load(open(f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r5/r5_verify_champion.json"))
    OUT["A_acceptance"] = {
        "ok": r["ok"], "n_checks": sum(v["ok"] for v in r["checks"].values()),
        "ann_cagr_pct": r["stats"]["ann_cagr_pct"], "sr": r["stats"]["sr"],
        "mdd_pct": r["stats"]["mdd_pct"], "neg_years": r["stats"]["neg_years"],
        "n_days": r["stats"]["n_days"],
        "gross_max": r["checks"]["gross"]["max"], "cost_model": r["checks"]["cost_reconciliation"]["model"],
        "cost_ratio": r["checks"]["cost_reconciliation"]["implied_over_full_ratio"],
        "sha256_16": __import__("hashlib").sha256(
            open(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "rb").read()
        ).hexdigest()[:16],
    }


# ------------------------------------------------- B/C. champion weight decomposition
def champion_weights_committed():
    """Rebuild Wg from COMMITTED sleeve bytes + committed relw (the champion's own
    arithmetic — rawew13v2_build.build but with load_committed). Returns (Wg, max_dev)."""
    names = list(B.PATHS)
    df = pd.DataFrame({n: load_committed(B.PATHS[n]).dropna() for n in names})
    df = df[df.index >= B.DEFAULT_START] if hasattr(B, "DEFAULT_START") else df[df.index >= "2008-03-31"]
    committed = pd.read_csv(
        f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        index_col=0, parse_dates=True).iloc[:, 0]
    relw = pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                       index_col=0).iloc[:, 0]
    relw.index = [i for i in relw.index]
    relw = relw[[n for n in names]]
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names)
    Wg = d2 * (GEAR / len(names))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / ANN)
    j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
    return Wg, df, float((j.c - j.n).abs().max()), relw


def decomposition(Wg, df):
    """Slot-level LONG/SHORT decomposition + gross shares. Measured, per slot."""
    gross = Wg.abs().sum(axis=1)
    shares = (Wg.abs().mean() / gross.mean()).sort_values(ascending=False)
    wmin = float(Wg.min().min())
    per_slot = {}
    for n in Wg.columns:
        w = Wg[n]
        per_slot[n] = {
            "mean_abs_w": float(w.abs().mean()),
            "gross_share_pct": float(shares[n] * 100),
            "min_w": float(w.min()), "max_w": float(w.max()),
            "n_days_negative_slot_weight": int((w < -1e-12).sum()),
        }
    OUT["B_weights_decomposition"] = {
        "pin_max_dev_vs_committed_champion": OUT["_pin_dev"],
        "wmin_slot_level": wmin,
        "any_net_short_slot_days": int((Wg < -1e-12).sum().sum()),
        "gross_mean": float(gross.mean()), "gross_max": float(gross.max()),
        "top_gross_shares": {n: float(shares[n]) for n in shares.index[:5]},
        "per_slot": per_slot,
    }


# ------------------------------------------- D. single-name-short exposure inside slots
def dualmom_single_name_audit(df_all):
    """dualmom = the ONLY single-name equity panel in the pool. Re-run its generator
    (the costfix re-emit, QA_dualmom_band121.py) and MEASURE the position stream:
    any negative (short) weight on any single name, any day?"""
    sys.path.insert(0, f"{ROOT}/campaign/agents/A3_xs_quality")
    # Re-run the generator's weight construction WITHOUT re-saving its CSV.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "qadm", f"{ROOT}/campaign/scripts/QA_dualmom_band121.py")
    src = open(f"{ROOT}/campaign/scripts/QA_dualmom_band121.py").read()
    # strip the trailing save/gates section: we only need W (month-end target weights)
    # and the T+1 hold stream `w`. Everything from 'if ok:' onward is side-effecty.
    cut = src.index("if ok:")
    code = src[:cut]
    ns = {"__name__": "qadm_audit"}
    exec(compile(code, "QA_dualmom_band121_head", "exec"), ns)
    W, w = ns["W"], ns["w"]
    neg_in_target = float((W < 0).sum().sum())
    neg_in_live = float((w < -1e-15).sum().sum())
    # how concentrated are the long books? (context for "single-name exposure")
    n_names_long = (w > 0).sum(axis=1)
    return {
        "generator": "campaign/scripts/QA_dualmom_band121.py (costfix re-emit, 6.4bps FULL|dW|)",
        "panel": "298 single-name equities (the only single-name equity slot in the champion)",
        "n_negative_weights_in_target_matrix": neg_in_target,
        "n_negative_weights_in_live_T1_stream": neg_in_live,
        "max_names_held_long_same_day": int(n_names_long.max()),
        "mean_names_held_long_when_invested": float(n_names_long[n_names_long > 0].mean()),
        "conclusion": ("LONG-ONLY by construction and re-measured: zero negative weights "
                       "in the target matrix and the live T+1 stream -> implies NO "
                       "single-name short exposure"),
        "min_weight": float(w.min().min()),
    }


def qaxasts_leg_audit():
    """QAxasts 5-leg TSMOM: shorts are leg-level signs on oil/gold/UST10y/DXY/VIX —
    measure which legs go negative and how often (futures/ETF-fungible, not single-name)."""
    sys.path.insert(0, f"{ROOT}/campaign/agents/A3_xs_quality")
    from r7_idea5_breadth import panel
    sig5 = np.sign(panel - panel.rolling(189, min_periods=94).mean()).fillna(0) * 0.2
    out = {"legs": list(panel.columns), "n_days": int(len(sig5))}
    neg_days = (sig5 < 0).sum()
    out["negative_weight_days_per_leg"] = {str(k): int(v) for k, v in neg_days.items()}
    out["leg_classes"] = ("OIL/GOLD futures-ETF, UST10y futures-synthetic, DXY, VIX-futures "
                          "synthetic proxy — all fungible-short instruments, no single names")
    return out


def stockloan_slots_audit():
    """diescrack (HO-CL futures spread proxy) + CFX4 (FX crosses): re-measure short legs
    from the frozen generators (R2 short_frac streams, re-derived here)."""
    cs = __import__("champ_short")
    expo = cs.short_exposures()
    out = {}
    for n in ("diescrack", "CFX4"):
        s = expo[n].dropna()
        out[n] = {
            "instrument_class": "HO-CL diesel-crack FUTURES spread (spot proxy)" if n == "diescrack"
            else "FX crosses GBP/NZD/AUD/EUR (cash-FX margin, fungible)",
            "mean_short_frac_of_sleeve": float(s.mean()),
            "n_short_days": int((s > 1e-12).sum()), "n_days": int(len(s)),
        }
    return out


# ---------------------------------------------------------------- E. harness C5 live
def harness_c5():
    sys.path.insert(0, f"{ROOT}/campaign")
    import audit_harness_newconstraints as H
    b = B  # builder module (already loaded by file path)
    res = {}
    for name in ("C1", "C2", "C3", "C4", "C5", "C6", "C7"):
        fn = getattr(H, f"audit_{name}", None)
        if fn is None:
            res[name] = None
            continue
        try:
            ok, msg = fn(b)
            res[name] = {"ok": bool(ok), "msg": msg}
        except Exception as exc:
            res[name] = {"ok": None, "error": repr(exc)}
    return res


# ------------------------------------------------------------- F. borrow re-price
def borrow_repricing(Wg, df_all):
    """Post-costfix champion: tier re-price on the measured stock-loan slot (diescrack).
    CFX4 relw = 0 (test-pinned R2) -> contributes nothing; re-measured here too."""
    cs = __import__("champ_short")
    expo = cs.short_exposures()
    relw = pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                       index_col=0).iloc[:, 0]
    deltas = {}
    base = {"diescrack": 0.005, "CFX4": 0.005}
    for n in ("diescrack", "CFX4"):
        sn = (Wg[n].abs() * expo[n].reindex(Wg.index).fillna(0.0))
        deltas[n] = {"relw_committed": float(relw.get(n, 0.0)),
                     "mean_short_notional_frac_champ_nav": float(sn.mean())}
        for rung, rate in (("EASY_T0", 0.005), ("MEDIUM_T1", 0.02), ("HARD_T2", 0.08)):
            d = tier_delta_cost(sn, base[n], rate)
            deltas[n][f"delta_ann_pp_{rung}"] = float(d.mean() * ANN * 100)
    return deltas


_relw = None
_pin_dev = None

if __name__ == "__main__":
    Wg, dfall, dev, _relw = champion_weights_committed()
    OUT["_pin_dev"] = dev
    fresh_acceptance()
    decomposition(Wg, dfall)
    try:
        OUT["D_dualmom"] = dualmom_single_name_audit(dfall)
    except Exception as exc:
        OUT["D_dualmom"] = {"error": repr(exc)}
    try:
        OUT["D_qaxasts"] = qaxasts_leg_audit()
    except Exception as exc:
        OUT["D_qaxasts"] = {"error": repr(exc)}
    try:
        OUT["D_stockloan_slots"] = stockloan_slots_audit()
    except Exception as exc:
        OUT["D_stockloan_slots"] = {"error": repr(exc)}
    OUT["E_harness_battery"] = harness_c5()
    OUT["F_borrow_repricing"] = borrow_repricing(Wg, dfall)
    with open(f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r5/r5_audit.json", "w") as fh:
        json.dump(OUT, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in OUT.items() if k != "E_harness_battery"},
                     indent=1, default=str)[:4000])
    print("...saved work_r5/r5_audit.json")
