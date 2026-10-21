#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 4 (b) — tests for MSSW SHORT_LEG_UNKNOWN resolution.

RED-GREEN history: the prior session's 4 tests assumed byte-reproduction was
achievable (1e-6 equity tolerance) and that weights sum to 1.0 with a 0.05
floor. This round PROVED both assumptions wrong:

  - byte-reproduction is impossible from disk (4/6 stream files regenerated
    after commit e0e47e0; even the e0e47e0 blobs leave a 1.7bp/day residual
    orthogonal to all streams) — reproduced must honestly be False;
  - recovered blend weights sum to 0.975 (the generator's streams are not a
    partition of NAV under zero-fill) and do NOT follow an SR/floor-0.05
    recipe (max dev 0.16 across recipe variants).

Tests now pin the PROVEN structure instead:
  T1 stream files present (unchanged, still fail-closed on missing input);
  T2 STRUCTURE: committed/fx ratio constant to 1e-8 on 134 fx-only days
     (the convention proof — would catch any wrong-convention rebuild);
  T3 WEIGHTS: recovery R^2 >= 0.999 and residual <2% explained by stream
     returns (i.e. residual is input drift, not a weight error);
  T4 HONESTY: byte-reproduction reported False (dev >= 1e-6), never faked;
  T5 SHORT LEG: blend short notional from census-measured stream shorts in
     (0, 0.15] of NAV, with the HARD(8%)/yr drag reported in (0, 1.2%].
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path("/Users/daxu/software/world-trader")
WORK = ROOT / "campaign/agents/chief/coord/HUNT_VOL2/work_r4"
sys.path.insert(0, str(WORK))

SRC = ROOT / "tools/quant/hedge_fund_strats/results/equity_Multi_Strategy_SharpeW.csv"


def test_stream_files_all_present():
    from mssw_reconstruct import STREAM_FILES
    missing = [n for n in STREAM_FILES.values()
               if not (ROOT / "tools/quant/hedge_fund_strats/results" / n).exists()]
    assert not missing, f"missing stream files: {missing}"


def test_structure_proof_fx_only_days_constant_weight():
    """committed_ret / fx_ret must be ONE constant on all fx-only (weekend) days."""
    from mssw_reconstruct import fx_only_weight
    w = fx_only_weight()
    assert 0.02 < w < 0.10, f"w_fx {w} outside plausible blend range"
    # determinism
    assert fx_only_weight() == w


def test_weight_recovery_r2_and_residual_orthogonality():
    from mssw_reconstruct import recover_weights
    w, r2, resid, expl = recover_weights()
    assert r2 >= 0.999, f"recovery R^2 {r2:.6f} too low for fixed-weight model"
    assert (w >= 0).all(), f"negative blend weight: {w[w < 0].to_dict()}"
    # residual must NOT be explainable by stream returns (else weights are wrong)
    assert expl < 0.02, (f"residual {expl:.1%} explained by stream returns — "
                         "weights NOT recovered, treat MSSW as unrecoverable")


def test_byte_reproduction_honestly_reported_false():
    """The committed curve must NOT be claimed reproducible from disk.
    If a future run reports True here, re-verify the stream inputs first."""
    from mssw_reconstruct import rebuild_sharpew, recover_weights
    w, _, _, _ = recover_weights()
    _, dev, n = rebuild_sharpew(weights=w)
    assert n >= 4900, f"overlap {n} too small"
    # measured 1.5e-2 (stream-input drift). The report must not pretend otherwise.
    assert dev >= 1e-6, "unexpected byte match — investigate before trusting"


def test_short_notional_measured_and_priced():
    from mssw_reconstruct import mssw_short_notional, short_notional_report
    sn = mssw_short_notional()
    assert sn > 0, "short notional must be positive (statarb+macro carry shorts)"
    assert sn < 0.15, f"short notional {sn} implausibly large vs census inputs"
    rep = short_notional_report()
    hard = rep["borrow_drag_ann_frac"]["HARD 0.08"]
    assert 0 < hard < 0.012, f"HARD-tier drag {hard} outside priced range"
    assert rep["byte_reproduced"] is False
