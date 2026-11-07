#!/usr/bin/env python3
"""extract_api_snapshot.py — deterministic read-only Privacy API shadow extractor.

Fetches the six Privacy API families from GitHub main (the canonical source),
records the commit SHA + per-file SHA-256, counts records per family, and
compares against the live /api/v1/health counts (parity report).
Read-only: the VM never writes to the serving API. Snapshots are NOT
committed to the repo until the license/redistribution review is done
(owner decision; V3-J). The parity report is the P7 evidence artifact.
Usage: python3 extract_api_snapshot.py --out <dir>
"""
import argparse, hashlib, json, re, subprocess, sys, urllib.request

REPO = "movahedi-ca/movahedi-ca"
RAW = "https://raw.githubusercontent.com/movahedi-ca/movahedi-ca/main/"
HEALTH = "https://movahedi.ca/api/v1/health"

FILES = {
    "data.ts": "workers/public-api/src/api/data.ts",
    "cookie-kb.ts": "src/data/cookie-kb.ts",
    "crawlers.json": "src/data/crawlers.json",
    "glossary.ts": "src/data/glossary.ts",
    "cai-enforcement.json": "src/data/cai-enforcement.json",
}

# (family, file, constant, key field)
FAMILIES = [
    ("glossary_terms", "data.ts", "GLOSSARY_TERMS", "slug"),
    ("enforcement_actions", "data.ts", "ENFORCEMENT_ACTIONS", "id"),
    ("law25_checks", "data.ts", "LAW25_CHECKLIST", "id"),
    ("cookie_patterns", "data.ts", "COOKIE_PATTERNS", "pattern"),
    ("crawlers", "data.ts", "CRAWLERS", "token"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dbt-privacy-inventory/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def extract_array(source, const):
    """Extract the array literal assigned to `export const NAME = [...]`
    (or `const NAME = [...]`) and count its top-level elements by bracket
    depth. Returns (count, array_text) or (None, None)."""
    m = re.search(r"(?:export\s+)?const\s+" + re.escape(const) + r"\s*=\s*\[", source)
    if not m:
        return None, None
    i = m.end() - 1
    depth = 0
    in_str = None
    esc = False
    start = i
    for j in range(i, len(source)):
        c = source[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
            continue
        if c in ("'", '"', "`"):
            in_str = c
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                body = source[start + 1:j]
                # Count top-level elements: commas at depth 0 within the array.
                d = 0
                s = None
                e = False
                commas = 0
                nonempty = body.strip() != ""
                for k, ch in enumerate(body):
                    if s:
                        if e:
                            e = False
                        elif ch == "\\":
                            e = True
                        elif ch == s:
                            s = None
                        continue
                    if ch in ("'", '"', "`"):
                        s = ch
                    elif ch in ("[", "{"):
                        d += 1
                    elif ch in ("]", "}"):
                        d -= 1
                    elif ch == "," and d == 0:
                        commas += 1
                return (commas + 1) if nonempty else 0, source[start:j + 1]
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--snapshot-dir", default=None,
                    help="Local dir holding data.ts, cookie-kb.ts, crawlers.json, "
                         "glossary.ts, cai-enforcement.json + manifest.json. "
                         "The Micro cannot fetch the private site repo directly; "
                         "the snapshot is fetched where GitHub auth lives and "
                         "transferred frozen, with SHA-256 verified here.")
    args = ap.parse_args()
    import os
    os.makedirs(args.out, exist_ok=True)
    if args.snapshot_dir:
        snap_manifest = json.load(open(os.path.join(args.snapshot_dir, "manifest.json")))
        head_sha = snap_manifest["head_sha"]
        blobs = {}
        for name, path in FILES.items():
            with open(os.path.join(args.snapshot_dir, name), "rb") as f:
                data = f.read()
            got = sha256(data)
            want = snap_manifest["files"][name]["sha256"]
            if got != want:
                print(f"SHA MISMATCH {name}: got {got} want {want}", file=sys.stderr)
                sys.exit(3)
            blobs[name] = {"path": path, "bytes": len(data), "sha256": got, "text": data.decode("utf-8", errors="replace")}
            print(f"verified {name}: {len(data)} bytes sha256={got[:16]}...")
    else:
        # Commit SHA from ls-remote (no clone needed).
        ls = subprocess.run(["git", "ls-remote", f"https://github.com/{REPO}.git", "refs/heads/main"],
                            capture_output=True, text=True, timeout=30)
        head_sha = ls.stdout.split()[0] if ls.returncode == 0 and ls.stdout else "UNKNOWN"
        blobs = {}
        for name, path in FILES.items():
            data = fetch(RAW + path)
            blobs[name] = {"path": path, "bytes": len(data), "sha256": sha256(data), "text": data.decode("utf-8", errors="replace")}
            print(f"fetched {name}: {len(data)} bytes sha256={blobs[name]['sha256'][:16]}...")
    data_ts = blobs["data.ts"]["text"]
    # Live counts from the health endpoint.
    health = json.loads(fetch(HEALTH).decode("utf-8"))
    live = {
        "glossary_terms": health.get("glossary_terms") or health.get("glossary"),
        "enforcement_actions": health.get("enforcement_actions"),
        "law25_checks": health.get("law25_checks"),
        "cookie_patterns": health.get("cookie_patterns"),
        "crawlers": health.get("crawlers"),
    }
    families = []
    for fam, fname, const, key in FAMILIES:
        count, _ = extract_array(data_ts, const)
        live_count = live.get(fam)
        families.append({
            "family": fam,
            "source_file": FILES[fname],
            "constant": const,
            "key_field": key,
            "snapshot_count": count,
            "live_count": live_count,
            "match": (count == live_count) if (count is not None and live_count is not None) else None,
        })
        print(f"{fam}: snapshot={count} live={live_count} match={families[-1]['match']}")
    # Vendor KB: derived from cookie-kb.ts (vendor/legalParty dimension).
    kb = blobs["cookie-kb.ts"]["text"]
    vendors = set(re.findall(r"vendor\s*:\s*['\"]([^'\"]+)['\"]", kb))
    families.append({
        "family": "vendor_knowledge_base",
        "source_file": FILES["cookie-kb.ts"],
        "constant": "NONE (derived from COOKIE_PATTERNS vendor/legalParty)",
        "key_field": "vendor / legalParty",
        "snapshot_count": len(vendors),
        "live_count": None,
        "match": None,
        "note": "distinct vendor values in cookie-kb.ts",
    })
    print(f"vendor_knowledge_base: distinct vendors={len(vendors)}")
    report = {
        "schema": "api_snapshot_parity/v1",
        "repo": REPO,
        "head_sha": head_sha,
        "files": {n: {"path": v["path"], "bytes": v["bytes"], "sha256": v["sha256"]} for n, v in blobs.items()},
        "families": families,
        "license_review": "NOT CHECKED (owner decision before inclusion)",
    }
    out = os.path.join(args.out, "api_snapshot_parity.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(f"parity report written: {out}")
    mismatches = [f["family"] for f in families if f.get("match") is False]
    if mismatches:
        print(f"PARITY MISMATCH: {mismatches}", file=sys.stderr)
        sys.exit(2)
    print("parity: all compared families match")

if __name__ == "__main__":
    main()
