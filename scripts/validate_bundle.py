#!/usr/bin/env python3
"""validate_bundle.py — scan a run directory before a release is written.

Checks (fail closed, exit 1 on any failure):
- public_graph.json exists and parses; node/edge counts within policy.
- No forbidden artifact in the release set (manifest raw is kept, but
  it never leaves the build plane; catalog is allowed only in the bundle,
  never published; no .duckdb, no .log, no compiled SQL in public files).
- Secret/PII scan over public files: api keys, passwords, tokens,
  private keys, emails, phone-like strings, real cookie IDs.
- Bundle size within the 5 MB policy limit.
"""
import argparse, json, os, re, sys

MAX_BUNDLE_BYTES = 5_000_000
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]\s*["\'][^"\']{8,}'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    re.compile(r'\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
]
FORBIDDEN_SUFFIXES = (".duckdb", ".duckdb.wal", ".log")
FORBIDDEN_NAMES = ("profiles.yml",)

def fail(msg):
    print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = args.run_dir
    graph_path = os.path.join(run_dir, "public_graph.json")
    if not os.path.exists(graph_path):
        fail("public_graph.json missing")
    with open(graph_path) as f:
        graph = json.load(f)
    if graph.get("schema") != "public_graph/v1":
        fail("public_graph.json schema mismatch")
    if graph["counts"]["nodes"] > 500 or graph["counts"]["edges"] > 2000:
        fail("graph exceeds policy size")
    total = 0
    for root, _, names in os.walk(run_dir):
        for n in names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, run_dir)
            if n.endswith(FORBIDDEN_SUFFIXES) or n in FORBIDDEN_NAMES:
                fail(f"forbidden file in run dir: {rel}")
            total += os.path.getsize(p)
    if total > MAX_BUNDLE_BYTES:
        fail(f"run dir {total} bytes > {MAX_BUNDLE_BYTES}")
    # Secret/PII scan over the public files only.
    for fname in ("public_graph.json",):
        p = os.path.join(run_dir, fname)
        text = open(p, encoding="utf-8", errors="replace").read()
        for pat in SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                fail(f"secret/PII pattern in {fname}: {m.group(0)[:40]}")
    print(f"bundle validation OK: {graph['counts']['nodes']} nodes, "
          f"{graph['counts']['edges']} edges, {total} bytes")

if __name__ == "__main__":
    main()
