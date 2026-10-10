"""Pins for HUNT_CN_MARGIN + HUNT_CN_HSGT closure (2026-09-22).

Two seams from AUDIT_R7REDO R8 §7b census closed as honest negatives:
eastmoney_margin (13 configs) and em_hsgt (8 configs). V7 untouched.
"""
import csv
import os

import pytest

ROOT = "/Users/daxu/software/world-trader"
HUNT = f"{ROOT}/campaign/agents/HUNT_CN_MARGIN"
DEAD = f"{ROOT}/campaign/results/DEAD_IDEAS.csv"


def _read_csv(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def test_hunt_artifacts_exist():
    for f in ("PRECOMMIT.md", "FINDINGS.md", "honest_gate_cn_margin.py",
              "honest_gate_hsgt.py", "screen_results.csv", "hsgt_screen_results.csv"):
        assert os.path.isfile(os.path.join(HUNT, f)), f"missing {f}"


def test_margin_screen_best_is_sr_below_bar():
    rows = _read_csv(os.path.join(HUNT, "screen_results.csv"))
    hdr = rows[0]
    col = hdr.index("is_sr")
    best = max(float(r[col]) for r in rows[1:])
    assert len(rows) == 14  # header + 13 configs
    assert best == pytest.approx(0.422, abs=0.005)
    assert best < 1.0  # 1.0 adoption bar


def test_hsgt_screen_best_is_sr_and_kill_reasons():
    rows = _read_csv(os.path.join(HUNT, "hsgt_screen_results.csv"))
    hdr = rows[0]
    col = hdr.index("is_sr")
    best = max(float(r[col]) for r in rows[1:])
    assert len(rows) == 9  # header + 8 configs
    assert best == pytest.approx(1.087, abs=0.005)
    # best passes the 1.0 bar nominally but is killed in FINDINGS (2015-episode
    # concentration, H2<0, data death 2024-08-16). Pin the h2 of the best row:
    names = hdr.index("name")
    best_row = max(rows[1:], key=lambda r: float(r[col]))
    assert best_row[names] == "SH1_netz21_d+1"
    h2 = float(best_row[hdr.index("h2")])
    assert h2 < 0  # halves fail -> honest-kill documented


def test_dead_ideas_rows_present():
    rows = _read_csv(DEAD)
    joined = " ".join(r[0] for r in rows)
    assert "China A-share margin-balance sentiment" in joined
    assert "HK Stock Connect northbound" in joined
    # 68 (header+67, HUNT_CN_MARGIN/HSGT closure 2026-09-22) -> 70 (2026-09-30):
    # +2 honest-negative closure rows from HUNT_BINANCE_AXES (Binance USD-M
    # metrics & bookdepth axes, both below the 1.0 fail-closed bar).
    # 70 -> 71 (2026-09-30, F2_DDC): +1 GOAL5DIR action-B closure row (drawdown-
    # control post-processing on V7.1: all 4 pre-registered families REJECT,
    # monotone binding-hurts evidence; campaign/agents/F2_DDC_results/).
    # 71 -> 72 (2026-09-30, K1_KURTOV): +1 GOAL5DIR action-D closure row
    # (inverse-kurtosis overlay on the 20 sleeves: all 3 arms REJECT, DD
    # deepens every arm; campaign/agents/K1_KURTOV_results/).
    # 72 -> 75 (2026-10-08/09, three chief hunts — re-pinned 2026-10-09 by
    # AUDIT_GATE_EVOID which found this pin stale after the closures):
    # +1 HUNT_NG_REGIONAL (regional non-L48 natgas storage cross-section,
    # 18/18 configs dead), +1 HUNT_WX_DEMAND (HDD/CDD weather-demand natgas
    # tilts, 20/20 dead), +1 HUNT_ENSO_AG (ENSO/NAO ag-complex tilts,
    # 14/14 dead). Rows 73/74 gate-e p-value citations carry VOID markers
    # per AUDIT_GATE_EVOID (degenerate return-shuffle; verdicts unaffected).
    assert len(rows) == 75  # header + 74 dead ideas


def test_v7_unaffected_note_in_findings():
    txt = open(os.path.join(HUNT, "FINDINGS.md")).read()
    assert "9/9 PASS" in txt
    assert "UNIMPLEMENTABLE" in txt or "unimplementable" in txt
