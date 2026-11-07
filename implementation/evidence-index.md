# Evidence index (dbt-privacy-inventory)

Every gate needs stored, checksum-recorded evidence. This file is the index.

## P0 discovery (DONE 2026-11-07 ~05:00 UTC)
- Evidence: ~/workspace/oracle-vm-ops/implementation/dbt/discovery/ (environment.md, repository-inventory.md, api-contracts.md, deploy-plane.md, cost-baseline.md).
- Live API counts (movahedi.ca/api/v1/health, 2026-11-07 ~05:00 UTC): glossary 333, enforcement 10, law25 11, cookie 202, crawlers 55. data_version v2026.12.0.

## G-COST + G-ENGINE (DONE 2026-11-07 05:17-05:24 UTC)
- Engine: dbt-oss 2.0.11, Apache 2.0, DuckDB v1.5.4 bundled. Acceptance log: ~/jobs/dbt-build.log on the Micro.
- Binary SHA: dbt shim e0fa0f89c3f1ea89fa273a38c888a4b171a61e85f6e36db64531dcf4a0b0d6d2; _core.abi3.so f10493462cccb22d8de25a7a7878d92994264f3b2f1ba511f796f823d5482585.
- Manifest schema: https://schemas.getdbt.com/dbt/manifest/v12.json, 44 nodes.
- Full lock: config/engine-lock.md.
- Cost: tenancy inventory 1 Micro instance, 1 boot volume (50 GB), 0 block volumes. Spend $0.00 (carried from the 2026-11-06 console verification; usage API not authorized for the auto-oracle user). T40 is a pending 30-day observation window.

## G-MODEL (DONE 2026-11-07 ~05:24 UTC)
- Full dbt build: 45 total, 45 success (9 models, 32 tests, 4 seeds).
- Negative tests: T05 duplicate activity_id fails (unique, 1 failed row). T06 missing vendor FK fails (relationships, 1 failed row; required adding the vendor_id relationship test). T07 unknown status: same mechanism, not yet run.
- Models: models/staging/demo (4), models/intermediate/demo (2), models/marts/demo (3). Schema: models/schema.yml.

## G-BUILD (DONE 2026-11-07 05:36-05:39 UTC)
- Builder: dbt-runner user, /opt/privacy-dbt tree, locked engine installed for dbt-runner.
- T29 RAM/CPU benchmark (measured, /usr/bin/time -v): full build peak RSS 236,732 KB (~231 MB), 7.13 s wall, 4.57 s user + 0.79 s system CPU. Full pipeline peak RSS 232,144 KB (~227 MB), 9.79 s wall. Verdict: fits the 952 MiB envelope with headroom (24% of RAM). Service MemoryMax=800M (3.5x measured peak, under box RAM).
- Keepalive: real maintenance work (health endpoint + disk + dbt parse, every 6 h). Tested live 2026-11-07 05:45 UTC: exit 0, health ok, disk 41G free, dbt parse 1.0s. Reasoning: V2 section 2.3 says do not run artificial load to prevent reclaim; the keepalive does real work, not a busy-loop (DEV-006).

## G-PRIVACY + G-ARTIFACT (DONE 2026-11-07 05:39 UTC)
- Graph exporter + bundle validator: scripts/export_graph.py, scripts/validate_bundle.py. First bundle rel-2026-11-07T05-39-23Z: 45 nodes, 55 edges, 663,050 bytes, checksums verified (all OK). PII validator test: injected email into a node description, validator blocked it (exit 1).
- Deviation DEV-007 (CORRECTED 2026-11-07 ~05:55 UTC by the engine research report): dbt-oss writes no catalog.json by default, but `dbt build --write-catalog` writes target/catalog.json (fixed in 2.0.8). The first release lacked catalog.json only because the build ran without the flag. run-nightly.sh now passes --write-catalog. NOT verified live on the Micro yet (SSH ingress removed at end of run); verify on the next Micro access and sync the updated scripts.
- Engine research report (subagent, completed 2026-11-07T04:56:19Z, delivered late): confirms dbt-oss 2.0.11, DuckDB 1.5.4 bundled, manifest v12, no sign-in, no paid boundary for local DuckDB use. Fallback pin corrected to dbt-core 1.12.6 + dbt-duckdb 1.11.1 (docs page; GitHub releases listed 1.11.17 — sources disagree, docs page is the pin). No official SHA-256 exists for any v2 binary (pin by version + install channel, not hash). Docs v2 viewers need internet (DuckDB-WASM from a CDN).

## G-DEPLOY / G-PUBLISH (STAGED, NOT DEPLOYED - owner review)
- Mode M only. Bundle stages at /opt/privacy-dbt/releases/rel-2026-11-07T05-39-23Z/. Live deploy held for owner review. He is asleep; do not deploy.

## G-API-SHADOW (PARTIAL 2026-11-07 05:43 UTC)
- Parity mechanism DONE: scripts/extract_api_snapshot.py, frozen snapshot at head 5b542d81850fcaf3365f79d9247dd016c0bf824b, SHA-256 verified on the Micro. Report: /opt/privacy-dbt/state/api-snapshot/out/api_snapshot_parity.json.
- Results: enforcement 10 vs 10 MATCH, law25 11 vs 11 MATCH, cookie 202 vs 202 MATCH, crawlers 55 vs 55 MATCH. Glossary MISMATCH: snapshot 331 vs live 333 (upstream glossary.ts has 334; live serves 333 from uncommitted working-tree refreshes; main data.ts has 331). Vendor KB: 66 distinct vendors.
- Deviation DEV-008: the Micro cannot fetch the private site repo; snapshots are fetched where GitHub auth lives and transferred frozen. DEV-009: data files live at repo-root src/data/.
- Row-level shadow models: PENDING (needs TS-to-JSON extraction of the data.ts constants + license review). License review: NOT CHECKED (owner decision).

## G-OPERATIONS (TIMER ENABLED, OBSERVATION PENDING)
- Timer 02:15 UTC daily, Persistent=false, enabled 2026-11-07 05:48 UTC; next run Sun 2026-11-08 02:15 UTC. Keepalive every 6 h, enabled and tested.
- 7 consecutive scheduled runs: cannot complete tonight (first run is tomorrow).
- 30-day $0 billing: cannot complete tonight (T40 observation window).
