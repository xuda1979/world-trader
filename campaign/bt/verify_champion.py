#!/usr/bin/env python3
"""bt/verify_champion.py — re-emit ACCEPTANCE TOOL (AUDIT_RECON round 3).

Independent acceptance gate for a champion CSV. Verifies a (champion_csv, weights_csv,
sleeve CSVs) triple WITHOUT importing any engine internals — only the builder arithmetic
(rawew13v2 recipe) is mirrored here, in this file's own algebra:

  1. weights_repro       committed relw == max(IS_SR,0)^P from the sleeves themselves.
  2. byte_repro          champion net series rebuilds exactly from sleeves + relw
                         (nav-drift weights, nav.shift(1) causal, FULL |dW| x bps with
                         day-1 entry NOT charged, margin (gear-1)*rate/252).
  3. cost_reconciliation cost implied by the champion series == FULL |dW| x bps computed
                         from the weights (own algebra, NOT engine.cost_turnover). A
                         half-turn book diagnoses as model="half_dw".
  4. causality           champion matches the nav.shift(1) rebuild and NOT the same-day
                         (leaky) rebuild; plus truncation-invariance (zero all sleeve
                         returns from probe day t onward -> Wg_t byte-identical).
  5. gross               daily gross <= gear, both from the rebuilt weights and from the
                         financing charge embedded in the champion series (a book whose
                         weights are 1.6x but which charges 1.7x margin diagnoses here).
  6. yearly              0 negative years (champion bar) and worst year > -5%.
                         (GATES_CONTRACT (d) new-sleeve variant reported alongside.)
  7. mdd                 max drawdown >= mdd_limit (GOAL100 goal: -7%).

Exit code 0/1, JSON report, fail-closed on any missing/mismatched input.

Usage:
  python3 campaign/bt/verify_champion.py \
      --champion campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv \
      --weights campaign/results/RAWEW13v2_IS_SR_weights.csv \
      --sleeve brwt15=campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv \
      --sleeve ... [--is-end 2017-01-01] [--p 0.55] [--start 2008-03-31] \
      [--gear 1.6] [--rate 0.045] [--bps 6.4] [--mdd-limit -0.07] [--json rep.json]

--is-end omitted -> inferred from a fixed candidate grid (must reproduce relw exactly);
the inferred value is reported. Everything else defaults to the committed recipe.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

# Recipe constants (rawew13v2_build.py). Overridable on the CLI; is_end is inferred when
# not given because the mini-champion fixtures use a different IS cutoff than the
# committed champion and the tool must accept both without flag drift.
DEFAULT_START = "2008-03-31"
DEFAULT_P = 0.55
DEFAULT_GEAR = 1.6
DEFAULT_RATE = 0.045
DEFAULT_BPS = 6.4
DEFAULT_MDD_LIMIT = -0.07
IS_END_GRID = [f"{y}-{m}-01" for y in range(2010, 2021) for m in (1, 7)]
TOL = 1e-12
RELW_TOL = 1e-9
TRUNC_TOL = 1e-15


# ---------------------------------------------------------------- loading (fail-closed)
def _load_ret(path, label, errors):
    """Load a [date,ret] csv -> float Series. Any problem lands in `errors` (fail-closed)."""
    if not os.path.exists(path):
        errors.append(f"missing {label} input: {path}")
        return None
    try:
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index)
    except Exception as exc:  # unreadable / malformed
        errors.append(f"unreadable {label} input {path}: {exc}")
        return None
    return _ret_from_frame(df, label, path, errors)


def _load_weights(path, label, errors):
    """Load a [name,relw] csv (name-indexed, NOT dates) -> float Series. Fail-closed."""
    if not os.path.exists(path):
        errors.append(f"missing {label} input: {path}")
        return None
    try:
        df = pd.read_csv(path, index_col=0)
    except Exception as exc:
        errors.append(f"unreadable {label} input {path}: {exc}")
        return None
    return _ret_from_frame(df, label, path, errors)


def _ret_from_frame(df, label, path, errors):
    col = "ret" if "ret" in df.columns else df.columns[0]
    if col not in df.columns:
        errors.append(f"no usable column in {label} input: {path}")
        return None
    s = df[col].astype(float)
    # NaN is BUILDER-LEGITIMATE (rawew13v2_build.load() dropna()s per series; arithmetic
    # fillna(0)s inside the frame — the real brwt* sleeve files carry 59 NaNs each), so
    # only inf/+inf is corruption here. NaNs flow through the mirrored arithmetic below
    # exactly as they do in the builder.
    if np.isinf(s.to_numpy()).any():
        errors.append(f"non-finite (inf) values in {label} input: {path}")
        return None
    s.name = label
    return s


def _is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


# ------------------------------------------------- builder arithmetic (own algebra)
def _build_frame(sleeves, names, start):
    """Outer-align dropna'd sleeve series (columns in `names` order), filter >= start.
    Mirrors rawew13v2_build.build(): NO inner-join dropna — missing values stay NaN and
    are fillna(0)-ed only inside the nav/port arithmetic, exactly like the builder."""
    df = pd.DataFrame({n: sleeves[n] for n in names})
    return df[df.index >= pd.Timestamp(start)]


def _relw_from(df, is_end, p):
    isr = df[df.index < pd.Timestamp(is_end)]
    return pd.Series({n: max(_is_sr(isr[n]), 0.0) ** p for n in df.columns})


def _weights_from(df, relw, causal=True):
    """nav-drift weights x relw, row-normalized to sum K, scaled to gross.
    causal=True -> nav.shift(1) (T+1, the R1 re-emit mechanism); False -> same-day leak."""
    nav = (1 + df.fillna(0)).cumprod()
    if causal:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    return d2 * (1.0 / len(relw))  # caller multiplies by gear via _net_from? no: keep raw


def _weights_gear(df, relw, gear, causal=True):
    W = _weights_from(df, relw, causal=causal)
    return W * gear


def _net_from(df, W, bps, rate, gear):
    """net = port - FULL|dW|*bps - (gear-1)*rate/252, day-1 entry NOT charged."""
    port = (df.fillna(0).values * W.values).sum(axis=1)
    to = W.diff().abs().sum(axis=1).fillna(0.0)
    return (pd.Series(port, index=df.index) - to * bps / 1e4
            - max(gear - 1, 0) * rate / 252), to


# ---------------------------------------------------------------- checks
def verify_champion(champion_csv, weights_csv, sleeve_paths, is_end=None, p_param=DEFAULT_P,
                    start=DEFAULT_START, gear=DEFAULT_GEAR, rate=DEFAULT_RATE,
                    bps=DEFAULT_BPS, mdd_limit=DEFAULT_MDD_LIMIT, tol=TOL,
                    truncation_probes=None):
    """Verify a champion triple independently of engine internals. Returns (ok, report)."""
    rep = {"tool": "bt/verify_champion.py", "ok": False, "errors": [], "checks": {}}
    errors = rep["errors"]

    # -- fail-closed inputs --------------------------------------------------------
    if not sleeve_paths:
        errors.append("missing sleeve inputs: no --sleeve name=path given")
        return False, rep
    champ = _load_ret(champion_csv, "champion", errors)
    wr = _load_weights(weights_csv, "weights", errors)
    sleeves, missing = {}, []
    for name, path in sleeve_paths.items():
        s = _load_ret(path, f"sleeve {name}", errors)
        if s is None:
            missing.append(name)
        else:
            sleeves[name] = s
    if champ is None or wr is None or missing:
        return False, rep
    if wr.isna().any() or (wr <= 0).all():
        errors.append("weights csv is empty / all non-positive — fail-closed")
        return False, rep
    names = list(wr.index)
    unknown = [n for n in names if n not in sleeves]
    if unknown:
        errors.append(f"missing sleeve input(s) for weights rows: {unknown}")
        return False, rep
    extra = [n for n in sleeves if n not in names]
    if extra:
        rep["warnings"] = [f"sleeve inputs not in weights csv (ignored): {extra}"]
    relw = wr.copy()
    relw.index = names

    df = _build_frame(sleeves, names, start)
    if len(df) == 0:
        errors.append(f"sleeve inputs empty after start filter {start} — fail-closed")
        return False, rep
    if (df.dropna(how="all").index != df.index).any() and df.isna().all(axis=1).any():
        errors.append("all-NaN rows in aligned sleeve frame — fail-closed")
        return False, rep

    # -- 1. weights_repro ----------------------------------------------------------
    inferred = {"is_end": is_end, "inferred": False}
    if is_end is None:
        cands, dev_by = [], {}
        for cand in IS_END_GRID:
            r = _relw_from(df, cand, p_param)
            if len(r) != len(relw):
                continue
            cands.append(cand)
            dev_by[cand] = float((r - relw).abs().max())
        good = [c for c in cands if dev_by[c] < RELW_TOL]
        if not good:
            best = min(cands, key=lambda c: dev_by[c]) if cands else None
            rep["checks"]["weights_repro"] = {
                "ok": False, "inferred_is_end": None,
                "max_dev": dev_by.get(best), "tol": RELW_TOL,
                "detail": "no IS-end candidate reproduces committed relw — "
                          "pass --is-end explicitly if this book uses one outside "
                          f"{IS_END_GRID[0]}..{IS_END_GRID[-1]}",
            }
            return False, rep
        inferred["is_end"], inferred["inferred"] = good[0], True
        is_end = good[0]
    rep["is_end"] = {"value": str(pd.Timestamp(is_end).date()), "inferred": inferred["inferred"],
                     "p": p_param, "start": start}
    r_rebuild = _relw_from(df, is_end, p_param)
    wdev = float((r_rebuild - relw).abs().max())
    rep["checks"]["weights_repro"] = {"ok": bool(wdev < RELW_TOL), "max_dev": wdev,
                                      "tol": RELW_TOL}

    # -- rebuild the weight path + net series (causal and same-day) -----------------
    W_c = _weights_gear(df, relw, gear, causal=True)
    W_s = _weights_gear(df, relw, gear, causal=False)
    net_c, to = _net_from(df, W_c, bps, rate, gear)
    net_s, _ = _net_from(df, W_s, bps, rate, gear)

    # -- champion series alignment (fail-closed on date mismatch) -------------------
    j = pd.concat([champ.rename("csv"), net_c.rename("rebuild")], axis=1, join="inner")
    if len(j) != len(champ) or len(j) != len(net_c) or not j.index.equals(champ.index):
        errors.append(f"date index mismatch: champion n={len(champ)} rebuild n={len(net_c)} "
                      f"inner={len(j)} — fail-closed")
        return False, rep

    # -- 2. byte_repro ---------------------------------------------------------------
    bdev = float((j["csv"] - j["rebuild"]).abs().max())
    rep["checks"]["byte_repro"] = {"ok": bool(bdev < tol), "max_dev": bdev, "tol": tol}

    # -- 3. cost_reconciliation (FULL |dW| from the weights themselves) --------------
    port = pd.Series((df.fillna(0).values * W_c.values).sum(axis=1), index=df.index)
    margin = max(gear - 1, 0) * rate / 252
    cost_implied = port - j["csv"] - margin          # what the csv must have charged
    cost_full = to * bps / 1e4                        # full |dW| x bps (own algebra)
    cost_half = 0.5 * cost_full
    dev_full = float((cost_implied - cost_full).abs().max())
    dev_half = float((cost_implied - cost_half).abs().max())
    denom = float(cost_full.sum())
    ratio = float(cost_implied.sum() / denom) if denom > 1e-18 else float("nan")
    if dev_full < tol:
        model = "full_dw"
    elif dev_half < tol:
        model = "half_dw"
    else:
        model = "unknown"
    cok = model == "full_dw" and (np.isnan(ratio) or abs(ratio - 1.0) < 1e-6)
    rep["checks"]["cost_reconciliation"] = {
        "ok": bool(cok), "model": model, "max_dev": dev_full, "max_dev_half": dev_half,
        "implied_over_full_ratio": ratio, "tol": tol,
        "charged_bp_sum": float(cost_implied.sum() * 1e4),
        "bp_per_year": float(cost_implied.mean() * 252 * 1e4),
        "turnover_full_dw_bp_per_year": float(to.mean() * 252 * bps),
        "day1_entry_charged": float(cost_implied.iloc[0] * 1e4),
    }

    # -- 4. causality (weights == f(nav.shift(1))) ----------------------------------
    causal_dev = float((j["csv"] - j["rebuild"]).abs().max())
    sameday_dev = float((j["csv"] - net_s.reindex(j.index)).abs().max())
    # Which mechanism does the CSV actually follow? (min deviation; both are reported.)
    mech = "causal" if causal_dev <= sameday_dev else "same_day"
    # Truncation-invariance under the MATCHED mechanism: zero all sleeve returns from
    # probe day t onward and rebuild — a causal weight path at t is unchanged; a
    # same-day (leaky) path moves (it consumed r_t), so the probe has teeth there too.
    probes = truncation_probes or [0, 1, 2, len(df) // 4, len(df) // 2,
                                   3 * len(df) // 4, len(df) - 1]
    W_mech = W_c if mech == "causal" else W_s
    tdev, trunc_detail = 0.0, []
    for t in probes:
        dfz = df.copy()
        dfz.iloc[t:] = 0.0                      # zero returns from probe day onward
        Wt = _weights_gear(dfz, relw, gear, causal=(mech == "causal"))
        d = float((Wt.iloc[t] - W_mech.iloc[t]).abs().max())
        trunc_detail.append({"t": int(t), "date": str(df.index[t].date()), "dev": d})
        tdev = max(tdev, d)
    trunc_ok = tdev < TRUNC_TOL
    rep["checks"]["causality"] = {
        "ok": bool(mech == "causal" and causal_dev < tol and trunc_ok),
        "mechanism": "nav.shift(1)",
        "matched_mechanism": mech,
        "causal_max_dev": causal_dev, "sameday_max_dev": sameday_dev, "tol": tol,
        "truncation": {"ok": bool(trunc_ok), "n_probes": len(probes), "max_dev": tdev,
                       "tol": TRUNC_TOL, "probes": trunc_detail},
    }

    # -- 5. gross (weights AND financing-implied) -----------------------------------
    gross = W_c.abs().sum(axis=1)
    resid = port - j["csv"] - cost_full             # == margin if book is consistent
    margin_hat = float(resid.median())
    fin_gross = pd.Series(1.0 + resid * 252.0 / rate if rate > 0 else 1.0, index=df.index)
    gmax_w = float(gross.max())
    gmax_f = float(fin_gross.max())
    n_over = int((fin_gross > gear + 1e-9).sum()) + int((gross > gear + 1e-9).sum())
    rep["checks"]["gross"] = {"ok": bool(gmax_w <= gear + 1e-9 and gmax_f <= gear + 1e-9),
                              "limit": gear, "max": max(gmax_w, gmax_f),
                              "weights_max": gmax_w, "financing_implied_max": gmax_f,
                              "margin_implied_pct_yr": margin_hat * 252 * 100,
                              "margin_expected_pct_yr": margin * 252 * 100,
                              "n_over": n_over}

    # -- 6. yearly gates (champion bar: 0 neg; contract (d) variant reported) --------
    yr = j["csv"].groupby(j["csv"].index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]
    contract_d_ok = bool(len(neg) <= 2 and (len(neg) == 0 or neg.min() > -0.05))
    champion_ok = bool(len(neg) == 0 and (len(neg) == 0 or neg.min() > -0.05))
    rep["checks"]["yearly"] = {"ok": champion_ok, "neg_years": int(len(neg)),
                               "worst_year": float(yr.min()) if len(yr) else None,
                               "neg_by_year": {int(k): float(v) for k, v in neg.items()},
                               "gates_contract_d_new_sleeve_ok": contract_d_ok}

    # -- 7. mdd ----------------------------------------------------------------------
    nav = (1 + j["csv"]).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    rep["checks"]["mdd"] = {"ok": bool(mdd >= mdd_limit), "mdd": mdd, "limit": mdd_limit}

    # -- stats ------------------------------------------------------------------------
    s = j["csv"]
    rep["stats"] = {
        "n_days": int(len(s)), "start": str(s.index[0].date()), "end": str(s.index[-1].date()),
        "ann_arith_pct": float(s.mean() * 252 * 100),
        "ann_cagr_pct": float(((1 + s).prod() ** (252 / len(s)) - 1) * 100),
        "sr": float(s.mean() / s.std(ddof=1) * np.sqrt(252)),
        "mdd_pct": mdd * 100, "neg_years": int(len(neg)),
    }
    rep["inputs"] = {"champion": champion_csv, "weights": weights_csv,
                     "sleeves": dict(sleeve_paths)}
    rep["params"] = {"gear": gear, "rate": rate, "bps": bps, "p": p_param, "start": start,
                     "tol": tol, "truncation_probes": list(probes)}
    rep["ok"] = bool(all(v["ok"] for v in rep["checks"].values()) and not errors)
    return rep["ok"], rep


# ---------------------------------------------------------------- CLI
def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    # tolerate "--sleeve name=path" arriving as ONE argv element (subprocess list form)
    expanded = []
    for tok in raw:
        if tok.startswith("--sleeve "):
            expanded += ["--sleeve", tok[len("--sleeve "):]]
        else:
            expanded.append(tok)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--champion", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--sleeve", action="append", default=[],
                    help="name=path/to/sleeve.csv (repeat for every slot)")
    ap.add_argument("--is-end", default=None)
    ap.add_argument("--p", dest="p_param", type=float, default=DEFAULT_P)
    ap.add_argument("--start", default=DEFAULT_START)
    ap.add_argument("--gear", type=float, default=DEFAULT_GEAR)
    ap.add_argument("--rate", type=float, default=DEFAULT_RATE)
    ap.add_argument("--bps", type=float, default=DEFAULT_BPS)
    ap.add_argument("--mdd-limit", type=float, default=DEFAULT_MDD_LIMIT)
    ap.add_argument("--json", dest="json_path", default=None)
    a = ap.parse_args(expanded)
    sleeves = {}
    for tok in a.sleeve:
        if "=" not in tok:
            print(f"bad --sleeve token (want name=path): {tok}", file=sys.stderr)
            return 2
        n, p = tok.split("=", 1)
        sleeves[n] = p
    is_end = pd.Timestamp(a.is_end) if a.is_end else None
    try:
        ok, rep = verify_champion(a.champion, a.weights, sleeves, is_end=is_end,
                                  p_param=a.p_param, start=a.start, gear=a.gear,
                                  rate=a.rate, bps=a.bps, mdd_limit=a.mdd_limit)
    except Exception as exc:  # never traceback past the gate: fail closed
        ok, rep = False, {"tool": "bt/verify_champion.py", "ok": False,
                          "errors": [f"exception during verification: {exc!r}"],
                          "checks": {}}
    out = json.dumps(rep, indent=2, default=str)
    if a.json_path:
        with open(a.json_path, "w") as fh:
            fh.write(out + "\n")
    print(out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
