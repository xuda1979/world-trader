"""RES_CALENDAR r1 TDD — pins the round-1 verdict numbers (REJECT-with-numbers).

Contract per team/charters/RES_CALENDAR.md + GATES_CONTRACT_V2:
  * gates.run is FAIL-CLOSED: sig-less calls must report leak_ok=False + pass=False.
  * The rebuilt FOMC calendar (Fed pages, direct HTTP) must match the public 2008-2025
    announcement-day calendar exactly (8/yr; 2020 has 2 unscheduled extras = 10).
  * The corrupt on-disk fomc_dates.csv must NOT validate: 2021-2024 announcement days
    have ZERO overlap with the real calendar (data-lint evidence, fail-closed use).
  * The best-of-round composite (FOMC day-after basket short + UNG short-Thursday) must
    be honestly SUB-GATE: SR<1.0, neg_years>2 -> pass=False (verdict pin).
Run: python3 -m pytest campaign/team/agents/RES_CALENDAR/tests_r1.py -q
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")

from bt.engine import (lag_signal, vol_target_scale, cost_turnover, borrow_cost,  # noqa: E402
                       margin_cost, cap_leverage)
from bt.gates import run as gates_run  # noqa: E402

ANN_PATH = f"{ROOT}/campaign/team/agents/RES_CALENDAR/work/fomc_ann_final.json"
PANEL = "/tmp/etf_panel.csv"


def _etf_panel():
    rets = {}
    d = f"{ROOT}/tools/quant/data/more_etf"
    for f in sorted(os.listdir(d)):
        if not f.endswith(".csv") or f == "manifest.csv":
            continue
        df = pd.read_csv(f"{d}/{f}", index_col=0, parse_dates=True)
        s = pd.to_numeric(df["close"], errors="coerce").dropna()
        rets[f[:-4]] = np.log(s).diff()
    P = pd.DataFrame(rets).clip(-0.25, 0.25)
    P = P[P.index >= "2008-01-01"]  # champion eval window (all recorded numbers use this)
    return P[[c for c in P.columns if P[c].notna().sum() >= 250]]


def _book(sig, r):
    pos = lag_signal(sig).fillna(0.0)
    scale = vol_target_scale(r).fillna(1.0)
    w = (pos * scale).to_frame("w") if isinstance(pos * scale, pd.Series) else pos * scale
    w = cap_leverage(w, 1.6)
    wc = w["w"]
    net = (wc * r - cost_turnover(w, 6.4) - borrow_cost(w)
           - margin_cost(wc.abs(), 0.045, 1.6)).dropna()
    return net, wc


# --- data-lint: the on-disk schedule file is corrupt (fail-closed evidence) -------------
def test_ondisk_fomc_csv_is_corrupt_2021plus():
    f = pd.read_csv(f"{ROOT}/tools/quant/data/newdata/fomc_dates.csv", dtype=str)
    ann = pd.to_datetime(f["day2"], errors="coerce").dropna().dt.strftime("%Y-%m-%d")
    real = {  # public knowledge: FOMC decision days (day2 of meeting)
        "2021": ["2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16"],
        "2022": ["2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15"],
        "2024": ["2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12"],
    }
    for yr, days in real.items():
        got = set(ann[ann.str.startswith(yr)])
        assert len(got & set(days)) == 0, f"{yr} unexpectedly matches — evidence stale"


def test_rebuilt_calendar_matches_public_knowledge():
    ann = json.load(open(ANN_PATH))
    per = {}
    for d in ann:
        per.setdefault(d[:4], []).append(d)
    for yr in [str(y) for y in range(2009, 2020)] + ["2021", "2022", "2023", "2024", "2025"]:
        assert len(per[yr]) == 8, (yr, per[yr])
    assert "2008-01-30" == ann[0] and len(per["2008"]) == 8
    # 2020: 9 decisions — Mar 17-18 became the special Mar 15 (COVID, Sunday) phone meeting,
    # plus the extra unscheduled Mar 2 meeting whose statement landed 8am Mar 3 (pre-open).
    assert len(per["2020"]) == 9, per["2020"]
    assert "2020-03-03" in per["2020"] and "2020-03-15" in per["2020"]
    assert "2020-03-02" not in per["2020"]


# --- framework fail-closed contract ------------------------------------------------------
def test_gates_fail_closed_without_sig():
    r = pd.Series(np.random.default_rng(1).normal(1e-4, 1e-2, 300),
                  index=pd.bdate_range("2020-01-01", periods=300))
    g = gates_run(r, leak_check=None) if False else gates_run(r)
    assert g["leak_ok"] is False and g["pass"] is False
    assert g["scr_ok"] is False  # NaN scramble p fails closed too


# --- round-1 headline verdict (pinned, reproducible) -------------------------------------
def test_best_composite_is_honestly_subgate():
    ann = sorted(json.load(open(ANN_PATH)))
    champ = pd.read_csv(f"{ROOT}/campaign/results/"
                        "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True)["ret"]
    P = _etf_panel()
    EW = P.mean(axis=1)
    d_str = pd.Series(EW.index.strftime("%Y-%m-%d"), index=EW.index)
    sigA = pd.Series(np.where(d_str.isin(ann), -1.0, 0.0), index=EW.index)
    netA, wA = _book(sigA, EW)
    u = pd.to_numeric(pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/UNG.csv",
                                  index_col=0, parse_dates=True)["close"],
                      errors="coerce").dropna()
    ru = np.log(u).diff()
    ru = ru[ru.index >= "2008-01-01"]
    sigB = pd.Series(np.where(ru.index.dayofweek == 2, -1.0, 0.0), index=ru.index)
    netB, wB = _book(sigB, ru)
    J = netA.index.union(netB.index)
    C = 0.5 * netA.reindex(J).fillna(0) + 0.5 * netB.reindex(J).fillna(0)
    wC = 0.5 * wA.reindex(J).fillna(0) + 0.5 * wB.reindex(J).fillna(0)
    rpu = (C / wC).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    g = gates_run(rpu, ref=champ, sig=wC.reindex(rpu.index).fillna(0).values, scramble_n=200)
    assert round(g["sr"], 3) == 0.592
    assert round(g["h1"], 2) == 0.54 and round(g["h2"], 2) == 0.64
    assert g["neg_years"] == 5 and round(abs(g["worst"]), 3) == 0.022
    assert round(g["corr"], 3) == 0.080          # decorrelated, as chartered
    assert round(g["scr_p"], 3) == 0.015         # real, not noise
    assert g["pass"] is False                    # SR<1.0 + neg_years 5>2 -> REJECT
