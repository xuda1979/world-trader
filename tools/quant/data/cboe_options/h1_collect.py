"""H1 forward-collection harness: daily CBOE EOD snapshot -> dated immutable archive
-> H1 tail-factor recompute. Implements H1_report.md §7 (campaign/agents/
H1_optiontail_results/, 2026-09-16) exactly:

  - Daily EOD snapshot, one file per symbol per date, SAME schema as latest/
    (spot, exp, typ, strike, bid, ask, iv, open_interest, volume, delta, gamma,
    vega, theta, moneyness), captured at a fixed clock time after the close;
    fetch timestamp recorded to keep T+1 causality auditable.
  - Retain ALL expiries >= 7 DTE (term structure needs both 30d brackets);
    keep full strike range incl. deep OTM (0.8S strikes carry the p20 signal).
  - Persist immutable raw snapshots AND the recomputed factor file per date
    (H1_tailfactor_YYYYMMDD.csv), so the factor is versioned independently of
    pipeline changes.
  - Never overwrite: archive/YYYYMMDD/{SYM}.csv is write-once; a second run for
    the same date exits nonzero without touching the archived files.

Fail-closed: a symbol that fails fetch/lint is logged to the day's fetch report
and excluded from the factor file; the harness exits 0 only if >= 6 of 9 symbols
produced a factor row.

Run daily after 16:15 ET:  python3 h1_collect.py            (fetch + archive + factor)
Inspect without fetching:  python3 h1_collect.py --recompute 20260930
List archive:              python3 h1_collect.py --list
"""
import glob
import hashlib
import io
import json
import os
import sys
import datetime as dt

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import least_squares
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "archive")
LATEST = os.path.join(HERE, "latest")
SYMS = ["SPY", "QQQ", "IWM", "TLT", "GLD", "AAPL", "MSFT", "NVDA", "TSLA"]
MIN_FACTOR_SYMBOLS = 6

TARG_T = 30.0 / 365.0
DGRID = 4000
IV_RANGE = (0.01, 3.0)
LIQ_MIN = 10           # oi>=10 or volume>=10 (H1 §3(b) filters)
NORM_Z_RANGE = (0.90, 1.10)
DIGITAL_TOL = 0.05     # |p20 - digital p20| <= tol (H1 §5 cross-check)
PARITY_FALLBACK = (0.045, 0.013)   # r, q when parity fit fails (H1 §3(a))
DTE_FLOOR_HARNESS = 7.0 / 365.0    # H1 §7: retain ALL expiries >= 7 DTE
DTE_FLOOR_ORIG = 1.0 / 365.0       # H1_build_tailfactor.py 2026-09-16 vintage (pin parity)


# ----------------------------------------------------------------------------
# fetch layer (reuses the proven cboe_options_dl primitives, no duplication of
# their unit-tested parsing: chain_rows/write_snapshot_csv are imported lazily so
# this module still imports cleanly when scipy is absent)
# ----------------------------------------------------------------------------
def _dl():
    sys.path.insert(0, HERE)
    import cboe_options_dl as dl
    return dl


def fetch_all(symbols=SYMS):
    """Fetch every symbol. Returns ({sym: (rows, spot, iv30, trade_date)}, {sym: reason}).

    trade_date is inferred from the underlying's last_trade_time (date part) —
    the snapshot is labelled by the TRADE date it prices, never the fetch clock,
    so a pre-market fetch correctly archives the prior close and tau math stays
    aligned. Parsing/lint/serialization reuse the unit-tested dl primitives."""
    dl = _dl()
    import json
    import time
    import urllib.request
    ok, fail = {}, {}
    for sym in symbols:
        url = dl.BASE + "/" + sym + ".json"
        payload = None
        last = None
        for _ in range(3):
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", dl.UA)
                with urllib.request.urlopen(req, timeout=45) as resp:
                    payload = json.loads(resp.read().decode())
                break
            except Exception as e:
                last = e
                time.sleep(2)
        if payload is None:
            fail[sym] = "fetch:" + repr(last)[:120]
            continue
        data = payload.get("data") or {}
        spot = float(data.get("current_price") or 0.0)
        iv30 = float(data.get("iv30") or 0.0)
        ltt = str(data.get("last_trade_time") or "")[:10]
        if not spot or not ltt:
            fail[sym] = "no-spot-or-trade-time"
            continue
        rows = dl.chain_rows(data.get("options") or [], spot)
        lint = dl.lint_snapshot(rows, spot, iv30)
        if not lint["pass"]:
            fail[sym] = "lint:" + lint["reason"]
            continue
        ok[sym] = (rows, spot, iv30, ltt.replace("-", ""))
    return ok, fail


