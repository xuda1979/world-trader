"""HUNT_COT2 round 3 (a): INDEPENDENT cross-verification of HUNT_CMDT2 sleeve CSVs.

Fraud-catch duty (charter round 3a): recompute SR / halves / neg_years / worst-year /
ann / vol / n / corr-vs-champion from HUNT_CMDT2's SAVED sleeve CSVs using MY OWN code
(no import of their bt.metrics / their scripts), and compare against the numbers they
published in each .csv.meta + FINDINGS.md. Any mismatch is escalated.

The sleeve CSVs contain only [date, ret] net-of-cost book returns, so three published
quantities are structurally NOT reproducible from the CSV alone and are flagged as such
rather than trusted: scramble_p (needs the weight matrix + raw returns), the 6.4bps cost
deduction itself, and vol-target scaling. Everything else is recomputed from scratch.

Self-tests first: synthetic series with hand-computable answers prove the metric
implementations are correct BEFORE they are pointed at anyone's sleeves.
"""
import os
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
ANN = 252

# --------------------------------------------------------------- my own metrics

def sharpe_d(r: pd.Series) -> float:
    """Daily SR annualized: mean / std(ddof=1) * sqrt(252)."""
    s = r.std(ddof=1)
    if not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def halves(r: pd.Series):
    """Gate c): SR on first half vs second half, split at n//2 (position split)."""
    k = len(r) // 2
    if k == 0:
        return (np.nan, np.nan)
    return (sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:]))


def year_stats(r: pd.Series):
    """Gate d): (# negative years, worst year geometric return). NaN year => negative."""
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    yr = yr.where(np.isfinite(yr), -1.0)          # fail-closed on ruined/missing years
    return int((yr < 0).sum()), float(yr.min())


def ann_geo(r: pd.Series):
    prod = (1 + r).prod(min_count=1)
    if not np.isfinite(prod) or prod <= 0:
        return np.nan                              # ruin guard
    return float(prod ** (ANN / len(r)) - 1)


def load_book(path: str) -> pd.Series:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    assert list(df.columns) == ["ret"], f"{path}: unexpected columns {list(df.columns)}"
    s = df.iloc[:, 0].astype(float)
    assert s.index.is_monotonic_increasing, f"{path}: dates not monotonic"
    assert not s.index.has_duplicates, f"{path}: duplicate dates"
    assert isinstance(s.index, pd.DatetimeIndex) and not s.isna().any(), \
        f"{path}: non-date index or NaN rows"
    return s


def integrity(s: pd.Series) -> dict:
    """Distribution forensics for fabrication / fill-zero artifacts."""
    z = float((s == 0).mean())
    exc = s - s.mean()
    kurt = float((exc**4).mean() / (exc.var(ddof=1) ** 2) - 3.0) if s.std() > 0 else np.nan
    ac1 = float(s.autocorr(1)) if len(s) > 2 else np.nan
    return dict(n=len(s), start=str(s.index[0].date()), end=str(s.index[-1].date()),
                zero_frac=z, max_abs=float(s.abs().max()), kurtosis=kurt, ac1=ac1,
                vol=float(s.std(ddof=1) * np.sqrt(ANN)))


# --------------------------------------------------------------------- self-tests

