#!/bin/bash
# run-nightly.sh — nightly dbt + DuckDB builder for dbt-privacy-inventory.
# Runs as the dbt-runner user on the Micro under a systemd timer (02:15 UTC).
# - Single-writer flock lock. A held lock exits 75 with a SKIPPED record.
# - Source is pinned: the checkout HEAD must equal the approved SHA in
#   config/approved-source.sha in the deployed tree, or the run stops.
# - DuckDB database file in work/ (never published).
# - Freeze artifacts immediately after the build, before any docs step.
#   Docs generation uses its own target path and never overwrites them.
# - Releases are staged privately and renamed into releases/ only when
#   complete and validated. Release creation is exclusive: a collision
#   fails the run.
# - Every run writes one structured JSON record to the state directory.
# - NEVER deploy to the live site. Mode M: the bundle stages for owner review.
# - On any failure: no publish, no partial release, structured record written.
set -euo pipefail
# dbt lives in the dbt-runner uv tool bin. Non-interactive shells do not
# carry ~/.local/bin on PATH, so set it explicitly (do not rely on login).
export PATH="/opt/privacy-dbt/.local/bin:$HOME/.local/bin:$PATH"
BASE="${PRIVACY_DBT_BASE:-/opt/privacy-dbt}"
REPO="${REPO:-$BASE/repo}"
RUN_ID="${RUN_ID:-$(date -u +%Y-%m-%dT%H-%M-%SZ)}"
SLOT="$RUN_ID"
RUN_DIR="$BASE/runs/$RUN_ID"
LOCK_FILE="$BASE/state/nightly.lock"
RECORD_DIR="$BASE/state"
RECORD_FILE="$RECORD_DIR/run-$RUN_ID.json"
PIN_FILE="${APPROVED_SHA_FILE:-$BASE/config/approved-source.sha}"
RELEASE_ID="rel-$RUN_ID"
REL_DIR="$BASE/releases/$RELEASE_ID"
STAGE_DIR="$BASE/releases/.staging-$RELEASE_ID"
START_EPOCH="$(date +%s)"
SOURCE_SHA=""
INVOCATION_ID=""
NODE_COUNT=""
EDGE_COUNT=""

record_json() {
  # record_json <result> <failure_class_or_empty>
  local result="$1" class="$2" duration now
  duration=$(( $(date +%s) - START_EPOCH ))
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local nodes_json="null" edges_json="null" inv_json="null" class_json="null" rel_json="null"
  [ -n "$NODE_COUNT" ] && nodes_json="$NODE_COUNT"
  [ -n "$EDGE_COUNT" ] && edges_json="$EDGE_COUNT"
  [ -n "$INVOCATION_ID" ] && inv_json="\"$INVOCATION_ID\""
  [ -n "$class" ] && class_json="\"$class\""
  [ "$result" = "OK" ] && rel_json="\"$RELEASE_ID\""
  printf '{"slot": "%s", "run_id": "%s", "release_id": %s, "source_sha": "%s", "invocation_id": %s, "nodes": %s, "edges": %s, "result": "%s", "failure_class": %s, "duration_seconds": %s, "recorded_utc": "%s"}\n' \
    "$SLOT" "$RUN_ID" "$rel_json" "$SOURCE_SHA" "$inv_json" "$nodes_json" "$edges_json" \
    "$result" "$class_json" "$duration" "$now" > "$RECORD_FILE"
}

fail() {
  # fail <class> <message>: classified record, staging removed, exit 1.
  local class="$1" msg="$2"
  echo "run $RUN_ID FAILED class=$class $msg" >&2
  record_json "FAILED" "$class" || true
  if [ -d "$STAGE_DIR" ]; then
    rm -rf "$STAGE_DIR"
  fi
  exit 1
}

mkdir -p "$BASE/runs" "$BASE/state" "$BASE/releases"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "another nightly run is active; skipping slot $SLOT" >&2
  record_json "SKIPPED_LOCK" "" || true
  exit 75