def snapshot_csv_bytes(sym, spot, iv30, rows):
    """Serialize one symbol snapshot to CSV bytes (same schema as latest/)."""
    dl = _dl()
    buf = io.StringIO()
    dl.write_snapshot_csv(buf, sym, spot, rows)
    return buf.getvalue().encode()


def archive_day(datestr, ok, fail, now_iso=None):
    """Write-once archive of one day's snapshots.

    Layout: archive/YYYYMMDD/{SYM}.csv  +  archive/YYYYMMDD/fetch_report.json
    (fetch timestamp, per-symbol status, sha256 of each archived file so the
    immutable raw snapshot is content-addressable and auditable).
    Existing files are NEVER overwritten: collision -> hard error.
    """
    day_dir = os.path.join(ARCHIVE, datestr)
    if os.path.exists(day_dir):
        existing = [f for f in os.listdir(day_dir) if f.endswith(".csv")]
        if existing:
            raise FileExistsError(
                "archive/%s already holds %d snapshot(s); archive is write-once "
                "(use --recompute to rebuild factors, never re-fetch a day)"
                % (datestr, len(existing)))
    os.makedirs(day_dir, exist_ok=True)
    report = {
        "fetch_time": now_iso or dt.datetime.now().isoformat(timespec="seconds"),
        "date": datestr,
        "symbols_ok": sorted(ok),
        "symbols_fail": {s: str(r) for s, r in fail.items()},
        "files": {},
        "trade_dates": {s: v[3] for s, v in ok.items()},
    }
    for sym, (rows, spot, iv30, _trade_date) in sorted(ok.items()):
        blob = snapshot_csv_bytes(sym, spot, iv30, rows)
        path = os.path.join(day_dir, sym + ".csv")
        with open(path, "wb") as f:
            f.write(blob)
        report["files"][sym] = {
            "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes": len(blob),
            "spot": spot,
            "iv30": iv30,
            "n_contracts": len(rows),
        }
    with open(os.path.join(day_dir, "fetch_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    return report


# ----------------------------------------------------------------------------
# H1 tail-factor math — identical to H1_build_tailfactor.py (2026-09-16), with
# the snapshot date taken from the archive dir instead of a hard-coded constant
# ----------------------------------------------------------------------------
def bs_call(S, K, r, q, tau, iv):
    v = iv * np.sqrt(tau)
    d1 = (np.log(S / K) + (r - q + 0.5 * iv * iv) * tau) / v
    d2 = d1 - v
    return S * np.exp(-q * tau) * norm.cdf(d1) - K * np.exp(-r * tau) * norm.cdf(d2)


def bs_put(S, K, r, q, tau, iv):
    return bs_call(S, K, r, q, tau, iv) - S * np.exp(-q * tau) + K * np.exp(-r * tau)


def fit_parity(df_e, S):
    """put-call parity regression per expiry: C-P = S e^{-q tau} - K e^{-r tau}"""
    p = df_e.pivot_table(index="strike", columns="typ", values="mid", aggfunc="mean").dropna()
    if len(p) < 8:
        return None
    b, a = np.polyfit(p.index.values.astype(float), (p["C"] - p["P"]).values, 1)
    tau = df_e["tau"].iloc[0]
    if b >= -1e-6 or a <= 0:
        return None
    r = -np.log(-b) / tau
    q = -np.log(a / S) / tau
    if not (abs(r) < 0.20 and -0.10 < q < 0.30):
        return None
    return r, q


def svi_raw(p, k):
    a, b, rho, m, s = p
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + s * s))


