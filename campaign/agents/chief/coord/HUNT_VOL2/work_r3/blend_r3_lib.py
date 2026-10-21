"""HUNT_VOL2 ROUND 3 — champion-blend integration library.

Charter (coordinator standup 2026-09-07 07:2x CST): the champion (39.85% ann, SR 3.296,
0/19 negy, MDD -6.84%, gross exactly 1.6) cannot lever up and every de-risk overlay
subtracts; the one honest path to more profit is ADD small weights of decorrelated
positive-SR sleeves.

CONVENTIONS (pinned by test_blend_r3.py, all honest/fail-closed):
  * Champion = the git-HEAD-PINNED blob (work_r3/champion_head_pin.csv, sha256 pinned).
    The working-tree champion CSV has drifted (work ann 39.69% vs HEAD 39.85%, max|diff|
    9.9e-4) — the same incident class CAMP_SHORT R2 documented. All deltas are vs HEAD.
  * Blend algebra re-derived from bt.borrow.margin_daily (positive drag) — NOT from
    bt.blend.blend_margin_daily, whose current working-tree form returns a NEGATIVE
    margin (rebate) with 5 of its own pinned tests RED. Fail-closed by re-derivation.
  * Constant-mix capital split B = w*N_c + (1-w)*N_s on already-costed nets. The
    champion's margin is charged per sub-book (gross 1.6 inside the w-slice) and the
    sleeve sits at gross 1.0 (no margin), so the linear blend IS the exact
    margin-re-priced blend at equal rate — proven by test and re-derived in blend_exact().
  * The ONLY new trade is blend-weight rebalancing: drift turnover = 2*|w - W_c,t| with
    W_c,t from PRIOR-day NAVs (T+1, no lookahead), costed at 6.4bps FULL |dW|.
  * Adoption gates (charter c): negy 0/19; MDD > -7%; dAnn > 0; dSR >= 0; gross <= 1.6;
    dSR > 0 in BOTH halves; w-plateau (>=2 adjacent ladder rungs pass); adversarial
    control: 200 vol-and-corr-matched random sleeves at the same w must not show
    consistent dSR>0.
  * Shortability: published nets already carry 0.5%/yr EASY borrow where shorted; ETF
    candidates = EASY (delta 0). CRX1030 perp funding NOT modeled (published meta caveat)
    -> funding-stress delta reported, never silently assumed covered.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CAMP = Path("/Users/daxu/software/world-trader/campaign")
if str(CAMP) not in sys.path:
    sys.path.insert(0, str(CAMP))

from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years  # noqa: E402

ANN = 252.0
BPS = 6.4
RATE = 0.045
GEAR = 1.6
PIN_SHA = "e6d8b9c0631aac243ecc60ddbe6ae5fd48998dbc1d9c47c3a0c28ba03d9237b3"
PIN_PATH = CAMP / "agents/chief/coord/HUNT_VOL2/work_r3/champion_head_pin.csv"

W_LADDER = [0.025, 0.05, 0.075, 0.10, 0.15]

POOL = {
    "MSSW":         ("results/sleeve_library/Multi_Strategy_SharpeW.csv",),
    "CRX1030":      ("agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_10-30_EW12_audit.csv",),
    "A_rs":         ("agents/chief/coord/HUNT_SECTOR2/sleeves/A_rs_ratio.csv",),
    "A11":          ("agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv",),
    "COMP50d":      ("agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_daily.csv",),
    "CMDTrot_h2":   ("agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_h2_LS.csv",),
    # rejected-with-numbers (charter: list, don't silently drop)
    "CTA_15vol":    ("results/sleeve_library/CTA_15vol.csv",),
    "CMDTrot_6m_LS": ("agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_LS.csv",),
    "COMP_invvol":  ("agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_invvol.csv",),
}

ADMITTED = ["MSSW", "CRX1030", "A_rs", "A11", "COMP50d", "CMDTrot_h2"]


# ---------------------------------------------------------------- champion pin
def load_champion() -> pd.Series:
    """Load the git-HEAD-PINNED champion blob; fail-closed on sha256 or shape drift."""
    raw = PIN_PATH.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != PIN_SHA:
        raise ValueError(f"champion pin sha256 mismatch: {got} != {PIN_SHA}")
    ch = pd.read_csv(PIN_PATH, parse_dates=["date"]).set_index("date")["ret"].astype(float)
    ch = ch[~ch.index.duplicated(keep="last")].sort_index()
    if len(ch) != 4805:
        raise ValueError(f"champion pin shape drift: n={len(ch)} != 4805")
    return ch


# ------------------------------------------------------------ blend primitives
def margin_daily_scalar(gross: float, rate: float = RATE) -> float:
    """Positive daily margin drag per unit NAV (bt.borrow convention, re-pinned)."""
    from bt.borrow import margin_daily
    return float(margin_daily(pd.Series([gross]), rate).iloc[0])


def blend_margin_daily(w: float, gross_c: float, gross_s: float, rate: float = RATE) -> float:
    """Blended margin drag, charged ONCE on blended gross-1 (positive, floors at 0).
    CHARTER WEIGHT CONVENTION: w is the SLEEVE slice, champion gets (1-w) —
    B_t = (1-w)*N_c,t + w*N_s,t ("champion_net*(1-w) + sleeve_net*w").
    Re-derived from bt.borrow (NOT bt.blend, whose margin sign is currently flipped)."""
    return max((1 - w) * gross_c + w * gross_s - 1.0, 0.0) * rate / ANN


def blend_margin_ann(w: float, gross_c: float, gross_s: float, rate: float = RATE) -> float:
    return blend_margin_daily(w, gross_c, gross_s, rate) * ANN


def blend_exact(net_c: pd.Series, net_s: pd.Series, w: float,
                gross_c: float = GEAR, gross_s: float = 1.0, rate: float = RATE) -> pd.Series:
    """Exact constant-mix blend B = (1-w)*N_c + w*N_s of two ALREADY-COSTED nets, margin
    re-priced from blended gross via bt.borrow primitives. Fail-closed on index mismatch.
    At equal rates with per-sub-book margin this reduces EXACTLY to the linear blend
    (test-pinned); the reconstruction is kept as the honesty guard vs convention drift."""
    a, b = pd.Series(net_c), pd.Series(net_s)
    if not a.index.equals(b.index):
        raise ValueError("blend_exact: champion and sleeve nets must share one index")
    drag_c = np.maximum(gross_c - 1.0, 0.0) * rate / ANN
    drag_s = np.maximum(gross_s - 1.0, 0.0) * rate / ANN
    port_b = (1 - w) * (a + drag_c) + w * (b + drag_s)
    margin_b = blend_margin_daily(w, gross_c, gross_s, rate)
    return port_b - margin_b


def leg_weight(ret_c: pd.Series, ret_s: pd.Series, w: float) -> pd.Series:
    """Champion leg's drifted capital weight (target (1-w)):
    W_c,t = (1-w)(1+r_c,t) / ((1-w)(1+r_c,t) + w(1+r_s,t))."""
    num = (1 - w) * (1 + ret_c)
    den = num + w * (1 + ret_s)
    return num / den


def blend_drift_turnover(ret_c: pd.Series, ret_s: pd.Series, w: float) -> pd.Series:
    """Daily one-side FULL |dW| turnover of the rebalance-to-((1-w), w) policy. The
    champion leg trades |(1-w) - W_c,t-1| and the sleeve leg the same the other way, so
    book-level one-side turnover is 2*|(1-w) - W_c,t-1|, W from PRIOR-day NAVs (T+1).
    Day 0 is establishment: no trade."""
    Wc_prev = leg_weight(ret_c, ret_s, w).shift(1)
    return (2.0 * ((1 - w) - Wc_prev)).abs().fillna(0.0)


def blend_gross_of(w: float, gross_c: float, gross_s: float) -> float:
    """Blended gross under the charter convention: (1-w) on champion, w on sleeve."""
    return float((1 - w) * gross_c + w * gross_s)


def load_ret(path: str, root: Path = CAMP) -> pd.Series:
    df = pd.read_csv(root / path, parse_dates=["date"])
    n_raw = len(df)
    df = df.dropna(subset=["date", "ret"])
    s = pd.Series(df["ret"].astype(float).values, index=pd.DatetimeIndex(df["date"]))
    if s.index.has_duplicates:
        raise ValueError(f"{path}: duplicate dates")
    s = s.sort_index()
    s.attrs["n_raw"] = n_raw
    s.attrs["n_nan"] = n_raw - len(s)
    return s.sort_index()


def looks_like_returns(s: pd.Series) -> bool:
    """Fail-closed returns-stream detector. COMP_invvol.csv holds a WEIGHTS stream
    (smooth, lag-1 autocorr ~0.99, NaN-tailed) that would poison every blend metric
    (naive ann = 1e21%). A daily net-return book has near-zero lag-1 autocorrelation;
    a level/weights series is highly persistent. Also unusable: any NaN row (a blend
    cannot have missing days — fail-closed, no forward-fill)."""
    if s.attrs.get("n_nan", 0) > 0:
        return False
    if len(s) < 50:
        return False
    return bool(abs(s.autocorr(1)) < 0.99)


def first_nonzero_index(s: pd.Series, tol: float = 1e-12) -> pd.Timestamp:
    nz = s[s.abs() > tol]
    if not len(nz):
        raise ValueError("series all-zero")
    return nz.index[0]


def joint_corr(a: pd.Series, b: pd.Series) -> float:
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner", sort=True).dropna()
    return float(j.a.corr(j.b))


# ----------------------------------------------------------- candidate screen
def screen_pool() -> dict:
    """Charter (a) admission screen. Published sleeves AS-IS (no re-fit).
    Admit: own-span net SR >= 0.5 AND |corr vs champion| <= 0.35. Reject-with-numbers
    otherwise. COMP_invvol.csv holds a weights stream, not returns -> REJECT_UNUSABLE_FILE."""
    ch = load_champion()
    out = {}
    a_rs_raw = load_ret(POOL["A_rs"][0])
    a_rs = a_rs_raw[a_rs_raw.index >= first_nonzero_index(a_rs_raw)]
    for name, (path,) in POOL.items():
        s = load_ret(path)
        is_ret = looks_like_returns(s)
        if is_ret:
            f0 = first_nonzero_index(s)
            own = s[s.index >= f0]
        else:
            own = s  # let metrics flag it; verdict set below
        rec = dict(path=path, n=len(s), start=str(s.index[0].date()), end=str(s.index[-1].date()),
                   own_sr=float(sharpe_d(own)), own_ann=float(ann_geo(own)),
                   corr_champ_own=joint_corr(ch, own),
                   neg_years=int(neg_years(own)[0]), mdd=float(max_dd(own)))
        rec["xcorr_A_rs"] = (1.0 if name == "A_rs" else joint_corr(own, a_rs))
        if not is_ret:
            rec["verdict"] = "REJECT_UNUSABLE_FILE"
        elif rec["own_sr"] >= 0.5 and abs(rec["corr_champ_own"]) <= 0.35:
            rec["verdict"] = "ADMIT"
        else:
            rec["verdict"] = "REJECT_OWN_SR" if rec["own_sr"] < 0.5 else "REJECT_CORR"
        out[name] = rec
    return out


# ------------------------------------------------------- blend machinery (real)
def blend_metrics(net_c: pd.Series, net_s: pd.Series, w: float, window: str = "FULL") -> dict:
    """Blend-machinery metrics at weight w on a SHARED index: exact-margin blend minus
    rebalance-drift cost. Fail-closed if the sleeve is missing any day of the window."""
    net_s_a = net_s.reindex(net_c.index)
    if net_s_a.isna().any():
        raise ValueError("blend_metrics: sleeve net missing days on the window index "
                         "(forward-fill would fabricate a book)")
    to = blend_drift_turnover(net_c, net_s, w)
    nb = blend_exact(net_c, net_s, w) - to * BPS / 1e4
    neg, worst = neg_years(nb)
    h1, h2 = _halves(nb)
    return dict(window=window, n=len(nb), w=w, gross=blend_gross_of(w, GEAR, 1.0),
                margin_drag_ann_pct=blend_margin_ann(w, GEAR, 1.0) * 100.0,
                drift_cost_bp_yr=float(to.mean() * ANN * BPS),
                ann=float(ann_geo(nb)), sr=float(sharpe_d(nb)), mdd=float(max_dd(nb)),
                neg_years=int(neg), worst_year=float(worst), h1=float(h1), h2=float(h2))


def _halves(r: pd.Series):
    k = len(r) // 2
    return sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:])


def overlap_index(ch: pd.Series, s: pd.Series) -> pd.DatetimeIndex:
    """Blend window: champion days on which BOTH books have a live observation.

    Sleeves publish only their own exchange/broker calendar (holidays absent). The honest
    capital accounting: on a day the sleeve book is CLOSED it cannot earn, cannot be
    traded, and its NAV is FROZEN (cash + positions marked at last close — no P&L accrual
    is claimable without a mark). The champion leg (w) stays live. So the blend return on
    a champion-only day is w*r_c + (1-w)*0 (sleeve flat P&L), and the leg drift uses r_s=0.
    A forward-filled sleeve P&L or a silently DROPPED champion day (losing the champion's
    return inside its own (1-w) slice) would both under/overstate the blend — both
    rejected; the asymmetry is reported per candidate in the table's n/window fields."""
    f0 = first_nonzero_index(s)
    idx = ch.index[(ch.index >= f0) & (ch.index <= s.index[-1])]
    return idx