fi
echo "run $RUN_ID started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ ! -e "$REL_DIR" ] || fail "RELEASE_COLLISION" "release already exists: $REL_DIR"

# Source pin: read the approved SHA and verify the checkout against it.
[ -f "$PIN_FILE" ] || fail "SOURCE_PIN_MISSING" "pin file not found: $PIN_FILE"
APPROVED_SHA="$(tr -d '[:space:]' < "$PIN_FILE")"
case "$APPROVED_SHA" in
  *[!0-9a-f]*|"") fail "SOURCE_PIN_INVALID" "pin file does not hold a hex SHA" ;;
esac
[ "${#APPROVED_SHA}" -eq 40 ] || fail "SOURCE_PIN_INVALID" "pin SHA length ${#APPROVED_SHA} != 40"

mkdir -p "$RUN_DIR"
cd "$REPO" || fail "SOURCE_CHECKOUT" "cannot cd to repo $REPO"
git fetch --quiet origin main || fail "SOURCE_FETCH" "git fetch failed"
git checkout --quiet "$APPROVED_SHA" || fail "SOURCE_CHECKOUT" "git checkout of approved SHA failed"
HEAD_SHA="$(git rev-parse HEAD)" || fail "SOURCE_CHECKOUT" "git rev-parse failed"
SOURCE_SHA="$HEAD_SHA"
[ "$HEAD_SHA" = "$APPROVED_SHA" ] || fail "SOURCE_PIN_MISMATCH" "HEAD $HEAD_SHA != approved $APPROVED_SHA"
DIRTY="$(git status --porcelain)" || fail "SOURCE_CHECKOUT" "git status failed"
[ -z "$DIRTY" ] || fail "SOURCE_DIRTY" "working tree is not clean after checkout"

cp -r "$REPO" "$RUN_DIR/project" || fail "SNAPSHOT_FAILED" "repo snapshot copy failed"
cd "$RUN_DIR/project" || fail "SNAPSHOT_FAILED" "cannot cd to snapshot"
cp profiles.yml.example profiles.yml || fail "SNAPSHOT_FAILED" "profiles copy failed"
mkdir -p work

# Build. --write-catalog: dbt-oss writes no catalog.json by default
# (2.0.8 fixed `dbt build --write-catalog` to write target/catalog.json).
BUILD_RC=0
dbt build --write-catalog > "$RUN_DIR/dbt-build.log" 2>&1 || BUILD_RC=$?
[ "$BUILD_RC" -eq 0 ] || fail "BUILD_FAILED" "dbt build exited $BUILD_RC"

# Freeze step: immediately after the build, before any docs invocation.
# The frozen copies are the only artifacts the bundle is built from.
mkdir "$STAGE_DIR" || fail "STAGING_COLLISION" "staging dir already exists: $STAGE_DIR"
cp target/manifest.json "$STAGE_DIR/manifest.json" || fail "FREEZE_FAILED" "manifest freeze copy failed"
cp target/run_results.json "$STAGE_DIR/run_results.json" || fail "FREEZE_FAILED" "run_results freeze copy failed"
cp target/catalog.json "$STAGE_DIR/catalog.json" || fail "FREEZE_FAILED" "catalog freeze copy failed (build must run with --write-catalog)"
cp "$STAGE_DIR/manifest.json" "$RUN_DIR/manifest.json" || fail "FREEZE_FAILED" "manifest run-dir copy failed"
cp "$STAGE_DIR/run_results.json" "$RUN_DIR/run_results.json" || fail "FREEZE_FAILED" "run_results run-dir copy failed"
cp "$STAGE_DIR/catalog.json" "$RUN_DIR/catalog.json" || fail "FREEZE_FAILED" "catalog run-dir copy failed"
INVOCATION_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["metadata"]["invocation_id"])' "$STAGE_DIR/run_results.json")" \
  || fail "FREEZE_FAILED" "cannot read invocation_id from frozen run_results.json"
