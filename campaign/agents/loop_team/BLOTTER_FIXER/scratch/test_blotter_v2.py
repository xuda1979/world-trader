#!/usr/bin/env python3
"""BLOTTER_FIXER TDD suite — RED first. Asserts the FIXED properties of blotter_v2
per BLOTTER_TESTER FINDINGS #1,#4,#6,#7,#8. Run: pytest -x -q test_blotter_v2.py"""
import sys, os
import numpy as np, pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
FIX = f"{ROOT}/campaign/agents/loop_team/BLOTTER_FIXER/scratch"
BOOKS = {"SAFE": (0.07, 0.04), "AGGRESSIVE": (0.091, 0.03)}

@pytest.fixture(scope="session")
def emis():
    import blotter_v2 as B
    return B.build_all()

def _holiday_set():
    from pandas.tseries.holiday import USFederalHolidayCalendar
    cal = USFederalHolidayCalendar()
    return set(cal.holidays(start='2006-01-01', end='2026-12-31').date)

# ---------- #1 CRITICAL: per-book ledgers, complete cost record ----------
def test_t1_perbook_files_exist(emis):
    for bk in BOOKS:
        p = f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_{bk}.csv"
        assert os.path.exists(p), f"missing per-book ledger {p}"

def test_t1_book_column_and_values(emis):
    for bk in BOOKS:
        led = emis.ledgers[bk]
        assert 'book' in led.columns
        assert (led.book == bk).all()

def test_t1_reb_reconciles_per_book_per_sleeve(emis):
    """per-sleeve trade-row sum|qty| == that book's own position-path |diff| turnover."""
    for bk, (tgt, thr) in BOOKS.items():
        led = emis.ledgers[bk]
        tr = led[led.cost_stream == 'trade']
        lt = tr.groupby('sleeve').qty_notional.sum()
        pt = emis.reb_abs_sleeve[bk]
        m = pd.concat([lt.rename('led'), pt.rename('pos')], axis=1).fillna(0.0)
        d = (m.led - m.pos).abs()
        assert (d <= 1e-8 + 1e-8 * m.pos).all(), f"{bk}: max abs gap {d.max():.3e}"

def test_t1_balanced_equals_pairwise_avg(emis):
    a = emis.ledgers['SAFE'].set_index(['date','sleeve','cost_stream'])
    b = emis.ledgers['AGGRESSIVE'].set_index(['date','sleeve','cost_stream'])
    bal = emis.ledgers['BALANCED'].set_index(['date','sleeve','cost_stream'])
    j = bal.join(a.qty_notional.rename('qa')).join(b.qty_notional.rename('qb'))
    d = (j.qty_notional - (j.qa + j.qb) / 2).abs()
    assert d.max() < 5e-11, f"BAL != (SAFE+AGG)/2, max {d.max():.3e}"

def test_t1_ledger_pnl_reproduces_champion(emis):
    """THE admissibility gate: ledger-alone daily PnL == committed champion to <1e-8."""
    for bk in BOOKS:
        champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{bk}_daily.csv",
                            index_col=0, parse_dates=True).iloc[:, 0]
        lp = emis.ledger_pnl[bk].reindex(champ.index).fillna(0.0)
        d = (lp - champ).abs()
        assert d.max() < 1e-8, f"{bk}: ledger-alone PnL max|diff| {d.max():.3e}"

# ---------- #6 MAJOR: borrow_charge + cost_total; all cost streams recorded ----------
def test_t6_borrow_and_cost_total_columns(emis):
    for bk in BOOKS:
        led = emis.ledgers[bk]
        for c in ('borrow_charge', 'cost_total', 'cost_bps'):
            assert c in led.columns, f"{bk}: missing {c}"
        br = led[led.cost_stream == 'borrow']
        assert len(br) > 0 and (br.qty_notional == 0).all(), "borrow rows are cost-only rows"
        assert (led[led.cost_stream != 'borrow'].borrow_charge.fillna(0) == 0).all()