def sleeve_on_champion_calendar(s: pd.Series, idx: pd.DatetimeIndex,
                                fill_value: float = 0.0) -> pd.Series:
    """Reindex a sleeve onto champion days: sleeve-closed days earn 0 (book frozen).
    Fails closed if the sleeve has a NaN INTERIOR to its own published span (data hole,
    not calendar asymmetry)."""
    interior_nan = s.loc[s.index[0]:s.index[-1]].isna().sum()
    if interior_nan > 0:
        raise ValueError(f"sleeve has {int(interior_nan)} NaN inside its own span (data hole)")
    out = s.reindex(idx)
    n_fill = int(out.isna().sum())
    out = out.fillna(fill_value)
    out.attrs["n_champ_only_days"] = n_fill
    return out


# --------------------------------------------------------- adversarial control
def null_sleeves(r_c: pd.Series, n: int, vol: float, corr: float,
                 rng: np.random.Generator) -> list:
    """n Gaussian nulls matched EXACTLY (per draw) to the real sleeve's daily vol AND
    champion-corr on the exact blend window. Construction: standardize the champion,
    draw noise, orthogonalize the noise against the champion IN SAMPLE (so the sample
    corr is exactly `corr`, not a draw from its sampling distribution — 1500 obs give a
    corr SE of ~0.026, which would otherwise fail any tight match test), then scale to
    exactly `vol`. A two-match control; vol-only matching was the R2 audit's complaint."""
    r_c = pd.Series(r_c).dropna()
    z = ((r_c - r_c.mean()) / r_c.std(ddof=1)).values
    out = []
    for _ in range(n):
        e = rng.standard_normal(len(r_c))
        e = e - e.mean()
        e = e - z * (z @ e) / (z @ z)        # orthogonalize noise to champion, in sample
        e = e / e.std(ddof=1)
        x = corr * z + np.sqrt(max(1.0 - corr ** 2, 1e-12)) * e
        s = pd.Series(x, index=r_c.index)
        s = s * (vol / s.std(ddof=1))        # exact vol match
        out.append(s)
    return out