[ -n "$INVOCATION_ID" ] || fail "FREEZE_FAILED" "frozen run_results.json has an empty invocation_id"
printf '{"invocation_id": "%s", "source_sha": "%s", "run_id": "%s"}\n' \
  "$INVOCATION_ID" "$SOURCE_SHA" "$RUN_ID" > "$RUN_DIR/bundle_record.json" \
  || fail "FREEZE_FAILED" "bundle record write failed"

# Docs step, isolated: its own target path. Its outputs land in
# docs-target/ and never overwrite the frozen target/ artifacts.
DOCS_RC=0
dbt docs generate --target-path docs-target > "$RUN_DIR/dbt-docs.log" 2>&1 || DOCS_RC=$?
[ "$DOCS_RC" -eq 0 ] || fail "DOCS_FAILED" "dbt docs generate exited $DOCS_RC"

# Graph export from the frozen manifest (allowlist only; the raw
# manifest never leaves the build plane).
python3 "$BASE/scripts/export_graph.py" \
  --manifest "$STAGE_DIR/manifest.json" \
  --out "$RUN_DIR/public_graph.json" || fail "EXPORT_FAILED" "graph export failed"
python3 "$BASE/scripts/validate_bundle.py" --run-dir "$RUN_DIR" \
  || fail "VALIDATION_FAILED" "bundle validation failed"
cp "$RUN_DIR/public_graph.json" "$STAGE_DIR/public_graph.json" \
  || fail "STAGING_FAILED" "public_graph staging copy failed"
COUNTS="$(python3 -c 'import json,sys; g=json.load(open(sys.argv[1])); print(g["counts"]["nodes"], g["counts"]["edges"])' "$STAGE_DIR/public_graph.json")" \
  || fail "STAGING_FAILED" "cannot read graph counts"
NODE_COUNT="${COUNTS%% *}"
EDGE_COUNT="${COUNTS##* }"

# Release descriptor and checksums inside staging. The descriptor is
# the bundle record: it carries the frozen invocation ID and source SHA.
DURATION=$(( $(date +%s) - START_EPOCH ))
python3 - "$STAGE_DIR" "$HEAD_SHA" "$RUN_ID" "$DURATION" "$INVOCATION_ID" << 'PYEOF' || fail "RELEASE_RECORD_FAILED" "release descriptor write failed"
import hashlib, json, sys, os
rel_dir, head_sha, run_id, duration, invocation_id = sys.argv[1:6]
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
    "invocation_id": invocation_id,
    "duration_seconds": int(duration),
    "files": files,
}
with open(os.path.join(rel_dir, 'release.json'), 'w') as f:
    json.dump(release, f, indent=2, sort_keys=True)
with open(os.path.join(rel_dir, 'checksums.sha256'), 'w') as f:
    for rel, h in sorted(files.items()):
        f.write(f"{h}  {rel}\n")
print("release rel-" + run_id + " staged")
PYEOF

# Atomic promotion into releases/: rename only when complete and
# validated. A pre-existing release path is a collision and fails.
[ ! -e "$REL_DIR" ] || fail "RELEASE_COLLISION" "release already exists: $REL_DIR"
mv "$STAGE_DIR" "$REL_DIR" || fail "RELEASE_COLLISION" "release rename failed for $REL_DIR"

# State pointer moves only on success. It lives in the state directory
# and is never part of the public set.
printf '{"release_id": "%s", "head_sha": "%s", "run_id": "%s", "invocation_id": "%s", "duration_seconds": %s}\n' \
  "$RELEASE_ID" "$HEAD_SHA" "$RUN_ID" "$INVOCATION_ID" "$DURATION" > "$BASE/state/current.json" \
  || fail "STATE_WRITE_FAILED" "state pointer write failed"
record_json "OK" "" || fail "RECORD_WRITE_FAILED" "run record write failed"
echo "run $RUN_ID OK duration=${DURATION}s release=$RELEASE_ID"