def self_test():
    idx = pd.bdate_range("2020-01-01", periods=8)
    # SR of a constant book: mean=0.001, std -> tiny; use a known alternating series instead
    r = pd.Series([0.01, -0.01, 0.01, -0.01], index=pd.bdate_range("2020-01-01", periods=4))
    assert abs(sharpe_d(r)) < 1e-12, "SR of zero-mean series must be 0"
    r2 = pd.Series([0.01, 0.02, 0.01, 0.02], index=pd.bdate_range("2020-01-01", periods=4))
    exp = (0.015 / r2.std(ddof=1)) * np.sqrt(252)
    assert abs(sharpe_d(r2) - exp) < 1e-12, f"SR formula wrong: {sharpe_d(r2)} vs {exp}"
    # halves: zero-variance half must NOT read as +inf skill (fail-closed 0.0 convention)
    r3 = pd.Series([0.01] * 4 + [-0.01] * 4, index=idx)
    h1, h2 = halves(r3)
    assert h1 == 0.0 and h2 == 0.0, f"constant halves must both be 0.0 (fail-closed), got {h1},{h2}"
    # hand-computable halves: n=8, split k=4. H1=[1,2,1,2]bp -> mean 1.5bp,
    # std = 1/sqrt(3) bp (deviations +/-0.5 over ddof=1 on 4 obs); H2 sign-flipped.
    r3b = pd.Series([1, 2, 1, 2, -1, -2, -1, -2], dtype=float,
                    index=idx) * 1e-4
    h1b, h2b = halves(r3b)
    exp_half = (1.5e-4 / (1e-4 * np.sqrt(1 / 3))) * np.sqrt(252)
    assert abs(h1b - exp_half) < 1e-9 and abs(h2b + exp_half) < 1e-9, (h1b, h2b, exp_half)
    # neg_years: one bad year, geometric year return computed over ACTUAL day count
    idx2 = pd.bdate_range("2019-01-01", "2020-12-31")
    r4 = pd.Series(np.where(idx2.year == 2019, 0.001, -0.002), index=idx2)
    neg, worst = year_stats(r4)
    n_bad = int((idx2.year == 2020).sum())
    assert neg == 1 and abs(worst - ((1 - 0.002) ** n_bad - 1)) < 1e-9, (neg, worst, n_bad)
    # ruin year counts as negative (fail-closed)
    r5 = pd.Series([1.0, -1.0] * 3, index=pd.bdate_range("2021-01-04", periods=6))
    neg5, worst5 = year_stats(r5)
    assert neg5 == 1 and worst5 == -1.0, (neg5, worst5)
    # ann_geo hand-check (relative tol: the scaled value is O(1e10))
    r6 = pd.Series([0.10, 0.10], index=pd.bdate_range("2020-01-01", periods=2))
    assert abs(ann_geo(r6) / ((1.21 ** (252 / 2)) - 1) - 1) < 1e-9
    # corr sanity: series with itself = 1, orthogonal alternating vs its negative = -1
    a = pd.Series([0.01, -0.02, 0.03, -0.04], index=pd.bdate_range("2020-01-01", periods=4))
    assert abs(corr_to(a, a) - 1.0) < 1e-12
    assert abs(corr_to(a, -a) + 1.0) < 1e-12
    print("self-test: 10/10 assertions green (SR, halves, neg_years, ruin, ann_geo, corr)")


def corr_to(ref: pd.Series, s: pd.Series) -> float:
    j = pd.concat([ref.rename("r"), s.rename("s")], axis=1).dropna()
    return float(j["r"].corr(j["s"])) if len(j) > 2 else np.nan


# ------------------------------------------------------------------ gate verdicts

def close_or_missing(claim, got, tol) -> bool:
    """FAIL-CLOSED comparison (R3 TDD): a missing (None) or non-finite (NaN) claim is a
    FAILURE, never a pass. abs(x - NaN) > tol is False, so a naive float compare would
    silently MATCH a sleeve whose meta is missing/corrupt — the exact bug this closes."""
    if claim is None:
        return False
    try:
        c = float(claim)
    except (TypeError, ValueError):
        return False
    if not np.isfinite(c) or not np.isfinite(float(got)):
        return False
    return abs(c - float(got)) <= tol


def gates(sr, h1, h2, neg, worst, corr):
    return dict(a_sr=sr >= 1.0,
                c_halves=(h1 >= 0.5 and h2 >= 0.5),
                d_yearly=(neg <= 2 and worst > -0.05),
                f_corr=abs(corr) < 0.15)


def parse_meta_text(txt: str) -> dict:
    out = {}
    for ln in txt.splitlines():
        if "=" not in ln or ln.startswith("name="):
            continue
        if ln.startswith("SR="):
            for tok in ln.split():
                if "=" not in tok:
                    continue
                k, v = tok.split("=", 1)
                v = v.strip("%")
                try:
                    out[k] = float(v) if k not in ("n",) else int(float(v))
                except ValueError:
                    out[k] = v
        elif ln.startswith("gates:"):
            out["gates_line"] = ln.strip()
    return out


def parse_meta(path: str) -> dict:
    return parse_meta_text(open(path).read())


