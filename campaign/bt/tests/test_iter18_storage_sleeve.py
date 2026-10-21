"""ITER18: the EIA storage-surprise sleeve — the one lead the ledger still marked untested.

Signal: US working gas in underground storage (weekly, Friday-dated) minus its trailing 5-year
same-week-of-year average change = the "storage surprise". Bigger-than-normal builds are
bearish for Henry Hub; smaller/normal draws are bullish. Position = -clip(z(surprise), +-cap),
held until the next weekly figure.

CAUSALITY IS THE WHOLE BALLGAME HERE, hence the tests come first:
  * EIA publishes the week-ending-Friday figure the FOLLOWING THURSDAY, so a value dated week
    t may not earn anything before t + publication lag. A same-week implementation would be a
    leak of exactly the kind audit A1 caught.
  * the sleeve's return on day t must be a function of information available at t-1 only.

These are written before the implementation on purpose: they fail on import until
`iter18_storage_sleeve` exists, and they are the only thing standing between this signal and a
repeat of the same-day-leak that cost the campaign 40.84% -> 39.85%.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import iter18_storage_sleeve as S  # noqa: E402

PUB_LAG = 6  # days: Friday figure -> following Thursday release


def _synth(n_weeks=400, seed=3):
    """Weekly storage with a clean seasonal shape + noise, and a daily price."""
    rng = np.random.default_rng(seed)
    wk = pd.date_range("2010-01-01", periods=n_weeks, freq="W-FRI")
    doy = wk.dayofyear.values
    seasonal = 60.0 * np.sin(2 * np.pi * (doy - 100) / 365.25)          # inject in summer
    level = 2000.0 + np.cumsum(seasonal / 52.0 + rng.normal(0, 12, n_weeks))
    days = pd.date_range(wk[0], wk[-1], freq="B")
    price = pd.Series(3.0 * np.exp(np.cumsum(rng.normal(0, 0.02, len(days)))), index=days)
    return pd.Series(level, index=wk), price


def test_return_on_day_t_uses_no_information_from_t_or_later():
    level, price = _synth()
    base = S.build_sleeve(level, price)
    t = price.index[len(price) // 2]
    shocked = price.copy()
    shocked.loc[shocked.index >= t] *= 1.25          # future prices move a lot
    alt = S.build_sleeve(level, shocked)
    a, b = base.loc[:t].iloc[:-1], alt.loc[:t].iloc[:-1]
    assert float((a - b).abs().max()) < 1e-12, "future prices leaked into past returns"


def test_storage_value_earns_nothing_before_its_publication_date():
    level, price = _synth()
    base = S.build_sleeve(level, price)
    wk = level.index[len(level) // 2]
    shocked = level.copy()
    shocked.loc[wk] += 500.0                          # huge build, known only at wk + lag
    alt = S.build_sleeve(shocked, price)
    cutoff = wk + pd.Timedelta(days=PUB_LAG)
    # exclude the cutoff day itself: the signal may legitimately become available on it, and
    # the sleeve earns day t from the position known at t-1, so t is still unaffected -- but
    # keeping the assertion one day clear of the boundary avoids testing the edge itself.
    a, b = base.loc[:cutoff].iloc[:-1], alt.loc[:cutoff].iloc[:-1]
    assert float((a - b).abs().max()) < 1e-12, "storage value was used before it was published"


def test_sleeve_is_finite_and_covers_the_price_history():
    level, price = _synth()
    r = S.build_sleeve(level, price)
    assert r.index.equals(price.index)
    assert np.isfinite(r.dropna()).all()
    assert r.abs().max() < 0.5, "implausible daily return"


def test_bigger_than_normal_build_is_short():
    """Direction check: a surprise build must produce a SHORT position, a surprise draw LONG."""
    wk = pd.date_range("2010-01-01", periods=200, freq="W-FRI")
    doy = wk.dayofyear.values
    level = pd.Series(2000.0 + np.cumsum(60.0 * np.sin(2 * np.pi * (doy - 100) / 365.25) / 52.0),
                      index=wk)
    shock = level.copy()
    shock.iloc[150] += 400.0                          # unmistakable surprise build
    pos = S.signal(level)
    pos_shock = S.signal(shock)
    assert pos_shock.iloc[150] <= pos.iloc[150], "a surprise BUILD must lower the position"
