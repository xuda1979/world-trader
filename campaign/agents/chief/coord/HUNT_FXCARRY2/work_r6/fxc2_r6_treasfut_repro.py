#!/usr/bin/env python3
"""HUNT_FXCARRY2 ROUND 6 (a) — fraud-catch cross-verification of HUNT_TREASFUT R5.

Charter: reproduce HUNT_TREASFUT's R5 verdicts from published artifacts with OWN code
(no import of any HUNT_TREASFUT module). Mismatch -> escalate.

What it does, all self-contained:
 1. Independent data layer (tauctions.csv + DGS yields -> synth TR), own implementations.
 2. Rebuild all 19 R5 books TWO ways:
      A = honest single net_of (decision weights W, one shift(1) + one VT + costs) — the
          convention the published sleeve CSVs claim to represent;
      B = their battery path (net_of applied AGAIN to the effective weights = second
          shift(1) + second VT) — what the 19 .metas + FINDINGS table report.
 3. Compare A vs published CSVs (byte match) and B vs meta cells (net_sr to 4dp).
 4. Recompute the acceptance-relevant cells on the HONEST books: SR, halves, neg years,
    worst year, corrChamp, corrA6R7, era split, beats-spy comparison, own scrambles
    (row-permutation seed 7 + lagroll seed 11 block 10, 200 draws — same documented scheme).
 5. Independent drift tables (k=5 post windows) vs published drift_table_DGS*_k5.csv,
    unconditional all-days drift vs uncond_drift_control.json, and the 30y weak/strong
    conditional drift claim (0.285% vs 0.806% per 5d).

Output: scorecard JSON + stdout verdict. Honest negatives stand or fall on the honest book.
"""
import json
import hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
TA = f"{ROOT}/tools/quant/data/treasury_auctions/tauctions.csv"
FRED = f"{ROOT}/tools/quant/data/more_fred"
TS = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r6"

DURS = {"2": 4.4, "5": 5.6375, "10": 7.7, "30": 15.5}
TERM_OF = {"2": ("Note", "2-Year"), "5": ("Note", "5-Year"),
           "10": ("Note", "10-Year"), "30": ("Bond", "30-Year")}
MIN_PRIOR = 4
COST_BPS = 6.4
K = 5
BOOKS = []  # (name, tenor, kind, sign, k)
for t in ("2", "5", "10", "30"):
    BOOKS += [(f"POST5_{t}_long", t, "post", 1, 5), (f"PRE5_{t}_long", t, "pre", 1, 5),
              (f"COND5_{t}", t, "cond", 1, 5)]
BOOKS += [("POST5_10_anti", "10", "post", -1, 5), ("PRE5_10_anti", "10", "pre", -1, 5),
          ("COND5_10_anti", "10", "cond", -1, 5),
          ("POST3_10_long", "10", "post", 1, 3), ("COND3_10", "10", "cond", 1, 3),
          ("POST10_10_long", "10", "post", 1, 10), ("COND10_10", "10", "cond", 1, 10)]

# ---------------------------------------------------------------- own primitives

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def load_yield(sid):
    s = pd.read_csv(f"{FRED}/{sid}.csv", index_col="date", parse_dates=True)["value"].astype(float)
    assert s.index.is_monotonic_increasing and not s.index.duplicated().any()
    return (s / 100.0).sort_index()

def synth_tr(y, dur):
    return -dur * y.diff() + y.shift(1) / 252.0

def grid(t):
    return synth_tr(load_yield(f"DGS{t}"), DURS[t]).dropna().to_frame(t)

def load_auctions():
    raw = pd.read_csv(TA, parse_dates=["date"])
    keep = []
    for t, (typ, term) in TERM_OF.items():
        s = raw[(raw["type"] == typ) & (raw["term"] == term)].copy()
        s = (s.sort_values("total_accepted_mmn", ascending=False)
              .drop_duplicates(subset=["date"], keep="first").sort_values("date"))
        keep.append(pd.Series(s.bid_to_cover.values, index=s["date"].values, name=t))
    ev = pd.concat(keep, axis=1, sort=True).sort_index()
    ev.index = pd.DatetimeIndex(ev.index)
    ev.index.name = "auction_date"
    return ev

def expanding_median_past(s):
    s = s.sort_index()
    v = s.values.astype(float)
    out = np.full(len(v), np.nan)
    for i in range(1, len(v)):
        past = v[:i]
        past = past[np.isfinite(past)]
        if len(past) >= MIN_PRIOR:
            out[i] = float(np.median(past))
    return pd.Series(out, index=s.index)