def test_t6_borrow_totals_match_charged(emis):
    """per-sleeve borrow charge sum == charged htb stream (per book, 1e-10 rel)."""
    for bk in BOOKS:
        led = emis.ledgers[bk]
        lb = led[led.cost_stream == 'borrow'].groupby('sleeve').cost_total.sum()
        cb = emis.htb_sleeve[bk]
        m = pd.concat([lb.rename('led'), cb.rename('chg')], axis=1).fillna(0.0)
        d = (m.led - m.chg).abs()
        assert d.max() < 1e-10 + 1e-10 * m.chg.abs().max(), f"{bk}: borrow gap {d.max():.3e}"

def test_t6_tw_dsc_streams_recorded(emis):
    for bk in BOOKS:
        led = emis.ledgers[emis.BAL_NAME] if False else emis.ledgers[bk]
        for st in ('overlay_vt', 'throttle'):
            s = led[led.cost_stream == st]
            assert len(s) > 0, f"{bk}: no {st} cost rows"
            tot = s.groupby('sleeve').cost_total.sum().sum()
            chg = emis.stream_tot[bk][st]
            assert abs(tot - chg) < 1e-12, f"{bk} {st}: {tot} vs {chg}"

def test_t6_total_cost_ledger_vs_charged(emis):
    for bk in BOOKS:
        led = emis.ledgers[bk]
        led_cost = led.cost_total.sum()
        chg = emis.charged_cost_tot[bk]
        assert abs(led_cost - chg) < 1e-8, f"{bk}: total cost ledger {led_cost:.10f} vs charged {chg:.10f}"

# ---------- #4 MAJOR: honest price maps ----------
def test_t4_carryv2_real_xau(emis):
    led = emis.ledgers['BALANCED']
    c = led[led.sleeve == 'carryv2']
    real = c[c.price_source == 'REAL']
    assert len(real) > 0, "carryv2 has 0 REAL rows — xau.csv map not applied"
    assert (real.price > 400).all() and (real.price < 6000).all(), "xau price out of spot range"

def test_t4_treasury_labels(emis):
    led = emis.ledgers['BALANCED']
    for sl in ('a6r7', 'QAxasts'):
        ins = led[led.sleeve == sl].instrument.iloc[0]
        assert 'YIELD' in ins, f"{sl}: instrument still futures-labeled: {ins}"

def test_t4_brwt_spread_labels(emis):
    led = emis.ledgers['BALANCED']
    ins = led[led.sleeve == 'brwt15'].instrument.iloc[0]
    assert 'SPREAD' in ins and 'Brent' in ins, f"brwt15 label: {ins}"

# ---------- #7 MINOR: exec price = t-1 close ----------
def test_t7_exec_price_is_tminus1(emis):
    led = emis.ledgers['BALANCED']
    px = emis.real_px
    a = led[(led.sleeve == 'A5r2') & (led.price_source == 'REAL')]
    sp = px['spy']
    got = a.date.dt.normalize().map(lambda d: sp.get(d, np.nan))
    got_prev = a.date.dt.normalize().map(lambda d: sp.asof(d - pd.Timedelta(days=1)))
    d = (a.price.values - got_prev.values)
    assert np.nanmax(np.abs(d)) < 1e-6, f"exec px != t-1 close, max {np.nanmax(np.abs(d))}"

