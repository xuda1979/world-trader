"""probe_pcr_refresh_r5.py — R5 charter (b): ONE honest attempt to refresh the CBOE PCR
archive past its 2019-10-04 freeze, from CURRENT CBOE CDN paths.

R3/R4 precedent (probe_pcr_live.py in tools/quant/data/cboe_pcr/): modern
delayed_quotes PCR endpoints 403 AccessDenied; legacy daily CSV 404; the 10 official
archive CSVs HTTP 200 but FROZEN upstream. This probe adds paths R3/R4 did NOT try,
plus a re-discovery sweep of CBOE's own historical_data page for any new/updated link.
Charter: if blocked -> log exact HTTP evidence and STOP. No scraping workarounds,
no synthetic substitutes. Reports only; exit 0 always.

Run:  python3 probe_pcr_refresh_r5.py    (from DATA_COTMORE/work_r5/)
"""
import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "/Users/daxu/software/world-trader/tools/quant/data/cboe_pcr/_raw"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (research; world-trader free-data harvest)"


def fetch(url, nread=400):
    """(status, content_type, head_text, full_body_or_None). HTTPError -> its status."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "text/csv,application/json,text/html,*/*")
    try:
        r = urllib.request.urlopen(req, timeout=45, context=CTX)
        head = r.read(nread)
        rest = r.read()
        return r.status, r.headers.get("Content-Type"), head.decode("utf-8", "replace"), head + rest
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), e.read(nread).decode("utf-8", "replace"), None
    except Exception as e:                                    # noqa: BLE001
        return None, None, f"{type(e).__name__}: {e}", None


def main():
    out = []

    # 1) control: known-good CSV on the same CDN proves the path is open (probe void if not)
    st, ct, head, _ = fetch("https://cdn.cboe.com/api/global/us_indices/daily_prices/"
                            "VIX_History.csv")
    out.append(dict(step="1_control", url="cdn.../us_indices/daily_prices/VIX_History.csv",
                    status=st, content_type=ct, head=head[:100]))
    assert st == 200, "control fetch failed - network path broken, probe void"

    # 2) current-day PCR API variants NOT probed in R3/R4
    api_paths = [
        "https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/_all.json",
        "https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/history.json",
        "https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/SPX.json",
        "https://cdn.cboe.com/api/global/delayed_quotes/pc_ratio/_all.json",
        "https://cdn.cboe.com/api/global/delayed_quotes/market_stats/put_call_ratio.json",
        "https://cdn.cboe.com/api/global/us_options/put_call_ratios/_all.json",
    ]
    for i, u in enumerate(api_paths, start=2):
        st, ct, head, _ = fetch(u)
        out.append(dict(step=f"{i}_api_variant", url=u, status=st, content_type=ct,
                        head=head[:160]))

    # 3) re-discovery: CBOE's own historical-data page - any link changed/added vs R3?
    st, ct, _, body = fetch("https://www.cboe.com/us/options/market_statistics/historical_data/",
                            nread=0)
    links = sorted(set(re.findall(rb'href="([^"]+\.csv)"', body or b"")))
    out.append(dict(step="3_historical_page", status=st, n_csv_links=len(links),
                    links=[l.decode().split("/")[-1] for l in links][:30]))

    # 4) byte-compare totalpc.csv (the frozen one that matters) against live CDN
    comp = []
    for f in ("totalpc.csv", "equitypc.csv", "spxpc.csv"):
        st, ct, _, b = fetch("https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/"
                             + f, nread=0)
        with open(os.path.join(RAW, f), "rb") as fh:
            lb = fh.read()
        comp.append(dict(file=f, status=st,
                         remote_sha16=hashlib.sha256(b).hexdigest()[:16] if b else None,
                         local_sha16=hashlib.sha256(lb).hexdigest()[:16],
                         identical=bool(b) and hashlib.sha256(b).digest() ==
                         hashlib.sha256(lb).digest(),
                         remote_rows=(b.count(b"\n") if b else None),
                         local_rows=(lb.count(b"\n"))))
    out.append(dict(step="4_archive_byte_compare", files=comp))

    # 5) also probe the US-index daily page for an equities PCR (different path family)
    st, ct, head, _ = fetch("https://www.cboe.com/us/options/market_statistics/daily/")
    out.append(dict(step="5_daily_page", status=st, content_type=ct, head=head[:120]))

    print(json.dumps(out, indent=1))
    ident = all(c["identical"] for c in comp)
    blocked = all(o.get("status") in (403, 404, None) for o in out
                  if str(o.get("step", "")).endswith("_api_variant"))
    print(f"\nVERDICT: api_variants_blocked={blocked} archive_byte_identical={ident}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