def weights_for(t, kind, sign, k, ev):
    R = grid(t)
    idx = R.index
    w = pd.Series(0.0, index=idx)
    if kind in ("post", "pre"):
        evd = ev.index[ev[t].notna()]
        ipos = np.searchsorted(idx.values, evd.values)
        n = len(idx)
        for e in ipos:
            if e >= n:
                continue
            lo, hi = (e + 1, min(e + k, n - 1)) if kind == "post" else (max(e - k, 0), e - 1)
            if hi >= lo:
                w.iloc[lo:hi + 1] = float(sign)
    else:  # cond
        med = expanding_median_past(ev[t])
        surprise = (ev[t] - med).dropna()
        pos = pd.Series(np.arange(len(idx)), index=idx)
        for e, s in surprise.items():
            i = pos.asof(e)
            if pd.isna(i):
                continue
            i = int(i)
            if i >= len(idx):
                continue
            v = float(sign) * float(np.sign(s))
            lo, hi = i + 1, min(i + k, len(idx) - 1)
            if hi >= lo:
                w.iloc[lo:hi + 1] = v
    return pd.DataFrame({t: w})

def vt_scale(gross, target=0.10, window=60, cap=3.0):
    vols = gross.expanding(min_periods=window).std(ddof=1) * np.sqrt(252)
    scale = target / vols.replace(0.0, np.nan)
    scale = scale.where(vols > 0, 1.0).clip(upper=cap).clip(lower=0.2).shift(1)
    return scale.fillna(1.0)

def cost_turnover(W):
    w = W.fillna(0.0)
    prev = w.shift(1)
    prev.iloc[0] = 0.0
    return (w - prev).abs().sum(axis=1) * COST_BPS / 1e4

def borrow_cost(W):
    return (-W.clip(upper=0.0)).sum(axis=1) * 0.005 / 252.0

def net_of(W, R, vt=True):
    """Decision weights -> T+1 costed net (single shift + single VT)."""
    W = W.reindex(index=R.index, columns=R.columns).fillna(0.0)
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        We = We.mul(vt_scale(gross.to_frame("g"))["g"], axis=0)
    net = (We * R).sum(axis=1) - cost_turnover(We) - borrow_cost(We)
    return net, We

def sharpe_d(r):
    s = r.std(ddof=1)
    return 0.0 if not s or not np.isfinite(s) or s < 1e-12 else float(r.mean() / s * np.sqrt(252))

def half_split(r):
    k = len(r) // 2
    return sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:])

def neg_years(r):
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    yr = yr.where(np.isfinite(yr), -1.0)
    return int((yr < 0).sum()), float(yr.min())

def ann_geo(r):
    prod = (1 + r).prod(min_count=1)
    return np.nan if (not np.isfinite(prod) or prod <= 0) else float(prod ** (252.0 / len(r)) - 1)

def corr_to(ref, r):
    j = pd.concat([ref.rename("r"), r.rename("s")], axis=1).dropna()
    return float(j.r.corr(j.s)) if len(j) > 2 else np.nan

def scramble_perm(We_final, R, net, n=200, seed=7):
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real = sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - cost_turnover(Wp) - borrow_cost(Wp)
        if sharpe_d(book) >= real:
            cnt += 1
    return cnt / n

def lagroll_p(We_final, R, net, n=200, block=10, seed=11):
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0).values
    Re = R.reindex(idx).fillna(0.0).values
    T = len(idx)
    win = slice(block, T - block)

    def sr_of(book):
        return sharpe_d(pd.Series(book, index=idx).iloc[win])

    real = sr_of((We * Re).sum(axis=1) - cost_turnover(pd.DataFrame(We, index=idx))
                 - borrow_cost(pd.DataFrame(We, index=idx)))
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(block, T - block + 1))
        Wp = np.roll(We, lag, axis=0)
        book = ((Wp * Re).sum(axis=1) - cost_turnover(pd.DataFrame(Wp, index=idx))
                - borrow_cost(pd.DataFrame(Wp, index=idx)))
        if sr_of(book) >= real:
            cnt += 1
    return cnt / n

# ---------------------------------------------------------------- main

