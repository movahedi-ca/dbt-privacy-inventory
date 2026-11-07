#!/bin/bash
# run-nightly.sh — nightly dbt + DuckDB builder for dbt-privacy-inventory.
# Runs as the dbt-runner user on the Micro under a systemd timer (02:15 UTC).
# - Single-writer flock lock. Isolated run directory per UTC run ID.
# - DuckDB database file in work/ (never published).
# - Freeze artifacts, generate docs, scan, write an immutable release bundle.
# - NEVER deploy to the live site. Mode M: the bundle stages for owner review.
# - On any failure: no publish, no partial release, state.yaml updated.
set -u
BASE="${PRIVACY_DBT_BASE:-/opt/privacy-dbt}"
REPO="${REPO:-$BASE/repo}"
RUN_ID="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
RUN_DIR="$BASE/runs/$RUN_ID"
LOCK_FILE="$BASE/state/nightly.lock"
STATE="$BASE/state/state.yaml"
mkdir -p "$BASE/runs" "$BASE/state" "$BASE/releases"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "another nightly run is active; exiting" >&2
  exit 0
fi
echo "run $RUN_ID started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$RUN_DIR"
cd "$REPO" || exit 1
git fetch --quiet origin main 2>&1 | tail -1
git checkout --quiet main
git pull --ff-only --quiet origin main 2>&1 | tail -1
HEAD_SHA="$(git rev-parse HEAD)"
cp -r "$REPO" "$RUN_DIR/project"
cd "$RUN_DIR/project" || exit 1
cp profiles.yml.example profiles.yml
mkdir -p work
START="$(date +%s)"
dbt build > "$RUN_DIR/dbt-build.log" 2>&1
BUILD_RC=$?
dbt docs generate > "$RUN_DIR/dbt-docs.log" 2>&1
DOCS_RC=$?
END="$(date +%s)"
DURATION=$((END - START))
if [ $BUILD_RC -ne 0 ] || [ $DOCS_RC -ne 0 ]; then
  echo "run $RUN_ID FAILED build=$BUILD_RC docs=$DOCS_RC duration=${DURATION}s" >&2
  echo "release: none (build failed)" >> "$RUN_DIR/status.txt"
  exit 1
fi
# Freeze artifacts: manifest, catalog, run results, docs.
cp target/manifest.json "$RUN_DIR/manifest.json"
cp target/catalog.json "$RUN_DIR/catalog.json" 2>/dev/null || true
cp target/run_results.json "$RUN_DIR/run_results.json"
cp -r target "$RUN_DIR/target"
# Graph export (allowlist only; raw manifest never leaves the build plane).
python3 "$BASE/scripts/export_graph.py" \
  --manifest "$RUN_DIR/manifest.json" \
  --out "$RUN_DIR/public_graph.json"
python3 "$BASE/scripts/validate_bundle.py" --run-dir "$RUN_DIR" || exit 1
# Immutable release bundle with checksums.
RELEASE_ID="rel-$RUN_ID"
REL_DIR="$BASE/releases/$RELEASE_ID"
mkdir -p "$REL_DIR"
cp "$RUN_DIR/public_graph.json" "$REL_DIR/"
cp "$RUN_DIR/manifest.json" "$REL_DIR/manifest.json"
cp -r "$RUN_DIR/target" "$REL_DIR/target"
cp "$RUN_DIR/run_results.json" "$REL_DIR/"
python3 - "$REL_DIR" "$HEAD_SHA" "$RUN_ID" "$DURATION" << 'PYEOF'
import hashlib, json, sys, os
rel_dir, head_sha, run_id, duration = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
files = {}
for root, _, names in os.walk(rel_dir):
    for n in sorted(names):
        p = os.path.join(root, n)
        rel = os.path.relpath(p, rel_dir)
        h = hashlib.sha256()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        files[rel] = h.hexdigest()
release = {
    "release_id": "rel-" + run_id,
    "run_id": run_id,
    "created_utc": run_id,
    "head_sha": head_sha,
    "duration_seconds": int(duration),
    "files": files,
}
with open(os.path.join(rel_dir, 'release.json'), 'w') as f:
    json.dump(release, f, indent=2, sort_keys=True)
with open(os.path.join(rel_dir, 'checksums.sha256'), 'w') as f:
    for rel, h in sorted(files.items()):
        f.write(f"{h}  {rel}\n")
print("release rel-" + run_id + " written")
PYEOF
echo "{\"release_id\": \"rel-$RUN_ID\", \"head_sha\": \"$HEAD_SHA\", \"run_id\": \"$RUN_ID\", \"duration_seconds\": $DURATION}" > "$BASE/state/current.json"
echo "run $RUN_ID OK duration=${DURATION}s release=rel-$RUN_ID"