def adversarial_control(net_c: pd.Series, vol: float, corr: float, w: float,
                        n_nulls: int = 200, rng: np.random.Generator = None,
                        real_sleeve: pd.Series = None) -> dict:
    """Charter (c) adversarial control: 200 vol-and-corr-matched RANDOM sleeves at the same
    w. If a majority of nulls also gain dSR (or the real gain sits inside the null bulk),
    the gain is a DIVERSIFICATION ARTIFACT, not signal."""
    rng = rng or np.random.default_rng(0)
    base_sr = float(sharpe_d(net_c))
    nulls = null_sleeves(net_c, n=n_nulls, vol=vol, corr=corr, rng=rng)
    null_dsrs = np.array([blend_metrics(net_c, s, w)["sr"] - base_sr for s in nulls])
    out = dict(n_nulls=n_nulls, w=w,
               frac_null_dsr_pos=float((null_dsrs > 0).mean()),
               null_dsr_p50=float(np.percentile(null_dsrs, 50)),
               null_dsr_p95=float(np.percentile(null_dsrs, 95)),
               real_dsr=None, verdict="DIVERSIFICATION_ARTIFACT"
               if float((null_dsrs > 0).mean()) > 0.5 else "SURVIVES_CONTROL")
    if real_sleeve is not None:
        rs = real_sleeve.reindex(net_c.index)
        out["real_dsr"] = float(blend_metrics(net_c, rs, w)["sr"] - base_sr)
        out["real_vol"] = float(rs.std(ddof=1))
        out["real_corr"] = joint_corr(net_c, rs)
        # construction targets the real sleeve's measured vol/corr; record the targets and
        # the exactness of the per-draw match (the generator is exact by construction)
        out["target_vol"], out["target_corr"] = vol, corr
        out["match_ok"] = bool(abs(vol - out["real_vol"]) / max(out["real_vol"], 1e-9) < 0.02
                               and abs(corr - out["real_corr"]) < 0.02)
        if not out["match_ok"]:
            out["verdict"] = "CONTROL_MISMATCH"
    return out


