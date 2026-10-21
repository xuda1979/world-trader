"""HUNT_VOL2 ROUND 5 — PCR-overlay scan (charter (a), pre-registered grid).

Grid: 6 PCR series x {level, z(expanding), chg5} x {gt, lt} x thresholds x to in
{0.0, 0.5} — all trim-only (gross cap 1.6 binding). ONE pass, no re-tuning after
seeing results: thresholds are fixed a-priori quantile levels of the PIT covariate
(5/6/7/8-digit standard cut points) or fixed z cut points, NOT data-mined optima.

Every variant reports the full delta table + era deltas (contiguous thirds + 5 eras)
+ gates.run(sig=, leak_check=True) on the WINDOW. §8 gates evaluated on the window.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
R5 = ROOT / "campaign/agents/chief/coord/HUNT_VOL2/work_r5"
for p in (str(ROOT / "campaign"), str(R5)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pcr5_lib as L  # noqa: E402

# --- pre-registered grid (BEFORE looking at any P&L) --------------------------
SERIES = ["pcr_total", "pcr_index", "pcr_equity", "pcr_spx", "pcr_etp", "pcr_vix"]
KINDS = ["level", "z", "chg"]
OPS = ["gt", "lt"]
LEVEL_THR = {   # a-priori economic cut points on the ratio itself
    "pcr_total": [0.75, 0.85, 0.95, 1.05],
    "pcr_index": [1.0, 1.2, 1.4],
    "pcr_equity": [0.6, 0.7, 0.8, 0.9],
    "pcr_spx": [1.3, 1.5, 1.7],
    "pcr_etp": [1.0, 1.3, 1.6],
    "pcr_vix": [0.3, 0.4, 0.5],
}
Z_THR = [1.0, 1.5, 2.0]
CHG_THR = [0.05, 0.10, 0.15]     # 5-session change in ratio units
TO_LIST = [0.0, 0.5]
MIN_TRIG = 0.01                  # variants firing <1% of days are degenerate -> skip
MAX_TRIG = 0.60


def variants():
    out = []
    for s in SERIES:
        for k in KINDS:
            if k == "level":
                thrs = LEVEL_THR[s]
            elif k == "z":
                thrs = Z_THR
            else:
                thrs = CHG_THR
            for op in OPS:
                for thr in thrs:
                    for to in TO_LIST:
                        out.append(dict(series=s, kind=k, op=op, thr=thr, to=to))
    return out


def run_variant(v, w, champ_w, champ_full):
    g = L.pcr_gate(w[v["series"]], kind=v["kind"], op=v["op"], thr=v["thr"],
                   to=v["to"], minp=502)
    freq = L.trim_frequency(g, v["to"])
    if not (MIN_TRIG <= freq <= MAX_TRIG):
        return None
    net = L.overlay_net(g, champ_w)
    d = L.delta_stats(net, champ_w)
    # positions actually held (T+1), for gates.run sig= + leak probe
    sig = g.reindex(champ_w.index).fillna(1.0).shift(1).fillna(1.0).values
    res = L.gate_run(net, champ_full, sig=sig)
    # era deltas on the WINDOW (TimesFM single-era kill: report all, gate on spread)
    eras = {}
    for name, (a, b) in L.era_splits(champ_w, n=3).items():
        seg_net = net.loc[a:b]
        seg_ch = champ_w.loc[a:b]
        eras[name] = L.delta_stats(seg_net, seg_ch)
    for name, (a, b) in L.era_splits(champ_w, n=5).items():
        seg_net = net.loc[a:b]
        seg_ch = champ_w.loc[a:b]
        eras[name] = L.delta_stats(seg_net, seg_ch)
    return dict(variant=v, freq=float(freq), d=d, gates=res, eras=eras)


def main():
    champ_full = L.champion()
    rows = []
    for s in SERIES:
        w, champ_w = L.window_frame(s)
        for v in [x for x in variants() if x["series"] == s]:
            try:
                r = run_variant(v, w, champ_w, champ_full)
            except Exception as e:  # noqa: BLE001
                r = dict(variant=v, error=str(e))
            if r:
                rows.append(r)
        print(f"{s}: done ({len(rows)} evaluated so far)", flush=True)

    # tabulate
    recs = []
    for r in rows:
        if "error" in r:
            recs.append(dict(**r["variant"], error=r["error"]))
            continue
        v, d, res = r["variant"], r["d"], r["gates"]
        e3 = {k: val["d_sr"] for k, val in r["eras"].items() if "of3" in k}
        e5 = {k: val["d_sr"] for k, val in r["eras"].items() if "of5" in k}
        recs.append(dict(
            series=v["series"], kind=v["kind"], op=v["op"], thr=v["thr"], to=v["to"],
            freq=round(r["freq"], 4),
            d_ann=round(d["d_ann"] * 100, 3),      # pp
            d_sr=round(d["d_sr"], 4),
            d_mdd=round(d["d_mdd"] * 100, 3),      # pp (mdd is negative; + = shallower)
            d_h1=round(d["d_h1"], 4), d_h2=round(d["d_h2"], 4),
            neg_yrs_net=d["neg_yrs_net"], worst_yr_net=round(d["worst_yr_net"] * 100, 2),
            net_mdd=round(d["net"]["mdd"] * 100, 3),
            net_ann=round(d["net"]["ann"] * 100, 2),
            champ_ann_win=round(d["champ"]["ann"] * 100, 2),
            leak_corr=(res.get("leak") or {}).get("same_period_corr"),
            leak_ok=res.get("leak_ok"),
            scr_p=res.get("scr_p"),
            **{k: round(x, 4) for k, x in {**e3, **e5}.items()},
        ))
    df = pd.DataFrame(recs)
    df.to_csv(R5 / "pcr_overlay_scan.csv", index=False)
    meta = dict(
        n_evaluated=int(df["d_sr"].notna().sum()) if "d_sr" in df else 0,
        n_variants_declared=len(variants()),
        errors=int(df["error"].notna().sum()) if "error" in df.columns else 0,
        window=[L.WIN_LO, L.WIN_HI],
        champ_sha=L.sha256_of(L.CHAMP_CSV)[:16],
        pcr_sha=L.sha256_of(L.PCR_CSV)[:16],
        grid=dict(series=SERIES, kinds=KINDS, ops=OPS, level_thr=LEVEL_THR,
                  z_thr=Z_THR, chg_thr=CHG_THR, to=TO_LIST),
    )
    (R5 / "pcr_overlay_scan.meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(df.sort_values("d_ann", ascending=False).head(15).to_string())
    print("saved", R5 / "pcr_overlay_scan.csv", len(df), "rows")


if __name__ == "__main__":
    main()
