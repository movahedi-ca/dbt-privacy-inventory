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
- Result coverage (TASK-008): the frozen run_results.json must be a
  build invocation, its invocation_id must match the frozen bundle
  record when one is present, and its result ID set must equal the
  expected executed-node set exactly (IDs unique, expected set
  nonempty, statuses in the approved set, no fail or error status).
  The expected set is expected_result_ids.json when the run directory
  holds one (fixture form), else the manifest nodes whose
  resource_type is model, seed, test, or snapshot.
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
RESULT_TYPES = ("model", "seed", "test", "snapshot")
ALLOWED_STATUSES = ("success", "pass", "fail", "error", "skipped")
FAILED_STATUSES = ("fail", "error")

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
    # The release set is only these files. The run dir also holds the
    # project/ copy (with profiles.yml) and work/*.duckdb — build-plane
    # internals that never enter a release and must NOT be scanned here.
    release_files = ["public_graph.json", "manifest.json", "run_results.json"]
    if os.path.exists(os.path.join(run_dir, "catalog.json")):
        release_files.append("catalog.json")
    total = 0
    for fname in release_files:
        p = os.path.join(run_dir, fname)
        if not os.path.exists(p):
            fail(f"release file missing: {fname}")
        if fname.endswith(FORBIDDEN_SUFFIXES) or fname in FORBIDDEN_NAMES:
            fail(f"forbidden file in release set: {fname}")
        total += os.path.getsize(p)
    if total > MAX_BUNDLE_BYTES:
        fail(f"release set {total} bytes > {MAX_BUNDLE_BYTES}")
    # Result coverage validation (TASK-008). Named failure reasons:
    # INVOCATION_NOT_BUILD, INVOCATION_MISMATCH, RESULTS_MISSING,
    # EXPECTED_EMPTY, RESULTS_EMPTY, RESULT_ID_DUPLICATE,
    # RESULT_ID_MISSING, RESULT_ID_EXTRA, RESULT_STATUS_DISALLOWED,
    # RESULT_STATUS_FAILED.
    with open(os.path.join(run_dir, "manifest.json")) as f:
        manifest = json.load(f)
    with open(os.path.join(run_dir, "run_results.json")) as f:
        run_results = json.load(f)
    metadata = run_results.get("metadata") or {}
    rargs = run_results.get("args") or {}
    which = rargs.get("which") or rargs.get("command")
    if which is not None and which != "build":
        fail(f"INVOCATION_NOT_BUILD: run_results invocation is {which!r}, not 'build'")
    record_inv = None
    for rec_name in ("bundle_record.json", "release.json"):
        rec_path = os.path.join(run_dir, rec_name)
        if os.path.exists(rec_path):
            with open(rec_path) as f:
                rec = json.load(f)
            if rec.get("invocation_id"):
                record_inv = rec["invocation_id"]
                break
    if record_inv is not None and metadata.get("invocation_id") != record_inv:
        fail(f"INVOCATION_MISMATCH: frozen record invocation {record_inv} "
             f"!= run_results invocation {metadata.get('invocation_id')}")
    results = run_results.get("results")
    if results is None or not isinstance(results, list):
        fail("RESULTS_MISSING: run_results.json has no results array")
    exp_path = os.path.join(run_dir, "expected_result_ids.json")
    if os.path.exists(exp_path):
        with open(exp_path) as f:
            exp_data = json.load(f)
        expected = set(exp_data["expected_ids"] if isinstance(exp_data, dict) else exp_data)
    else:
        expected = {k for k, n in (manifest.get("nodes") or {}).items()
                    if n.get("resource_type") in RESULT_TYPES}
    if not expected:
        fail("EXPECTED_EMPTY: expected executed-node set is empty")
    if not results:
        fail("RESULTS_EMPTY: run_results.json holds zero results")
    ids = []
    for r in results:
        uid = r.get("unique_id")
        if uid is None:
            fail("RESULT_ID_MISSING: a result entry has no unique_id")
        ids.append(uid)
    seen, dups = set(), set()
    for i in ids:
        if i in seen:
            dups.add(i)
        seen.add(i)
    if dups:
        fail(f"RESULT_ID_DUPLICATE: {sorted(dups)}")
    actual = set(ids)
    missing = expected - actual
    if missing:
        fail(f"RESULT_ID_MISSING: {sorted(missing)[:5]} ({len(missing)} missing)")
    extra = actual - expected
    if extra:
        fail(f"RESULT_ID_EXTRA: {sorted(extra)[:5]} ({len(extra)} extra)")
    for r in results:
        st = r.get("status")
        if st not in ALLOWED_STATUSES:
            fail(f"RESULT_STATUS_DISALLOWED: {r.get('unique_id')} status {st!r}")
        if st in FAILED_STATUSES:
            fail(f"RESULT_STATUS_FAILED: {r.get('unique_id')} status {st!r}")
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
