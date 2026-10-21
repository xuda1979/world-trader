"""HUNT_VXV_TERM overlay composer — exact-cost m-scaling of a champion path (GREEN)."""
import numpy as np
import pandas as pd
from bt.engine import COST_BPS


def overlay_ret(champ_ret: pd.Series, m_exec: pd.Series, gross: float,
                cost_bps: float = COST_BPS) -> pd.Series:
    """ret'_t = r_t * m_exec_t - |m_exec_t - m_exec_{t-1}| * cost_bps/1e4 * gross.
    m_exec must ALREADY be T+1 (caller: bt.engine.lag_signal). Entry (m_{t-1}=NaN->0)
    charged at t=0. gross = champion capital-real gross of the traded notional."""
    m = m_exec.reindex(champ_ret.index).astype(float).fillna(0.0)
    dm = m.diff().abs().fillna(m.iloc[0])
    return champ_ret * m - dm * (cost_bps / 1e4) * gross
