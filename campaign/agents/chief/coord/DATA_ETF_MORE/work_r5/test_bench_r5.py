#!/usr/bin/env python3
"""DATA_ETF_MORE round-5 TDD suite — bench pack for the V2 §8 blend battery.

Charter corner (a): extend the ETF overlay bench (spy/ief/cta trio is the minimum)
with 1-2 decorrelated passive benches from keyless sources; PIT lint + byte-stable
manifest. NO signal hunting: nothing here is a sleeve, no gate battery is run on a
candidate signal, and no blend performance claim is computed.

PRE-REGISTERED selection rule (fixed before any candidate measurement, encoded in
test_decorrelation_gate / test_failclosed_rejects_bad_bench):
  candidates a-priori (price-close, keyless-acquired): GLD SLV IAU DBC GSG UUP TIP
    - TIP is included as a control EXPECTED to be rejected (rates beta vs IEF).
  rejected a-priori (not decorrelated by construction, not measured):
    rates/credit (TLT SHY AGG BND LQD HYG EMB JNK BIL), equity beta (EFA EEM VWO
    QQQ DIA SMH IYR VNQ XL* EW* GDX COPX FXI INDA ITB XHB XME XOP KBE KRE),
    thin single-commodity with stale-print zero runs (USO UNG CANE CORN SOYB WEAT
    CPER BNO DBP DBE MOO).
  eligible iff ALL of:
    (i)   lint status in {PASS, PASS_WAIVER} under the R3 fail-closed gates;
    (ii)  span_years >= 8 and fresh end (R4 TimesFM span-gate generalization);
    (iii) corr measurable on >= 1008 common daily obs (4y) vs each trio member;
    (iv)  max(|corr_spy|, |corr_ief|, |corr_cta|) <= 0.5.
  rank eligible by max_corr_trio asc, then span_years desc; greedily take up to 2,
  skipping any with |corr| > 0.7 vs an already-taken bench (no near-duplicates:
  this kills IAU vs GLD and SLV vs GLD pairs). 1 bench is acceptable; 0 = the
  round's deliverable FAILS and is reported with exact numbers.
"""
import hashlib
import sys

import pandas as pd
import pytest

HERE = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/DATA_ETF_MORE/work_r5"
sys.path.insert(0, HERE)

import bench_r5  # noqa: E402

ROOT = "/Users/daxu/software/world-trader"
BENCH_MANIFEST = f"{ROOT}/tools/quant/data/bench_r5/manifest.csv"

# Pins measured 2026-09-08 pre-round (recorded in FINDINGS R5 pre-registration).
# §7c: the trio is PINNED — this suite is the canary that nobody re-fetches it.
TRIO_PINS = {
    "SPY": (f"{ROOT}/tools/quant/data/twelvedata/SPY.csv",
            "d35d72808dcc9fc3ae9f900ad713f64e4adef9836ce60b55f03e8dbbb2b994e5"),
    "IEF": (f"{ROOT}/tools/quant/data/more_etf/IEF.csv",
            "603cb2a56afd5616cc143e883414210e9482b86944ccc35ec755045a5aff515f"),
    "CTA_15vol": (f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv",
                  "d7f3b5cd4616f0f46264c26c76ca874faef92cca2415f7716dcfa27653735700"),
}
CHAMPION_SHA16 = "4358dfab95679b97"  # charter-of-record pin (prefix)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------- T1 trio pins
def test_trio_pins_unchanged():
    for name, (path, want) in TRIO_PINS.items():
        got = sha256(path)
        assert got == want, f"{name} re-fetched/rotated: {got} != pinned {want}"
    assert sha256(bench_r5.CHAMPION_PATH).startswith(CHAMPION_SHA16)


# --------------------------------------------------- T2 selected benches lint
def test_selected_benches_pass_lint_and_span():
    mf = pd.read_csv(BENCH_MANIFEST)
    sel = mf[mf.role == "decorrelated_passive"]
    assert 1 <= len(sel) <= 2, f"charter asks 1-2 benches, got {len(sel)}"
    for _, r in sel.iterrows():
        assert r.status in ("PASS", "PASS_WAIVER"), r.symbol
        assert r.span_years >= 8.0, (r.symbol, r.span_years)
        assert r.rows >= 250 and int(r.dup_dates) == 0
        assert int(r.maxgap_days) <= 10 and int(r.jump_days) == 0


# ------------------------------------------------------ T3 decorrelation rule
def test_decorrelation_gate():
    mf = pd.read_csv(BENCH_MANIFEST)
    sel = mf[mf.role == "decorrelated_passive"]
    for _, r in sel.iterrows():
        for c in ("corr_spy", "corr_ief", "corr_cta", "corr_to_champion"):
            assert pd.notna(r[c]), (r.symbol, c)
        assert r.max_corr_trio <= 0.5, (r.symbol, r.max_corr_trio)
    # mutual decorrelation: no near-duplicate pair
    syms = list(sel.symbol)
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            a = sel[sel.symbol == syms[i]].iloc[0]
            b = sel[sel.symbol == syms[j]].iloc[0]
            pair = bench_r5.pair_corr(a.symbol, b.symbol)
            assert abs(pair) <= 0.7, (syms[i], syms[j], pair)
    # rejections are loud: every measured non-selected candidate carries a reason
    rej = mf[mf.role == "candidate_rejected"]
    assert len(rej) > 0
    for _, r in rej.iterrows():
        assert isinstance(r.note, str) and len(r.note) > 3, r.symbol