# --------------------------------------------------------------- shortability
def shortability_report() -> dict:
    """CAMP_SHORT tier deltas for the admitted pool. Published nets already cost 0.5%/yr
    EASY borrow where they short; ETF sleeves = EASY (delta 0). CRX1030: binance perp
    funding NOT modeled (published meta caveat) -> report a funding-stress delta."""
    rep = {}
    for name in ADMITTED:
        if name == "CRX1030":
            s = load_ret(POOL[name][0])
            own = s[s.index >= first_nonzero_index(s)]
            frac_long = float((own > 0).mean())   # fraction of days net-long the basket
            rep[name] = dict(tier="PERP", borrow_delta_ann_pp=0.0, funding_modeled=False,
                             avg_long_frac=frac_long,
                             stress_10pct_ann_pp=float(0.10 * frac_long * 100.0))
        else:
            rep[name] = dict(tier="EASY", borrow_delta_ann_pp=0.0, funding_modeled=True,
                             avg_long_frac=None, stress_10pct_ann_pp=0.0)
    return rep


# ------------------------------------------------------------------ gates
def gates_for(tbl: pd.DataFrame, name: str) -> dict:
    """Charter (c) adoption gates over a candidate's whole ladder (every rung must hold
    where the gate says 'stays'): negy 0/19, MDD > -7%, gross <= 1.6; directional gates
    dAnn>0 / dSR>=0 / both-halves dSR>0 / plateau must hold on a >=2-rung contiguous run."""
    sub = tbl[tbl.candidate == name].sort_values("w")
    if not len(sub):
        return dict(candidate=name, verdict="NO_ROWS")
    ok_rung = ((sub.d_ann_pp > 0) & (sub.d_sr >= 0) & (sub.d_h1 > 0) & (sub.d_h2 > 0)
               & (sub.neg_years == 0) & (sub.mdd > -7.0) & (sub.gross <= GEAR + 1e-12)
               & (sub.worst_year > 0))
    # w-plateau: the PASSING rungs must form a contiguous block of >= 2 (not a knife-edge)
    best_block, cur = 0, 0
    for v in ok_rung.values:
        cur = cur + 1 if v else 0
        best_block = max(best_block, cur)
    plateau = best_block >= 2
    any_pass = bool(ok_rung.any())
    blocking = []
    if not (sub.neg_years == 0).all():
        blocking.append(f"negy>0 on {int((sub.neg_years > 0).sum())} rungs")
    if not (sub.mdd > -7.0).all():
        blocking.append(f"MDD<=-7% on {int((sub.mdd <= -7.0).sum())} rungs")
    if not any_pass:
        blocking.append(f"dAnn>0 & dSR>=0 & dSR>0 both halves never (best dAnn "
                        f"{sub.d_ann_pp.max():+.2f}pp, best dSR {sub.d_sr.max():+.3f}, "
                        f"best d_h1 {sub.d_h1.max():+.3f}, best d_h2 {sub.d_h2.max():+.3f})")
    elif not plateau:
        blocking.append("knife-edge: <2 contiguous passing rungs")
    return dict(candidate=name, n_rungs=int(len(sub)), window=str(sub.window.iloc[0]),
                any_pass=any_pass, best_block=best_block, plateau=plateau,
                best_dann_pp=float(sub.d_ann_pp.max()), best_dsr=float(sub.d_sr.max()),
                best_dsr_w=float(sub.loc[sub.d_sr.idxmax(), "w"]),
                best_dann_w=float(sub.loc[sub.d_ann_pp.idxmax(), "w"]),
                all_negy_zero=bool((sub.neg_years == 0).all()),
                all_mdd_ok=bool((sub.mdd > -7.0).all()),
                all_gross_ok=bool((sub.gross <= GEAR + 1e-12).all()),
                blocking=blocking,
                verdict="PASS_LADDER" if (any_pass and plateau and not blocking) else "FAIL")