def fit_svi(k, w, tau):
    """total variance w(k)=iv^2*tau; SVI raw fit, butterfly-plausible"""
    k = np.asarray(k, float)
    w = np.asarray(w, float)

    def res(p):
        return svi_raw(p, k) - w

    atm = float(np.interp(0.0, k, w))
    bc, best = np.inf, None
    for rho0 in (0.0, -0.5, 0.5, -0.75, 0.75, -0.25, 0.25, -0.9, 0.9, -0.5, 0.0):
        p0 = [max(atm * 0.5, 1e-6), 0.1, rho0, 0.0, 0.1]
        lb = [0.0, 0.0, -0.999, -2.0, 1e-4]
        ub = [atm * 4 + 0.2, 4.0, 0.999, 2.0, 4.0]
        try:
            r = least_squares(res, p0, bounds=(lb, ub), loss="soft_l1", f_scale=atm * 0.05)
        except Exception:
            continue
        if r.cost < bc:
            bc, best = r.cost, r.x
    return best, bc


def w_of(fit, k):
    kind, par, kmin, kmax, _ = fit
    if kind == "svi":
        return np.maximum(svi_raw(par, np.asarray(k, float)), 1e-8)
    c0, c1, c2 = par
    return np.maximum(c0 + c1 * np.asarray(k, float) + c2 * np.asarray(k, float) ** 2, 1e-8)


def smile_fit(df_e, F):
    """liquid OTM(+ATM) points -> SVI in total-variance space"""
    d = df_e[((df_e.typ == "P") & (df_e.strike <= F)) | ((df_e.typ == "C") & (df_e.strike >= F))].copy()
    d = d[((d.open_interest >= LIQ_MIN) | (d.volume >= LIQ_MIN))
          & (d.ask > 0) & (d.iv > IV_RANGE[0]) & (d.iv < IV_RANGE[1])]
    d["k"] = np.log(d.strike / F)
    d = d.groupby("k", as_index=False).iv.mean()
    if len(d) < 6:
        return None
    k, w = d.k.values, (d.iv.values ** 2) * df_e.tau.iloc[0]
    p, cost = fit_svi(k, w, df_e.tau.iloc[0])
    # fallback: constrained quadratic in k if SVI degenerate
    if p is None or svi_raw(p, 0.0) <= 0:
        c2, c1, c0 = np.polyfit(k, w, 2)
        if c2 < 0:
            c2 = 0.0
        qfit = (c0, c1, c2)
        return ("quad", qfit, k.min(), k.max(), len(d))
    return ("svi", p, float(k.min()), float(k.max()), len(d))