# --------------------------------------------------------- T4 byte stability
def test_manifest_byte_stable(tmp_path):
    p1, p2 = tmp_path / "m1.csv", tmp_path / "m2.csv"
    bench_r5.build(out_path=str(p1))
    bench_r5.build(out_path=str(p2))
    b1, b2 = p1.read_bytes(), p2.read_bytes()
    assert b1 == b2, "manifest build is not deterministic"
    committed = open(BENCH_MANIFEST, "rb").read()
    assert b1 == committed, "committed manifest differs from a fresh build"


# ------------------------------------------------------- T5 vintage pinning
def test_trio_disclosure_columns_match_convention():
    """RED-first (R5): trio rows must disclose jump_days under the SAME
    convention as lint_price — price |pct_change|>0.5, ret-curve |diff|>0.5 —
    not raw price deltas (which flagged 3653/1161 'jumps' on SPY/IEF)."""
    import numpy as np
    mf = pd.read_csv(BENCH_MANIFEST)
    trio = mf[mf.role == "trio_pinned"]
    assert len(trio) == 3
    for _, r in trio.iterrows():
        s = bench_r5.load_any(r.path, r.lint_mode)
        if r.lint_mode == "price":
            jr = int((s.pct_change().abs() > 0.5).sum())
        else:
            jr = int((s.diff().abs() > 0.5).sum())
        assert int(r.jump_days) == jr, (r.symbol, r.jump_days, jr)
        zg = int((s.diff() == 0).sum())
        assert int(r.zero_ret_rows) == zg, (r.symbol, r.zero_ret_rows, zg)
        mg = int(s.index.to_series().diff().dt.days.max())
        assert int(r.maxgap_days) == mg, (r.symbol, r.maxgap_days, mg)


def test_manifest_pins_vintage():
    mf = pd.read_csv(BENCH_MANIFEST)
    assert len(mf) == 3 + len(bench_r5.CANDIDATES)  # trio + all measured cands
    for _, r in mf.iterrows():
        assert sha256(r.path)[:16] == r.sha256_16, r.symbol
        assert isinstance(r.fetch_source, str) and r.fetch_source
        assert r.px_convention in ("close_price", "ret_curve")


# ------------------------------------------------------------- T7 fail-closed
def test_failclosed_rejects_bad_bench():
    import numpy as np
    idx = pd.bdate_range("2010-01-04", periods=2000)
    px = pd.DataFrame({"date": idx, "close": 100 + np.arange(2000) * 0.01})
    px.loc[px.index[1000:1040], "date"] = px.loc[px.index[1040], "date"]  # 40d gap
    px = px.drop(px.index[1000:1040])
    st, cls, m = bench_r5.lint_price(px)
    assert st.startswith("FAIL"), st
    measured = bench_r5.measure_candidates(force_frames={"FAKE": px})
    row = measured[measured.symbol == "FAKE"].iloc[0]
    assert row.status.startswith("FAIL")
    sel, _ = bench_r5.select_benches(measured)
    assert "FAKE" not in list(sel.symbol)


# ------------------------------------------------------ T8 consumption smoke
def test_consumption_smoke():
    import numpy as np
    import sys as _s
    # bt is a package under campaign/ — the package PARENT goes on the path
    _s.path.insert(0, f"{ROOT}/campaign")
    from bt.beats_passive import evaluate
    from bt.blend import blend_nets

    mf = pd.read_csv(BENCH_MANIFEST)
    # (a) every manifest input loads clean through one loader convention
    for _, r in mf.iterrows():
        s = bench_r5.load_any(r.path, r.lint_mode)
        assert s.index.is_monotonic_increasing and not s.index.duplicated().any()
        assert (s > 0).all() if r.lint_mode == "price" else np.isfinite(s).all()
    # (b) the pinned trio evaluates through beats_passive on the champion span:
    #     finite per-benchmark SRs. This is a consumption check, NOT a candidate.
    #     Caller contract (HUNT_INTL2_round5.py:219-222): price benches are
    #     pct_change'd BY THE CALLER; the CTA [date,ret] curve passes through.
    #     (Passing price levels would trip the >1e3 curve heuristic and score
    #     level-SRs — finite garbage — which is exactly the vacuous pass this
    #     test originally had; corrected to the production convention.)
    champ = bench_r5.load_champion()
    spy = bench_r5.load_any(TRIO_PINS["SPY"][0], "price").pct_change().dropna()
    ief = bench_r5.load_any(TRIO_PINS["IEF"][0], "price").pct_change().dropna()
    cta = bench_r5.load_any(TRIO_PINS["CTA_15vol"][0], "ret_curve")
    ev = evaluate(champ, spy=spy, ief=ief, cta=cta)
    for name, info in ev["benchmarks"].items():
        assert np.isfinite(info["sr"]), (name, info)
    assert set(ev["benchmarks"]) == {"spy_bh", "sixty_forty", "cta_trend"}
    # (c) blend_nets mechanical compat with a selected bench (no perf claim)
    sel = mf[mf.role == "decorrelated_passive"]
    b = bench_r5.load_any(sel.iloc[0].path, "price")
    common = champ.index.intersection(b.index)
    bl = blend_nets(champ.reindex(common), b.pct_change().reindex(common).dropna(), 0.95)
    assert np.isfinite(bl).all() and bl.index.equals(common)
    with pytest.raises(ValueError):
        blend_nets(champ, b.pct_change().dropna(), 0.95)  # misaligned must raise
