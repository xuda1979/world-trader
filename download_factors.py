"""Download FREE Kenneth French factors (5-factor + momentum) for alpha regressions."""
import io, os, re, urllib.request, zipfile
import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
UA = {'User-Agent': 'Mozilla/5.0'}
OUT = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/factors"
os.makedirs(OUT, exist_ok=True)


def fetch_csv(name):
    url = BASE + name + ".zip"
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=40).read()
    z = zipfile.ZipFile(io.BytesIO(data))
    return z.read(z.namelist()[0]).decode()


def parse_table(txt, header_col):
    """Return DataFrame from KF CSV: locate header line containing header_col."""
    lines = txt.split("\n")
    hdr = None
    for i, ln in enumerate(lines):
        if header_col in ln and "," in ln:
            hdr = i
            break
    assert hdr is not None, f"header '{header_col}' not found"
    cols = [c.strip() for c in lines[hdr].split(",") if c.strip()]
    rows = []
    j = hdr + 1
    while j < len(lines):
        parts = lines[j].split(",")
        if parts and re.match(r"^\d{6}$", parts[0].strip()):
            rows.append([p.strip() for p in parts])
        j += 1
    df = pd.DataFrame(rows, columns=cols)
    df["date"] = pd.to_datetime(df[df.columns[0]], format="%Y%m")
    for c in cols[1:]:
        if c and c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def main():
    # 5 factors
    txt = fetch_csv("F-F_Research_Data_5_Factors_2x3_CSV")
    ok = False
    try:
        ff5 = parse_table(txt, "Mkt-RF")
        ff5.to_csv(os.path.join(OUT, "ff5_factors.csv"), index=False)
        print("FF5:", ff5.shape, ff5["date"].min(), "->", ff5["date"].max())
        ok = True
    except Exception as e:
        print("FF5 parse failed:", str(e)[:100])
    # momentum 10 portfolios (value-weighted) -> build UMD = Hi - Lo
    txt = fetch_csv("10_Portfolios_Prior_12_2_CSV")
    try:
        pm = parse_table(txt, "Average Value Weighted Returns")
        # columns: date, lo priOR ... hi priOR
        vw = pm.loc[:, [c for c in pm.columns if c not in ("date",) and pm[c].dtype != "datetime64[ns]"]]
        lo = vw.iloc[:, 0].astype(float)
        hi = vw.iloc[:, -1].astype(float)
        umd = pd.DataFrame({"date": pm["date"], "MOM": (hi - lo).values})
        umd.to_csv(os.path.join(OUT, "momentum_factor.csv"), index=False)
        print("MOM:", umd.shape, umd["date"].min(), "->", umd["date"].max())
    except Exception as e:
        import traceback; traceback.print_exc()
        print("MOM parse failed:", str(e)[:120])


if __name__ == "__main__":
    main()