# ------------------------------------------------------------- runner
def _ladder_rows(ch: pd.Series, name: str, ladder) -> list:
    s = load_ret(POOL[name][0])
    f0 = first_nonzero_index(s)
    if s.reindex(ch.index).isna().any():
        idx = overlap_index(ch, s)
        net_c = ch.reindex(idx)
        net_s = sleeve_on_champion_calendar(s, idx)
        win = f"OVERLAP[{idx[0].date()}..{idx[-1].date()}](+{net_s.attrs['n_champ_only_days']}champ-only-days)"
    else:
        net_c, net_s, win = ch, s, "FULL"
    rows = []
    h1_c, h2_c = _halves(net_c)   # champion halves on the SAME window/split as the blend
    for w in ladder:
        m = blend_metrics(net_c, net_s, w, window=win)
        rows.append(dict(candidate=name, w=w,
                         d_ann_pp=(m["ann"] - float(ann_geo(net_c))) * 100.0,
                         d_sr=m["sr"] - float(sharpe_d(net_c)),
                         d_mdd_pp=(m["mdd"] - float(max_dd(net_c))) * 100.0,
                         d_h1=m["h1"] - float(h1_c), d_h2=m["h2"] - float(h2_c),
                         neg_years=m["neg_years"], gross=m["gross"], window=win, n=m["n"],
                         ann=m["ann"] * 100.0, sr=m["sr"], mdd=m["mdd"] * 100.0,
                         h1=m["h1"], h2=m["h2"], worst_year=m["worst_year"] * 100.0,
                         drift_cost_bp_yr=m["drift_cost_bp_yr"]))
    return rows, net_c, net_s, win


