# Phase 1 change log (TASK-034, TASK-008, TASK-035 parts)

Working copy only. Nothing pushed.
Base head: 555b2e790a4a2cf8f643afeb081f67034a76e786.
Base file hashes matched the Phase 0 capture in safety-evidence-prep.md section 1 before any edit.

## scripts/run-nightly.sh (TASK-034, TASK-008 freeze)

Before: 101 lines, sha256 916ed3b2845713678ef05d8848657a5e078a6e66dac2fa5e70895abe65fc7362.
After: 184 lines. Full rewrite.
Changes:
- set -euo pipefail replaces set -u. Every step carries an explicit check with a named failure class. No pipe remains in the script, so no pipe can mask a failure.
- Source pin: reads config/approved-source.sha from the deployed tree (APPROVED_SHA_FILE override), checks out that exact SHA, verifies git rev-parse HEAD equals it, and requires a clean tree. A mismatch stops the run with class SOURCE_PIN_MISMATCH.
- Lock: flock -n. A held lock exits 75 and writes a SKIPPED_LOCK record. It never writes a success record and never moves the state pointer.
- Freeze: manifest.json, run_results.json, and catalog.json are copied into the staging bundle immediately after dbt build succeeds and before any docs call. The build runs with --write-catalog. A missing catalog now fails the run with class FREEZE_FAILED. The frozen run_results metadata.invocation_id is recorded in bundle_record.json and in release.json.
- Docs: dbt docs generate runs with --target-path docs-target, after the freeze. Its outputs never overwrite the frozen files.
- Staging: the bundle is built in releases/.staging-<release-id>, created with mkdir and no -p. It is renamed into releases/ only when complete and validated. A pre-existing release path fails the run with class RELEASE_COLLISION, checked before the run and again before the rename.
- Run record: one JSON record per run in the state directory, file run-<run-id>.json. Fields: slot, run_id, release_id, source_sha, invocation_id, nodes, edges, result (OK, FAILED with failure_class, SKIPPED_LOCK), duration_seconds, recorded_utc. The record never enters the public set.
- Mode M line kept: the script never deploys. Publication stays the manual promotion procedure.
- RUN_ID may be set from the environment for fixture runs. The timer path does not set it.

## scripts/validate_bundle.py (TASK-008)

Before: 71 lines, sha256 1038fb0a310fbaeea5710eea2ff352e29107cb55fa2b3ff16feb41031b923b38.
After: 149 lines. Extended, existing checks kept.
Changes:
- New result coverage validation block with named failure reasons: INVOCATION_NOT_BUILD, INVOCATION_MISMATCH, RESULTS_MISSING, EXPECTED_EMPTY, RESULTS_EMPTY, RESULT_ID_DUPLICATE, RESULT_ID_MISSING, RESULT_ID_EXTRA, RESULT_STATUS_DISALLOWED, RESULT_STATUS_FAILED.
- Expected set derivation: manifest nodes with resource_type in model, seed, test, snapshot. When the run directory holds expected_result_ids.json, that stored set is the expected set (fixture form).
- Approved statuses: success, pass, fail, error, skipped. A fail or error status fails validation. A status outside the set fails validation.

## tests/fixtures/run-results/ (TASK-008, new)

Eight fixture directories, five files each, 40 files.
Cases: good, empty-results, failed-status, duplicate-id, missing-id, extra-id, stale-invocation, wrong-invocation.
Each directory holds manifest.json, public_graph.json, run_results.json, expected_result_ids.json, bundle_record.json.

## scripts/export_graph.py (TASK-035 part)

Before: 80 lines, sha256 583f8e12913c6fb3556d9007a1abd653170b5c88efc48efa4c711f40a6d95ed8.
After: 149 lines. Rewritten projection logic, output format kept.
Changes:
- Topological cycle detection with iterative DFS. A cycle fails with reason CYCLE_DETECTED and the cycle path named.
- Depth is a memoised longest-path calculation over the projected graph. It replaces the breadth-first seen-set walk. Over-depth fails with reason DEPTH_EXCEEDED.
- Edges whose parent sits outside the projection are dropped, with a DANGLING_EDGE_DROPPED notice on stdout. Emitted depends_on lists hold projected parents only.
- Strings are bounded with failure, never truncated. Limits: name 200 chars (OVERSIZED_NAME), description 200 chars (OVERSIZED_DESCRIPTION), tag 200 chars (OVERSIZED_TAG), 20 tags per node (TOO_MANY_TAGS). Size limits kept: 500 nodes, 2000 edges (GRAPH_TOO_LARGE), depth 10.

## tests/fixtures/exporter/ (TASK-035 part, new)

Six manifest fixtures: good-manifest.json, cycle-manifest.json, dangling-manifest.json, oversized-manifest.json, oversized-tag-manifest.json, depth-manifest.json.

## config/public-artifact-policy.yml (TASK-035 part)

Before: 30 lines, sha256 bc33d17d5e13c8dc8c55b578e460f57e3bd97f83c14bf7d7b1c1e1da943a32f2.
After: 43 lines.
Changes:
- Allowlist is now location-aware and holds exactly four paths: public/dbt/releases/current.json, public/dbt/releases/index.json, public/dbt/releases/<release-id>/release.json, public/dbt/releases/<release-id>/public_graph.json.
- Removed from the permitted set: docs/index.html, docs/assets/**, data-quality-summary.json. All three now sit in the forbid list.
- Added: index.json at the releases root.
- Forbid list, limits, and scan list otherwise kept.

## config/approved-source.sha (TASK-034, new)

One line: 555b2e790a4a2cf8f643afeb081f67034a76e786.
This is the owner-approved source SHA at Phase 1 build time. The deployed tree carries the same file at config/approved-source.sha, and run-nightly.sh reads it from there.
