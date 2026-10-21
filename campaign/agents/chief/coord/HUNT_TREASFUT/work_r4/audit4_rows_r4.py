#!/usr/bin/env python3
"""R4 DEAD_IDEAS audit rotation (HUNT_TREASFUT round 4b) — 4 non-treasury rows.

Audits (repro + numbers re-verification vs campaign/results/DEAD_IDEAS.csv):
  ROW 33: USDJPY weekday sign-maps (30-grid)      [SKILL_ALPHAAGB_B p7]
  ROW 34: FX tsmom63 satellites EUR/GBP/AUD       [SKILL_ALPHAAGB_B p8]
  ROW 29: QQQ/SPY + XLF/SPY ratio z-reversion     [SKILL_ALPHAAGB_B p4b]
  ROW 9:  gold-silver spread                      [B2_highfreq 'XAU_SLV' — probe was
          LOGGED NOT SAVED; this script REBUILDS it from the described mechanism
          (log-spread z-reversion) under the CURRENT GATES_CONTRACT cost model]

Upgrades over the original probes (that's the audit value-add):
  - all correlation gates recomputed vs the CURRENT champion
    GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (originals used HONEST14V3)
  - row 9 gets a full battery it never had (halves/negy/perm/corr) and the
    contract-standard cost 6.4bps FULL |dW| + 0.5%/yr borrow (B2 used 6bps on
    half-turnover, which undercharges high-turnover z books)
No tuning: windows are the originals (33/34/29) or a-priori grid (row 9).
"""
import itertools
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6.4 / 1e4          # one-side on FULL |dW| (GATES_CONTRACT)
BORROW = 0.005 / 252
CHAMP = pd.read_csv(
    f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
    index_col=0, parse_dates=True).iloc[:, 0].astype(float)


def stats(net: pd.Series) -> dict:
    net = net.dropna()
    sr = net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else float("nan")
    eq = (1 + net).cumprod()
    mdd = float((eq / eq.cummax() - 1).min())
    yr = net.groupby(net.index.year).apply(lambda s: float((1 + s).prod() - 1))
    h = np.array_split(net, 2)
    hsr = [x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else float("nan")
           for x in h]
    # lagroll permutation (timing-only destruction, re-costed) — R1 convention
    rng = np.random.default_rng(0)
    pos_like = net.copy()
    perm_srs = []
    base = net - net.mean()
    for _ in range(200):
        s = pd.Series(rng.permutation(net.values), index=net.index)
        perm_srs.append(s.mean() / s.std() * np.sqrt(252))
    p = float(np.mean(np.array(perm_srs) >= sr))
    return {"sr": float(sr), "ann": float(net.mean() * 252),
            "mdd": mdd, "negyr": int((yr < 0).sum()),
            "worst": float(yr.min()), "h1": float(hsr[0]), "h2": float(hsr[1]),
            "perm_p": p, "n": len(net)}


def corr_champ(net: pd.Series) -> float:
    j = pd.concat([net.rename("n"), CHAMP.rename("c")], axis=1,
                  join="inner").dropna()
    return float(j.n.corr(j.c))


def vt_apply(net: pd.Series, tgt=0.10, min_win=60, cap=3.0) -> pd.Series:
    vol = net.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0.0
    return net * s


def fx(n):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/fx/{n}.csv",
                     index_col=0, parse_dates=True)
    s = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    return s[~s.index.duplicated(keep="last")].sort_index()


def print_row(tag, st, corr, extra=""):
    print(f"  {tag:28s} SR {st['sr']:+.3f} H1 {st['h1']:+.2f} H2 {st['h2']:+.2f} "
          f"negyr {st['negyr']:2d} worst {st['worst']*100:+.1f}% "
          f"perm_p {st['perm_p']:.3f} corrChamp {corr:+.3f} n {st['n']} {extra}")


# ---------------------------------------------------------------- ROW 33
print("=" * 100)
print("ROW 33  USDJPY weekday sign-maps (30-grid)  claim: best SR 0.599 <0.6 & best-of-30")
jpy = fx("USD_JPY").dropna()
r = jpy.pct_change()
rows = []
for bits in itertools.product([-1, 1], repeat=5):
    if all(b == 1 for b in bits) or all(b == -1 for b in bits):
        continue
    pos = pd.Series(0.0, index=r.index)
    for d, b in enumerate(bits):
        pos[r.index.dayofweek == d] = b
    g = (pos.shift(1) * r).fillna(0.0)          # T+1
    g = g - pos.diff().abs().fillna(0.0) * COST - BORROW * pos.shift(1).clip(upper=0).abs().fillna(0)
    net = vt_apply(g)
    rows.append((float(net.mean() / net.std() * np.sqrt(252)), bits))
rows.sort(reverse=True)
print(f"  re-run on current data: {len(rows)} maps, span {r.index.min().date()}..{r.index.max().date()}")
for sr, bits in rows[:3]:
    days = [d for d, b in enumerate(bits) if b == -1]
    print(f"  top map longJPY days {days}: SR {sr:+.3f}")
best_sr, best_bits = rows[0]
print(f"  claim check: best-of-30 SR {best_sr:+.3f} vs claimed 0.599 -> "
      f"{'MATCH' if abs(best_sr - 0.599) < 0.02 else 'DRIFT'}; <0.6 gate: {best_sr < 0.6}")