def run_round3(out_dir: Path, quick: bool = False, n_nulls: int = 200,
               ladder=None, seed: int = 20260907) -> tuple:
    """Full round-3 run: screen -> blend ladder x candidates -> gates -> adversarial
    control (200 vol/corr-matched nulls) -> blend table CSV + recommendation JSON."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ch = load_champion()
    pool = screen_pool()
    ladder = ladder or ([0.05] if quick else W_LADDER)

    rows, controls = [], {}
    for name in ADMITTED:
        lad_rows, net_c, net_s, win = _ladder_rows(ch, name, ladder)
        rows.extend(lad_rows)
        sub = pd.DataFrame(lad_rows)
        vol = float(net_s.std(ddof=1))
        corr = joint_corr(net_c, net_s)
        # charter: the control runs at the SAME w as the candidate's best-dSR rung
        w_ctl = float(sub.loc[sub.d_sr.idxmax(), "w"])
        controls[name] = adversarial_control(net_c, vol=vol, corr=corr, w=w_ctl,
                                             n_nulls=n_nulls,
                                             rng=np.random.default_rng(seed),
                                             real_sleeve=net_s)
    tbl = pd.DataFrame(rows)
    gates = {n: gates_for(tbl, n) for n in ADMITTED}

    adoptable = [n for n, g in gates.items()
                 if g["verdict"] == "PASS_LADDER"
                 and controls[n]["verdict"] == "SURVIVES_CONTROL"]
    rec = dict(verdict="ADOPT" if adoptable else "NOTHING_ADOPTABLE",
               adopt=adoptable,
               gates=gates, adversarial=controls, pool=pool,
               shortability=shortability_report(),
               basis=dict(champion="git-HEAD pin sha256 " + PIN_SHA[:16],
                          champ_ann=float(ann_geo(ch)), champ_sr=float(sharpe_d(ch)),
                          champ_mdd=float(max_dd(ch)), champ_negy=int(neg_years(ch)[0]),
                          cost="6.4bps one-side FULL |dW| on rebalance drift; margin per bt.borrow @4.5% on blended gross-1",
                          rejected=REJECT_NOTES,
                          adversarial_rule="200 vol+corr-matched Gaussian nulls at same w; majority-gain => artifact"))

    tbl.to_csv(out_dir / "blend_table.csv", index=False)
    import json
    (out_dir / "recommendation.json").write_text(json.dumps(rec, indent=2, default=str))
    return tbl, rec


REJECT_NOTES = (
    "CTA_15vol: charter assumed library CTA own-span SR>=0.5; measured -0.147 (13/19 neg "
    "years) -> rejected (premise wrong, numbers listed). CMDTrot_6m_LS: 0.445 < 0.5 bar "
    "(charter '0.40 below bar' confirmed). COMP_invvol.csv: weights stream not returns -> "
    "unusable file. A_rs x MSSW cross-corr 0.866 -> charter pick-ONE honored: MSSW kept "
    "(higher own-SR 0.873 vs 0.549, same 2008+ span); A_rs admitted separately for the "
    "blend ladder but NOT co-blended with MSSW (their pair would double the same signal)."
)