def test_t7_turnover_byte_identical_to_v1_on_aggr_rows():
    """#7 constraint: price-reference change must NOT move qty/weights/charged cost.
    AGG book trade rows re-derived qty must equal the v1 delivered CSV per (date,sleeve)."""
    led = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_AGGRESSIVE.csv",
                      parse_dates=['date'])
    led = led[led.cost_stream == 'trade']
    v1 = pd.read_csv(f"{FIX}/V1_BLOTTER_HONEST14V3_BALANCED.backup.csv", parse_dates=['date'])
    k1 = led.set_index(['date', 'sleeve']).qty_notional
    kv = v1.set_index(['date', 'sleeve']).qty_notional
    j = pd.concat([k1.rename('v2'), kv.rename('v1')], axis=1, join='inner')
    assert len(j) == 61194, f"row-coverage of v1 changed: {len(j)}"
    assert (j.v2 - j.v1).abs().max() < 1e-12, "qty changed vs v1 on AGG book"

# ---------- #8 MINOR: holiday_trade flag ----------
def test_t8_holiday_flag(emis):
    led = emis.ledgers['BALANCED']
    hol = _holiday_set()
    flag = led.date.dt.date.isin(hol).astype(int)
    assert 'holiday_trade' in led.columns
    assert (led.holiday_trade.values == flag.values).all()
    # v1 census: 140 TRADE records on 96 distinct US federal holidays (BLOTTER_TESTER #8)
    tr = led[led.cost_stream == 'trade']
    n_hol = int((tr.date.dt.date.isin(hol)).sum())
    assert n_hol == 140, f"expected 140 holiday trade rows (v1 census), got {n_hol}"
    assert tr[tr.date.dt.date.isin(hol)].date.nunique() == 96

# ---------- hard constraints ----------
def test_hard_champions_untouched():
    import hashlib
    for f, want in [
        ("campaign/scripts/honest13_build.py", "bca89d0ee8e2c699850e951c97eca3c8cc7bb3107ba6dd8bbe0f8562b5143734"),
        ("campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv", "fdbca6552b9a2e9e89cfba13b06eb5b0d61cc196b410d3cae2ba4d6149a907cb"),
        ("campaign/results/GOAL100_HONEST14V3_SAFE_daily.csv", "eb1bb91be4e68bfc2a56c2fd4092611737db76f0e52b357b1d4a29fe8f53c82f"),
        ("campaign/results/GOAL100_HONEST14V3_AGGRESSIVE_daily.csv", "a16c6b7c6dd5727f55bbd7fff678c042a568242304f8196f5ba973add4d5a13b")]:
        h = hashlib.sha256(open(f"{ROOT}/{f}", 'rb').read()).hexdigest()
        assert h == want, f"FROZEN FILE MODIFIED: {f}"

# ---------- gate #6 (Tester FIX PLAN #5): round-trip from the EMITTED FILES alone ----------
def test_gate_roundtrip_from_files():
    for bk in ('SAFE', 'AGGRESSIVE', 'BALANCED'):
        f = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_{bk}.csv", parse_dates=['date'])
        g = f.groupby('date')[['pnl_contrib', 'cost_total']].sum()
        lp = g.pnl_contrib - g.cost_total
        champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{bk}_daily.csv",
                            index_col=0, parse_dates=True).iloc[:, 0]
        d = (lp.reindex(champ.index).fillna(0) - champ).abs()
        assert float(d.max()) < 1e-8, f"{bk} round-trip max {float(d.max()):.3e}"

def test_gate_bal_is_pairwise_mean_from_files():
    s = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_SAFE.csv", parse_dates=['date'])
    a = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_AGGRESSIVE.csv", parse_dates=['date'])
    bal = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv", parse_dates=['date'])
    key = ['date', 'sleeve', 'cost_stream']
    m = bal.set_index(key)[['qty_notional', 'cost_total']].join(
        s.set_index(key)[['qty_notional']].rename(columns={'qty_notional': 'qs'}),
        how='left').join(
        a.set_index(key)[['qty_notional']].rename(columns={'qty_notional': 'qa'}), how='left')
    exp = (m.qs.fillna(0) + m.qa.fillna(0)) / 2
    d = (m.qty_notional - exp).abs()
    assert float(d.max()) < 1e-12, f"BAL not pairwise mean: {float(d.max()):.3e}"