def main():
    ev = load_auctions()
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    a6r7 = pd.read_csv(f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
                       index_col=0, parse_dates=True).iloc[:, 0]
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", parse_dates=["date"]
                      ).set_index("date")["close"].sort_index().pct_change()
    metas = pd.read_json(f"{TS}/work_r5/round5_meta.json").T

    score = {"data_pins": {"tauctions": sha16(TA),
                           "champion": sha16(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")},
             "books": {}, "drift": {}}
    rows = []
    for name, t, kind, sign, k in BOOKS:
        W = weights_for(t, kind, sign, k, ev)
        R = grid(t)
        # A: honest single net_of
        netA, WeA = net_of(W, R)
        live = (WeA.fillna(0.0) != 0).any(axis=1)
        netA = netA[netA.index >= live.idxmax()]
        # B: their battery path — net_of applied AGAIN to effective weights
        netB, WeB = net_of(WeA, R)
        netB = netB[netB.index >= (WeB.fillna(0.0) != 0).any(axis=1).idxmax()]

        pub = pd.read_csv(f"{TS}/sleeves/TREASFUT5_{name}.csv", parse_dates=["date"]
                          ).set_index("date")["ret"]
        pubpos = pd.read_csv(f"{TS}/sleeves/TREASFUT5_{name}_positions.csv", parse_dates=["date"]
                             ).set_index("date")["w"]
        devA = float(np.nanmax(np.abs(netA.reindex(pub.index).values - pub.values)))
        m = metas.loc[name]
        srB = sharpe_d(netB)
        # honest-book cells
        sr, ag = sharpe_d(netA), ann_geo(netA)
        neg, worst = neg_years(netA)
        h1, h2 = half_split(netA)
        pre = sharpe_d(netA[netA.index < "2013-01-01"])
        post = sharpe_d(netA[netA.index >= "2013-01-01"])
        cc = corr_to(champ, netA)
        ca6 = corr_to(a6r7, netA)
        # beats spy on matched span (their §7 convention: candidate book vs spy_bh SR)
        j = pd.concat([netA.rename("b"), spy.rename("s")], axis=1).dropna()
        spy_sr = sharpe_d(j.s)
        p_perm = scramble_perm(WeA, R, netA)
        p_lag = lagroll_p(WeA, R, netA)
        # honest leak probe: same-period corr of the PUBLISHED effective positions with the
        # honest book return (both on the same single-T+1 convention)
        leak_honest = corr_to(pubpos.reindex(netA.index).fillna(0.0), netA)
        # published positions == my effective weights?
        dev_pos = float(np.nanmax(np.abs(
            WeA.reindex(pubpos.index).values.flatten() - pubpos.values)))
        rows.append(dict(name=name, n_pub=len(pub), n_meta=int(m.n), n_honest=len(netA),
            sr_pub=round(sharpe_d(pub), 4), sr_meta=m.net_sr, sr_honest=round(sr, 4),
            sr_double=round(srB, 4), devA_vs_pub=devA, dev_pos_vs_pub=dev_pos,
            ann_honest=round(ag, 4), neg_honest=neg, worst_honest=round(worst, 4),
            h1=round(h1, 4), h2=round(h2, 4), era_pre=round(pre, 4), era_post=round(post, 4),
            corr_champ=round(cc, 4), corr_a6r7=round(ca6, 4),
            spy_sr_matched=round(spy_sr, 4), beats_spy=bool(sr > spy_sr),
            perm_p=p_perm, lag_p=p_lag, leak_honest_c=round(leak_honest, 4)))
        score["books"][name] = rows[-1]

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    print("=== A) published-CSV vs meta vs my-honest rebuild (all 19 books) ===")
    print(df[["name", "n_pub", "n_meta", "n_honest", "sr_pub", "sr_meta", "sr_honest",
              "sr_double", "devA_vs_pub", "dev_pos_vs_pub"]].to_string(index=False))
    print()
    exactA = all(r["devA_vs_pub"] < 1e-12 for r in rows)
    exact_pos = all(r["dev_pos_vs_pub"] < 1e-12 for r in rows)
    exactB = all(abs(r["sr_double"] - metas.loc[r["name"]].net_sr) < 5e-5 for r in rows)
    print(f"my honest rebuild == published sleeve CSV, byte-exact (<1e-12): {exactA}")
    print(f"my effective weights == published positions CSV (<1e-12):        {exact_pos}")
    print(f"my double-net rebuild == 19 meta net_sr cells (<5e-5):           {exactB}")
    csv_dupes = []
    for name, t, kind, sign, k in BOOKS:
        if k == K:
            continue
        base = (f"POST5_{t}_long" if kind == "post" else f"COND5_{t}")
        a = open(f"{TS}/sleeves/TREASFUT5_{name}.csv", "rb").read()
        b = open(f"{TS}/sleeves/TREASFUT5_{base}.csv", "rb").read()
        mk = json.load(open(f"{TS}/sleeves/TREASFUT5_{name}.meta.json"))["k"]
        csv_dupes.append((name, base, a == b, mk))
    print("plateau-book published CSVs byte-identical to their k=5 counterpart:", csv_dupes)
    print()
    print("=== B) honest single-T+1 book cells (what the submission SHOULD have reported) ===")
    print(df[["name", "sr_honest", "ann_honest", "h1", "h2", "neg_honest", "worst_honest",
              "corr_champ", "corr_a6r7", "spy_sr_matched", "beats_spy", "perm_p", "lag_p",
              "era_pre", "era_post"]].to_string(index=False))
    print()
    n_pass = sum(1 for r in rows if r["sr_honest"] >= 1.0 and r["beats_spy"]
                 and r["perm_p"] <= 0.05 and r["lag_p"] <= 0.15
                 and min(abs(r["era_pre"]), abs(r["era_post"])) >= 0.25
                 and r["era_pre"] * r["era_post"] > 0)
    print(f"honest books passing sr>=1.0 AND beats_spy AND scrambles AND era: {n_pass}/19")
    print(f"honest books with SR>=1.0: {sum(1 for r in rows if r['sr_honest']>=1.0)}/19; "
          f"max honest SR = {max(r['sr_honest'] for r in rows):.4f}")
    print()

    # ---- drift controls ------------------------------------------------------
    print("=== C) drift controls (independent) ===")
    uncond_pub = json.load(open(f"{TS}/work_r5/uncond_drift_control.json"))
    for t in ("2", "5", "10", "30"):
        R = grid(t)
        ret = R[t]
        pos = pd.Series(np.arange(len(R)), index=R.index)
        evd = ev.index[ev[t].notna()]
        dr = []
        for a in evd:
            i = pos.asof(a)
            if pd.isna(i):
                dr.append(np.nan)
                continue
            i = int(i)
            lo, hi = i + 1, min(i + K, len(R) - 1)
            dr.append(float(ret.iloc[lo:hi + 1].sum()) if hi >= lo else np.nan)
        dr = pd.Series(dr, index=evd).dropna()
        post_bp = dr.mean() * 1e4
        post_t = dr.mean() / (dr.std(ddof=1) / np.sqrt(len(dr)))
        # unconditional: 5d forward TR sum over ALL grid days
        allf = ret.rolling(K).sum().shift(-K)
        all_bp = allf.mean() * 1e4
        # weak/strong conditional on surprise sign (PIT median, MIN_PRIOR=4)
        med = expanding_median_past(ev[t])
        surp = (ev[t] - med).reindex(dr.index)
        weak = dr[surp < 0].mean() * 1e4 if (surp < 0).any() else np.nan
        strong = dr[surp > 0].mean() * 1e4 if (surp > 0).any() else np.nan
        pubtab = pd.read_csv(f"{TS}/work_r5/drift_table_DGS{t}_k{K}.csv", parse_dates=["date"]
                             ).set_index("date")["drift"].dropna()
        devtab = float(np.nanmax(np.abs(dr.reindex(pubtab.index).values - pubtab.values)))
        u = uncond_pub[t]
        score["drift"][t] = dict(post_bp=post_bp, pub_post_bp=u["post_bp"], all_bp=all_bp,
                                 pub_all_bp=u["all_bp"], excess_bp=post_bp - all_bp,
                                 pub_excess_bp=u["excess_bp"], weak_bp=weak, strong_bp=strong,
                                 drift_table_maxdev=devtab)
        print(f"  {t}y: post {post_bp:6.1f}bp (pub {u['post_bp']:6.1f})  all {all_bp:6.1f}bp "
              f"(pub {u['all_bp']:6.1f})  excess {post_bp-all_bp:+6.1f}bp "
              f"(pub {u['excess_bp']:+6.1f})  t {post_t:4.1f} (pub {u['excess_t']:4.1f})  "
              f"weak/strong {weak:6.1f}/{strong:6.1f}bp  driftCSV maxdev {devtab:.2e}")
    print()

    verdict = dict(
        published_csv_matches_honest_single_netof=exactA,
        published_positions_match=exact_pos,
        metas_match_double_netof_rebuild=exactB,
        metas_match_published_csv=False,
        honest_books_any_pass=n_pass,
        max_honest_sr=float(max(r["sr_honest"] for r in rows)),
    )
    score["verdict"] = verdict
    with open(f"{OUT}/r6_treasfut_repro_scorecard.json", "w") as f:
        json.dump(score, f, indent=1, default=str)
    print("scorecard -> work_r6/r6_treasfut_repro_scorecard.json")
    print(json.dumps(verdict, indent=1))

if __name__ == "__main__":
    main()
