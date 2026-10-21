import io, os, re, urllib.request, zipfile
import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
UA = {'User-Agent': 'Mozilla/5.0'}
OUT = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/factors"
os.makedirs(OUT, exist_ok=True)

def fetch(name):
    url = BASE + name + ".zip"
    req = urllib.request.Request(url, headers=UA)
    d = urllib.request.urlopen(req, timeout=40).read()
    z = zipfile.ZipFile(io.BytesIO(d))
    return z.read(z.namelist()[0]).decode()

def parse_table(txt, token):
    lines = [ln.replace("\r", "") for ln in txt.split("\n")]
    hdr = None
    for i, ln in enumerate(lines):
        if token in ln and "," in ln:
            hdr = i; break
    assert hdr is not None, f"header not found: {token}"
    raw = lines[hdr].split(",")
    # first token is usually empty (date col)
    cols = []
    if raw[0].strip() == "":
        cols = ["Date"] + [c.strip() for c in raw[1:] if c.strip()]
    rows = []
    j = hdr + 1
    while j < len(lines):
        parts = lines[j].split(",")
        if parts and re.match(r"^\d{6}$", parts[0].strip()):
            rows.append([p.strip() for p in parts])
        j += 1
    df = pd.DataFrame(rows, columns=cols)
    df["date"] = pd.to_datetime(df["Date"], format="%Y%m")
    for c in cols:
        if c not in ("Date", "date"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def main():
    t = fetch("F-F_Research_Data_5_Factors_2x3_CSV")
    ff5 = parse_table(t, "Mkt-RF")
    ff5.to_csv(os.path.join(OUT, "ff5_factors.csv"), index=False)
    print("FF5:", ff5.shape, ff5["date"].min().date(), "->", ff5["date"].max().date())

    t = fetch("10_Portfolios_Prior_12_2_CSV")
    pm = parse_table(t, "Lo PRIOR")
    # columns have "Lo PRIOR" ... "Hi PRIOR"; build momentum via first/last
    vw = [c for c in pm.columns if c not in ("Date", "date")]
    mom = pd.DataFrame({"date": pm["date"],
                        "MOM": (pm[vw[-1]] - pm[vw[0]]).astype(float).values})
    mom.to_csv(os.path.join(OUT, "momentum_factor.csv"), index=False)
    print("MOM:", mom.shape, mom["date"].min().date(), "->", mom["date"].max().date())

if __name__ == "__main__":
    main()