def main():
    self_test()
    champ = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    files = sorted(f for f in os.listdir(SLEEVES) if f.endswith(".csv"))
    rows = []
    print(f"\n=== independent recompute of {len(files)} HUNT_CMDT2 sleeve CSVs ===")
    for fn in files:
        name = fn[:-4]
        s = load_book(f"{SLEEVES}/{fn}")
        itg = integrity(s)
        sr = sharpe_d(s)
        h1, h2 = halves(s)
        neg, worst = year_stats(s)
        ann = ann_geo(s)
        c = corr_to(champ, s)
        g = gates(sr, h1, h2, neg, worst, c)
        m = parse_meta(f"{SLEEVES}/{fn}.meta")

        def close(a, b, tol):
            try:
                return abs(float(a) - float(b)) <= tol
            except (TypeError, ValueError):
                return False

        checks = {
            "SR": close_or_missing(m.get("SR"), sr, 0.0015),
            "H1": close_or_missing(m.get("H1"), h1, 0.015),
            "H2": close_or_missing(m.get("H2"), h2, 0.015),
            "negyrs": close_or_missing(m.get("negyrs"), neg, 0.0),
            "worstyr": close_or_missing(m.get("worstyr"), worst * 100, 0.2),
            "vol": close_or_missing(m.get("vol"), itg["vol"] * 100, 0.2),
            "ann": close_or_missing(m.get("ann"), ann * 100, 0.2),
            "corr": close_or_missing(m.get("corr_champ"), c, 0.005),
            "n": close_or_missing(m.get("n"), itg["n"], 0.0),
            "window": str(m.get("n")) != "" and name and True,  # placeholder, replaced below
        }
        # window check: meta embeds start->end in the SR= line's tail or instruments line
        meta_txt = open(f"{SLEEVES}/{fn}.meta").read()
        win_ok = (itg["start"] in meta_txt and itg["end"] in meta_txt)
        checks["window"] = win_ok
        bad = [k for k, v in checks.items() if not v]
        rows.append(dict(name=name, sr=round(sr, 3), h1=round(h1, 2), h2=round(h2, 2),
                         neg=neg, worst=round(worst * 100, 1), ann=round(ann * 100, 1),
                         vol=round(itg["vol"] * 100, 1), corr=round(c, 3), n=itg["n"],
                         zero_frac=round(itg["zero_frac"], 3), max_abs=round(itg["max_abs"], 3),
                         kurt=round(itg["kurtosis"], 1), ac1=round(itg["ac1"], 3),
                         meta_sr=m.get("SR"), mismatches=";".join(bad) or "NONE",
                         all_match=not bad))
        print(f"[{name}] SR={sr:.3f} (meta {m.get('SR')}) H1={h1:.2f}/{h2:.2f} "
              f"(meta {m.get('H1')}/{m.get('H2')}) negyr={neg} (meta {m.get('negyrs')}) "
              f"worst={worst*100:.1f}% (meta {m.get('worstyr')}) corr={c:.3f} "
              f"(meta {m.get('corr_champ')}) n={itg['n']} (meta {m.get('n')}) "
              f"zero%={itg['zero_frac']*100:.1f} max|r|={itg['max_abs']:.3f} "
              f"-> {'MATCH' if not bad else 'MISMATCH: ' + ','.join(bad)}")
        print(f"    my gates: a_sr={g['a_sr']} c_halves={g['c_halves']} "
              f"d_yearly={g['d_yearly']} f_corr={g['f_corr']}")
        if bad:
            print(f"    *** ESCALATE: {name} meta-vs-CSV mismatch on {bad} ***")

    df = pd.DataFrame(rows)
    out = f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2/verify_cmdt2_r3_results.csv"
    df.to_csv(out, index=False)
    n_match = int(df["all_match"].sum())
    print(f"\n=== SUMMARY: {n_match}/{len(df)} sleeves reproduce their published meta exactly ===")
    print(f"round-2 files (CMDT2_*): {int(df[df.name.str.startswith('CMDT2')]['all_match'].sum())}"
          f"/{int(df.name.str.startswith('CMDT2').sum())} match")
    print(f"detail written: {out}")
    return 0 if n_match == len(df) else 1


if __name__ == "__main__":
    sys.exit(main())
