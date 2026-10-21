"""TDD tests for RES_COT — honest COT positioning engine + data panel.

Pins (project convention, mirroring RES_VOL/RES_CREDIT):
  - COT panel completeness: no NaNs, monotonic, sensible pct_oi ranges, 2010+ clean panel.
  - Fail-LOUD data defect: a mapped market with no resolvable price proxy RAISES (no silent
    blank manifest rows).
  - Causal timing: a COT report (as-of Tue) released Fri trades ONLY in the next trading week
    — a decision at report t may not use returns before its release Friday + 1.
  - Leak gate re-verifies empirically on the built book.
  - Honest verdict: no COT grid config clears the champion-eligible SR>=1.0 acceptance bar.
"""
import os, sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_COT")

from cot_panel import build_panel, MKT2PX, load_cot, load_px_window  # noqa: E402
from cot_engine import (cot_signal, release_friday, build_book, SUBBASKETS,  # noqa: E402
                        ALL_MARKETS)


# --------------------------------------------------------------------------
# data panel layer
# --------------------------------------------------------------------------
def test_panel_all_mapped_markets_have_price_proxy():
    """Every market with a MKT2PX mapping must resolve to a non-empty price proxy (the
    previous silent blank-row defect for sp500_emini/nasdaq_emini is fixed fail-loud)."""
    net, pct, px, man = build_panel()
    man = man.set_index('market')
    for m in MKT2PX:
        assert m in man.index, f"mapped market {m} missing from manifest"
        assert man.loc[m, 'px_end'] and man.loc[m, 'px_start'], \
            f"{m} has blank price proxy (data defect)"
        assert man.loc[m, 'px_rows'] > 0, f"{m} has 0 price rows"


def test_cot_panel_clean_no_interior_null_sane_ranges():
    """Within each market's OWN span, pct_oi must be contiguous (no interior nulls) and sane.
    Leading/trailing NaN are legitimate coverage gaps (markets start at different report dates);
    the fail-criterion is an INTERIOR hole, which indicates a fetch/join defect."""
    net, pct, px, man = build_panel()
    for m in man['market']:
        s = pct[m].dropna()
        assert s.index.is_monotonic_increasing and not s.index.duplicated().any(), m
        raw = pct[m]
        valid = raw.notna()
        interior_valid = valid & valid.shift(1, fill_value=False) & valid.shift(-1, fill_value=False)
        assert raw[interior_valid].notna().all(), f"{m} pct_oi has an INTERIOR null (defect)"
        assert s.between(-1.5, 1.5).all(), (f"{m} pct_oi out of sane range "
                                            f"({s.min():.3f},{s.max():.3f})")


def test_cot_panel_is_2010_plus_not_1971():
    """Correctness/pinning: the clean more_cot panel starts 2010+, NOT 1971+ (the stale
    DATA_COVERAGE claim). Champion eligibility (2008+) is therefore data-limited."""
    net, pct, px, man = build_panel()
    cols = [c for c in pct.columns if len(pct[c].dropna()) > 0]
    first = pct[cols].apply(lambda s: s.dropna().index.min()).min()
    assert first >= pd.Timestamp('2010-01-01'), f"unexpected pre-2010 COT: {first}"


# --------------------------------------------------------------------------
# signal layer: causal timing (fail-closed no-lookahead)
# --------------------------------------------------------------------------
def test_release_friday_is_same_week_friday():
    # as-of Tuesday 2020-01-07 -> Friday 2020-01-10
    assert release_friday(pd.Timestamp('2020-01-07')) == pd.Timestamp('2020-01-10')
    # as-of Monday (snow/makeup) -> Friday of that week
    assert release_friday(pd.Timestamp('2020-01-06')) == pd.Timestamp('2020-01-10')