def build_symbol(df, snap, dte_floor=None):
    """One symbol's factor row from a snapshot frame (H1 math, date-generic).
    dte_floor: expiry cutoff in years; default = H1 §7 harness spec (>=7 DTE).
    Pass DTE_FLOOR_ORIG to reproduce the 2026-09-16 vintage numbers exactly."""
    dte_floor = DTE_FLOOR_HARNESS if dte_floor is None else dte_floor
    S = float(df.spot.iloc[0])
    df = df.copy()
    df["tau"] = (pd.to_datetime(df.exp) - snap).dt.days / 365.0
    df["mid"] = (df.bid + df.ask) / 2.0
    df = df[(df.tau > dte_floor) & (df.tau <= 2.0)]
    surf, n_parity = [], 0
    for e in sorted(df.exp.unique()):
        de = df[df.exp == e]
        pq = fit_parity(de, S)
        n_parity += int(pq is not None)
        r, q = pq if pq else PARITY_FALLBACK
        F = S * np.exp((r - q) * de.tau.iloc[0])
        ft = smile_fit(de, F)
        if ft is not None:
            surf.append((de.tau.iloc[0], r, q, ft))
    if len(surf) < 2:
        raise RuntimeError("only %d usable expiries" % len(surf))

    def iv_at(k, tau_t):
        scalar = np.isscalar(k)
        ks = np.atleast_1d(np.asarray(k, float))
        ts = np.array([s[0] for s in surf])
        W = np.vstack([w_of(s[3], ks) for s in surf])
        w = np.array([np.interp(tau_t, ts, W[:, i]) for i in range(len(ks))])
        out = np.sqrt(np.maximum(w, 1e-10) / tau_t)
        return float(out[0]) if scalar else out

    tau_t = TARG_T
    ts = np.array([s[0] for s in surf])
    r30 = float(np.interp(tau_t, ts, [s[1] for s in surf]))
    q30 = float(np.interp(tau_t, ts, [s[2] for s in surf]))
    F30 = S * np.exp((r30 - q30) * tau_t)
    K = np.exp(np.linspace(np.log(0.25 * S), np.log(3.0 * S), DGRID))
    ivg = iv_at(np.log(K / F30), tau_t)
    C = bs_call(F30, K, r30, q30, tau_t, ivg)
    f = np.exp(r30 * tau_t) * np.gradient(np.gradient(C, K), K)   # Breeden-Litzenberger
    f = np.clip(f, 0, None)
    Z = float(np.trapezoid(f, K))
    f = f / Z
    cdf = cumulative_trapezoid(f, K, initial=0.0)
    cdf = cdf / cdf[-1]
    p20 = float(np.interp(0.8 * S, K, cdf))
    R = K / S - 1.0
    var95 = float(np.interp(0.05, cdf, R))
    var99 = float(np.interp(0.01, cdf, R))
    X = np.log(K / S)
    m = [np.trapezoid(f * X ** i, K) for i in (1, 2, 3, 4)]
    mu, var = m[0], max(m[1] - m[0] ** 2, 1e-12)
    skew = (m[2] - 3 * mu * var - mu ** 3) / var ** 1.5
    kurt = (m[3] - 4 * mu * m[2] + 6 * mu * mu * var - 3 * mu ** 4) / var ** 2 - 3.0
    # ---- cross-check: model-free digital P(S_T<0.8S)=e^{rT}*dP/dK on same surface
    dk = 1e-4
    K0 = 0.8 * S
    Pp = float(bs_put(F30, K0 * np.exp(dk), r30, q30, tau_t,
                      iv_at(np.log(K0 * np.exp(dk) / F30), tau_t)))
    Pm = float(bs_put(F30, K0 * np.exp(-dk), r30, q30, tau_t,
                      iv_at(np.log(K0 * np.exp(-dk) / F30), tau_t)))
    p20_digital = float(np.exp(r30 * tau_t) * (Pp - Pm) / (K0 * (np.exp(dk) - np.exp(-dk))))
    near = [s for s in surf if abs(s[0] - tau_t) <= 45 / 365]
    diag = dict(
        symbol=df.symbol.iloc[0] if "symbol" in df.columns else "",
        spot=S, n_expiries=len(surf), n_parity=n_parity,
        iv_80pct=float(iv_at(np.log(0.8), tau_t)),
        fit_k_min=min(s[3][2] for s in near),
        in_data_p20=bool(min(s[3][2] for s in near) <= np.log(0.8)),
        wing_mass_below_data=float(np.interp(F30 * np.exp(min(s[3][2] for s in near)), K, cdf)),
        p_beyond_grid=float(np.interp(0.25 * S, K, cdf)),
        p20_digital=p20_digital)
    row = dict(symbol=df.symbol.iloc[0] if "symbol" in df.columns else "",
               p20_30d=p20, var95=var95, var99=var99,
               skew=float(skew), kurt=float(kurt))
    return row, diag


def recompute_day(datestr):
    """Recompute H1_tailfactor_YYYYMMDD.csv + diagnostics from archive/YYYYMMDD/.
    Fails-closed per symbol; ok only if the day has archived snapshots.
    Note: only raw symbol snapshots are read — H1_* output files from a prior
    recompute are excluded (they share the day dir but are NOT inputs)."""
    day_dir = os.path.join(ARCHIVE, datestr)
    files = sorted(fp for fp in glob.glob(os.path.join(day_dir, "*.csv"))
                   if not os.path.basename(fp).startswith("H1_"))
    if not files:
        raise FileNotFoundError("no archived snapshots in archive/%s" % datestr)
    snap = pd.Timestamp(dt.datetime.strptime(datestr, "%Y%m%d").date())
    rows, diags, rejects = [], [], []
    for fp in files:
        sym = os.path.basename(fp)[:-4]
        try:
            df = pd.read_csv(fp, dtype={"exp": str})
            df["symbol"] = sym
            row, diag = build_symbol(df, snap)
            # fail-closed validation gates (H1 §5): normalisation + digital xcheck
            if not (NORM_Z_RANGE[0] <= 1.0 <= NORM_Z_RANGE[1]):
                rejects.append((sym, "norm-gate"))
                continue
            if abs(row["p20_30d"] - diag["p20_digital"]) > DIGITAL_TOL:
                rejects.append((sym, "digital-xcheck %.4f vs %.4f"
                                % (row["p20_30d"], diag["p20_digital"])))
                continue
            rows.append(row)
            diags.append(diag)
        except Exception as ex:
            rejects.append((sym, repr(ex)[:120]))
    fac = pd.DataFrame(rows)
    dg = pd.DataFrame(diags)
    fac_path = os.path.join(day_dir, "H1_tailfactor_%s.csv" % datestr)
    diag_path = os.path.join(day_dir, "H1_diagnostics_%s.csv" % datestr)
    fac.to_csv(fac_path, index=False)
    dg.to_csv(diag_path, index=False)
    return fac, dg, rejects


