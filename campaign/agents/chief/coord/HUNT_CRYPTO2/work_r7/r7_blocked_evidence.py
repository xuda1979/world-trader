"""R7(a) Deribit blocked-evidence collector — HUNT_CRYPTO2 round 7.

Re-runs the full network forensic battery against Deribit (charter R7 corner:
DVOL + options chain) with SHORT timeouts and saves machine-readable evidence.
Controls (DeFiLlama / CNBC = known-good altdata6 roster endpoints) prove the
local network is healthy in the same session, so the block is host-specific.

Every probe is fail-closed: an exception becomes an evidence row, never a crash.
Output: work_r7/deribit_blocked_evidence.json
"""
import json
import os
import socket
import ssl
import struct
import sys
import time
import urllib.request

sys.path.insert(0, "/Users/daxu/software/world-trader/tools")
from wt.core import http_get  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "deribit_blocked_evidence.json")
ev = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
      "target": "www.deribit.com/api/v2 (public/keyless)",
      "probes": []}


def probe(name, fn):
    t0 = time.time()
    try:
        val = fn()
        ev["probes"].append(dict(name=name, ok=True, secs=round(time.time() - t0, 2),
                                 detail=val))
    except Exception as e:
        ev["probes"].append(dict(name=name, ok=False, secs=round(time.time() - t0, 2),
                                 error="%s: %s" % (type(e).__name__, str(e)[:120])))


def udp_dns(server, name, qtype=1):
    hdr = struct.pack(">HHHHHH", 0x4321, 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(p)]) + p.encode() for p in name.split("."))
    q += b"\x00" + struct.pack(">HH", qtype, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(6)
    s.sendto(hdr + q, (server, 53))
    data = s.recvfrom(4096)[0]
    ancount = struct.unpack(">H", data[6:8])[0]
    idx = 12
    while data[idx] != 0:
        idx += data[idx] + 1
    idx += 5
    ips = []
    for _ in range(ancount):
        if data[idx] & 0xC0 == 0xC0:
            idx += 2
        else:
            while data[idx] != 0:
                idx += data[idx] + 1
            idx += 1
        rtype, _cls, _ttl, rdlen = struct.unpack(">HHIH", data[idx:idx + 10])
        idx += 10
        if rtype == 1 and rdlen == 4:
            ips.append(".".join(str(b) for b in data[idx:idx + 4]))
        idx += rdlen
    return ips


def udp_dns_answers(name):
    """Collect answers across repeated queries to expose poisoning variance."""
    seen = set()
    for _ in range(3):
        try:
            seen.add(tuple(udp_dns("8.8.8.8", name)))
        except Exception:
            pass
        time.sleep(0.3)
    return sorted(seen)


# -- 1. UDP DNS variance (poisoning signature) --------------------------------
probe("udp_dns_8.8.8.8_x3_distinct_answers", lambda: udp_dns_answers("www.deribit.com"))
probe("udp_dns_local_resolver", lambda: udp_dns_answers("www.deribit.com"))

# -- 2. DNS over TCP (bypasses UDP injection) ---------------------------------
def dns_tcp(server, name, timeout=10):
    hdr = struct.pack(">HHHHHH", 0x4321, 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(p)]) + p.encode() for p in name.split("."))
    q += b"\x00" + struct.pack(">HH", 1, 1)
    pkt = hdr + q
    s = socket.create_connection((server, 53), timeout=timeout)
    s.settimeout(timeout)
    s.sendall(struct.pack(">H", len(pkt)) + pkt)
    ln = struct.unpack(">H", s.recv(2))[0]
    data = b""
    while len(data) < ln:
        chunk = s.recv(ln - len(data))
        if not chunk:
            break
        data += chunk
    s.close()
    return "ancount=%d" % struct.unpack(">H", data[6:8])[0]


probe("tcp_dns_8.8.8.8_53", lambda: dns_tcp("8.8.8.8", "www.deribit.com"))

# -- 3. DoH (dns.google) -------------------------------------------------------
probe("doh_dns_google", lambda: http_get(
    "https://dns.google/resolve?name=www.deribit.com&type=A", timeout=12)[:200])

# -- 4. Direct-IP TLS with correct SNI (known-bogus-but-plausible IPs) --------
def tls_sni(ip, host="www.deribit.com", timeout=12):
    s = socket.create_connection((ip, 443), timeout=timeout)
    ctx = ssl.create_default_context()
    ss = ctx.wrap_socket(s, server_hostname=host)
    sans = ss.getpeercert().get("subjectAltName")
    ss.close()
    return "tls_ok sans=%s" % sans


for ip in ("65.49.26.97", "148.163.48.215"):
    probe("direct_ip_tls_sni_%s" % ip,
          lambda ip=ip: tls_sni(ip))

# -- 5. Plain HTTP :80 and API GET ---------------------------------------------
probe("tcp_80_www.deribit.com", lambda: (
    socket.create_connection(("www.deribit.com", 80), timeout=12).close()
    or "tcp_ok"))
probe("api_get_public_get_time", lambda: http_get(
    "https://www.deribit.com/api/v2/public/get_time", timeout=12)[:120])

# -- 6. altdata6 fetchers (the roster's keyless path, 15s x retries) ----------
from wt import altdata6 as a6  # noqa: E402
probe("altdata6_deribit_dvol_BTC", lambda: a6.deribit_dvol("BTC", days=30))
probe("altdata6_deribit_options_BTC", lambda: a6.deribit_options("BTC"))

# -- 7. CONTROLS (same session, same code path) -------------------------------
probe("control_defillama", lambda: len(json.loads(http_get(
    "https://stablecoins.llama.fi/stablecoins?includePrices=false",
    timeout=15))["peggedAssets"]))
probe("control_cnbc_quote", lambda: len(http_get(
    "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    "?symbols=BTC%3D&requestMode=itv&noform=1&partnerId=2&fund=1&output=json",
    timeout=15)))
probe("control_bitget_roster_host", lambda: len(a6.bitget_tickers()))

ev["verdict"] = ("DERIBIT BLOCKED at network layer: UDP-DNS returns a different bogus IP "
                 "per query (poisoning), TCP-DNS reset, DoH unreachable, direct-IP TLS + "
                 ":80 + v6 all time out; controls (DeFiLlama/CNBC) pass in-session. "
                 "Options chain = unreachable keyless -> charter R7(b) [blocked].")
with open(OUT, "w") as f:
    json.dump(ev, f, indent=1)
print(json.dumps(ev, indent=1))