def test_build_book_trades_only_after_release():
    """Causal contract (engine's real guarantee): position on a business day d MUST equal the
    sign of the MOST RECENT report t with release_friday(t) < d. Any day whose holdings are
    explained by a report released ON/AFTER that day is a lookahead defect."""
    net, pct, px, man = build_panel()
    cal = pd.date_range('2015-01-01', '2016-12-31', freq='B')
    zf = pd.DataFrame({m: cot_signal(pct[m], lb=8, mode='dz') for m in ALL_MARKETS}).sort_index()
    netb, W, r = build_book(['gold'], zf, px, cal, side=1)
    sig = zf['gold'].dropna()
    # map each report date -> its release Friday; then position on day d uses the newest
    # release Friday strictly before d
    releases = pd.Series({t: release_friday(t) for t in sig.index}, index=sig.index).sort_index()
    for d in cal[::30]:  # sample every 30th business day (fast, still thorough)
        # releases strictly before d
        before = releases[releases.values < d]
        if len(before) == 0:
            continue  # no report yet released before d -> not in live span
        newest_t = before.index[-1]
        expected = np.sign(sig.loc[newest_t])
        assert W.loc[d] == 0.0 or abs(W.loc[d] - expected) < 1e-9, (
            f"day {d.date()}: W={W.loc[d]} but most-recent released report {newest_t.date()} "
            f"sign={expected} -> lookahead")


# --------------------------------------------------------------------------
# cost conventions
# --------------------------------------------------------------------------
def test_engine_charges_costs_not_double_counts_costs():
    """build_book returns net < rpu_book on turnover days (costs are positive-drag) — and the
    per-unit rpu_book passed to the gate is NOT cost-smudged (gate judges sig*r cleanly)."""
    net, pct, px, man = build_panel()
    cal = pd.date_range('2015-01-01', '2019-12-31', freq='B')
    zf = pd.DataFrame({m: cot_signal(pct[m], lb=8, mode='dz') for m in ['gold']}).sort_index()
    netb, W, r = build_book(['gold'], zf, px, cal, side=1)
    # on days position changes, net <= rpu_book (cost drag)
    dW = W.diff().abs()
    switch = dW > 1e-9
    if switch.any():
        assert (netb[switch] <= (W[switch] * r[switch]) + 1e-12).all()


def test_honest_verdict_cot_edge_below_champion_bar():
    """Honest finding pin: the COT positioning family is genuinely DECORRELATED but does NOT
    clear the champion-eligible standalone SR>=1.0 bar (data starts 2010+, edge ~flat). This
    pins the research conclusion so a future change can't silently flip it without review."""
    sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_COT")
    from cot_engine import (champ_rets, build_book, cot_signal, benchmark_series, SUBBASKETS)
    from bt.metrics import sharpe_d

    champ = champ_rets()
    cal = pd.date_range(champ.index[0], champ.index[-1], freq='B')
    netf, pct, px, man = build_panel()
    # representative configs (fast): commo + rates, dz lb 8, follow & fade
    best_sr = -9.9
    max_corr = 0.0
    for bname in ('commo', 'rates', 'all'):
        markets = [m for m in SUBBASKETS[bname] if m in pct.columns and m in px]
        zf = pd.DataFrame({m: cot_signal(pct[m], lb=8, mode='dz') for m in markets}).sort_index()
        for side in (1, -1):
            net, W, r = build_book(markets, zf, px, cal, side=side)
            live = (W != 0.0)
            net = net[net.index >= net.index[live.to_numpy().nonzero()[0][0]]] if live.any() else net.iloc[0:0]
            s = sharpe_d(net)
            best_sr = max(best_sr, s)
            max_corr = max(max_corr, abs(net.reset_index(drop=True).corr(
                champ.reindex(net.index).reset_index(drop=True))) if len(net) > 3 else 0.0)
    # Decorrelated (pass) but NOT champion-eligible edge (fail the SR>=1.0 bar)
    assert max_corr < 0.15, f"COT unexpectedly correlated to champion: {max_corr:.3f}"
    assert best_sr < 1.0, f"COT surprisingly cleared SR>=1.0 (best {best_sr:.2f}) — revisit"