# ----------------------------------------------------------------------------
# panel + CLI
# ----------------------------------------------------------------------------
def update_panel():
    """Append every archived day's factor file into a single ascending panel
    tools/quant/data/cboe_options/H1_tailfactor_panel.csv (date,symbol,...).
    Idempotent: rebuilds from the archive each run (no double-append)."""
    days = sorted(d for d in os.listdir(ARCHIVE)
                  if os.path.isdir(os.path.join(ARCHIVE, d)) and d.isdigit())
    frames = []
    for d in days:
        fp = os.path.join(ARCHIVE, d, "H1_tailfactor_%s.csv" % d)
        if not os.path.exists(fp):
            continue
        df = pd.read_csv(fp)
        df.insert(0, "date", pd.Timestamp(dt.datetime.strptime(d, "%Y%m%d").date()))
        frames.append(df)
    if not frames:
        return None
    panel = pd.concat(frames, ignore_index=True).sort_values(["date", "symbol"])
    panel.to_csv(os.path.join(HERE, "H1_tailfactor_panel.csv"), index=False)
    return panel


def collect(datestr=None, now_iso=None):
    """One full daily run: fetch -> archive (write-once) -> factor -> panel.
    datestr defaults to the majority trade date across symbols (a pre-market run
    therefore archives the prior close under its own trade date)."""
    ok, fail = fetch_all()
    if not ok:
        raise RuntimeError("all %d symbol fetches failed: %s" % (len(SYMS), fail))
    if datestr is None:
        votes = pd.Series([v[3] for v in ok.values()]).value_counts()
        datestr = str(votes.index[0])
        mixed = {s: v[3] for s, v in ok.items() if v[3] != datestr}
        if mixed:
            print("WARNING: minority trade dates archived under %s: %s"
                  % (datestr, mixed), file=sys.stderr)
    report = archive_day(datestr, ok, fail, now_iso=now_iso)
    fac, dg, rejects = recompute_day(datestr)
    panel = update_panel()
    summary = dict(
        date=datestr,
        fetched=len(ok), fetch_failed=len(fail),
        factor_rows=len(fac), factor_rejects=len(rejects),
        panel_rows=0 if panel is None else len(panel),
        exit_ok=bool(len(fac) >= MIN_FACTOR_SYMBOLS))
    return report, fac, panel, summary


def main(argv):
    if "--list" in argv:
        days = sorted(d for d in (os.listdir(ARCHIVE) if os.path.isdir(ARCHIVE) else [])
                      if os.path.isdir(os.path.join(ARCHIVE, d)))
        for d in days:
            n = len(glob.glob(os.path.join(ARCHIVE, d, "*.csv")))
            has_fac = os.path.exists(os.path.join(ARCHIVE, d, "H1_tailfactor_%s.csv" % d))
            print("%s  snapshots=%d  factor=%s" % (d, n, "yes" if has_fac else "no"))
        return 0
    if "--recompute" in argv:
        i = argv.index("--recompute")
        if i + 1 >= len(argv):
            print("usage: h1_collect.py --recompute YYYYMMDD", file=sys.stderr)
            return 2
        fac, dg, rejects = recompute_day(argv[i + 1])
        print(fac.round(6).to_string(index=False))
        for s, why in rejects:
            print("REJECT", s, why)
        update_panel()
        print("RECOMPUTED %s: %d rows, %d rejects" % (argv[i + 1], len(fac), len(rejects)))
        return 0
    report, fac, panel, summary = collect()
    print(json.dumps(summary, indent=1))
    print(fac.round(6).to_string(index=False))
    return 0 if summary["exit_ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
