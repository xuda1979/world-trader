"""Probe SNB data portal internal JSON API: navigation tree -> cube list."""
import json, socket, urllib.request

socket.setdefaulttimeout(45)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

def hdr():
    h = dict(User_Agent=UA, Accept="application/json")
    h["X-EPB-ajax"] = "true"
    return h

def walk(node, path, found):
    t = node.get("title") or ""
    cid = node.get("cubeId") or ""
    ntype = node.get("type") or node.get("partType") or ""
    if cid or ntype == "cube":
        found.append((path[-70:], t, cid))
    kids = node.get("children") or node.get("topics") or node.get("parts") or []
    for c in kids:
        walk(c, path + "/" + t, found)

def main():
    u = "https://data.snb.ch/json/structure/getNavigationTree?lang=en"
    req = urllib.request.Request(u, headers=hdr())
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
    found = []
    if isinstance(d, dict):
        walk(d, "", found)
    print("cubes found:", len(found))
    for row in found:
        print(" | ".join(str(x) for x in row))

main()