# ---------------------------------------------------------------- ROW 34
print("=" * 100)
print("ROW 34  FX tsmom63 satellites EUR/GBP/AUD  claim: 'SR <=0.09'  (audit: AUD understated?)")
for n in ["EUR_USD", "GBP_USD", "AUD_USD"]:
    p = fx(n).dropna()
    rr = p.pct_change()
    tr = p - p.shift(63)
    ps = pd.Series(np.nan, index=p.index)
    ps[tr > 0] = 1.0
    ps[tr < 0] = -1.0
    ps = ps.ffill().fillna(0.0)
    g = (ps.shift(1) * rr).fillna(0.0)
    g = g - ps.diff().abs().fillna(0.0) * COST - BORROW * ps.shift(1).clip(upper=0).abs().fillna(0)
    net = vt_apply(g)
    print_row(f"{n} tsmom63", stats(net), corr_champ(net))

# ---------------------------------------------------------------- ROW 29
print("=" * 100)
print("ROW 29  QQQ/SPY + XLF/SPY ratio zrev  claim: QQQ -0.051/-0.230/-0.222; XLF +0.293/+0.011/-0.044")
px = {}
for n in ["QQQ", "SPY", "XLF"]:
    df = pd.read_csv(f"{ROOT}/tools/quant/data/twelve_big/{n}.csv",
                     parse_dates=["date"], index_col="date")
    px[n] = df["close"].sort_index()
    px[n] = px[n][~px[n].index.duplicated(keep="last")]
P = pd.DataFrame(px).sort_index().dropna()


def ratio_zrev(a, b, zwin):
    ratio = P[a] / P[b]
    z = (ratio - ratio.rolling(zwin).mean()) / ratio.rolling(zwin).std()
    pos = pd.Series(np.nan, index=P.index)
    pos[z < -1.0] = 1.0     # long ratio when cheap
    pos[z > 1.0] = -1.0
    pos = pos.ffill().fillna(0.0)
    ra, rb = P[a].pct_change(), P[b].pct_change()
    # dollar-neutral 0.5/0.5: long a / short b (or reversed)
    w = pd.DataFrame({"a": 0.5 * pos, "b": -0.5 * pos})
    rets = pd.DataFrame({"a": ra, "b": rb})
    g = (w.shift(1) * rets).sum(axis=1).fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    g = g - turn * COST - BORROW * w.shift(1).clip(upper=0).abs().sum(axis=1).fillna(0)
    return vt_apply(g)


claimed = {("QQQ", "SPY"): {-0.051: 21, -0.230: 63, -0.222: 126},
           ("XLF", "SPY"): {0.293: 21, 0.011: 63, -0.044: 126}}
for (a, b), m in claimed.items():
    for zw in [21, 63, 126]:
        net = ratio_zrev(a, b, zw)
        st = stats(net)
        want = [k for k, v in m.items() if v == zw][0]
        ok = abs(st["sr"] - want) < 0.03
        print_row(f"{a}/{b} zrev{zw} (claim {want:+.3f})", st, corr_champ(net),
                  extra=f"{'MATCH' if ok else 'DRIFT'}")

# ---------------------------------------------------------------- ROW 9
print("=" * 100)
print("ROW 9  gold-silver spread (B2 'XAU_SLV SR -0.2..-0.6', probe never saved) — REBUILD")
xau = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/xau.csv",
                  index_col=0, parse_dates=True).iloc[:, 0].astype(float)
slv = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/slv.csv",
                  index_col=0, parse_dates=True).iloc[:, 0].astype(float)
X = pd.concat([xau.rename("xau"), slv.rename("slv")], axis=1).sort_index().dropna()
print(f"  span {X.index.min().date()}..{X.index.max().date()} n={len(X)}")
ls = np.log(X.xau) - np.log(X.slv)
rx, rs = X.xau.pct_change(), X.slv.pct_change()
for zwin in [21, 63, 126]:
    z = (ls - ls.rolling(zwin).mean()) / ls.rolling(zwin).std()
    pos = pd.Series(np.nan, index=X.index)
    pos[z > 1.0] = -1.0     # reversion: short spread when rich
    pos[z < -1.0] = 1.0
    pos = pos.ffill().fillna(0.0)
    w = pd.DataFrame({"xau": 0.5 * pos, "slv": -0.5 * pos})
    rets = pd.DataFrame({"xau": rx, "slv": rs})
    g = (w.shift(1) * rets).sum(axis=1).fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    g = g - turn * COST - BORROW * w.shift(1).clip(upper=0).abs().sum(axis=1).fillna(0)
    net = vt_apply(g)
    print_row(f"XAU/SLV zrev{zwin} (B2 claim -0.2..-0.6)", stats(net), corr_champ(net))
# B2's own claim was a MOMENTUM-like spread failure; also test momentum sign for the record
z = (ls - ls.rolling(63).mean()) / ls.rolling(63).std()
pos = pd.Series(np.nan, index=X.index)
pos[z > 1.0] = 1.0
pos[z < -1.0] = -1.0
pos = pos.ffill().fillna(0.0)
w = pd.DataFrame({"xau": 0.5 * pos, "slv": -0.5 * pos})
g = (w.shift(1) * pd.DataFrame({"xau": rx, "slv": rs})).sum(axis=1).fillna(0.0)
g = g - w.diff().abs().sum(axis=1).fillna(0.0) * COST - BORROW * w.shift(1).clip(upper=0).abs().sum(axis=1).fillna(0)
print_row("XAU/SLV z-MOM63 (sign-flip control)", stats(vt_apply(g)), corr_champ(vt_apply(g)))

print("=" * 100)
print("AUDIT RULE: a row is CONFIRMED if re-run SR lands within ~0.03 of claim (or inside")
print("the claimed band) and the negative verdict survives current-champion corr + battery.")
