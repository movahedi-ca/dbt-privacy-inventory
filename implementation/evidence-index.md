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

## G-BUILD (IN PROGRESS)
- Builder: dbt-runner user, /opt/privacy-dbt tree, locked engine installed for dbt-runner.
- T29 RAM/CPU benchmark: PENDING (runs after P3 setup).
- Keepalive: real maintenance work (health endpoint + disk + dbt parse, every 6 h). Reasoning: V2 section 2.3 says do not run artificial load to prevent reclaim; the keepalive does real work, not a busy-loop (DEV-006).

## G-PRIVACY + G-ARTIFACT (PENDING)
- Graph exporter + bundle validator: scripts/export_graph.py, scripts/validate_bundle.py (written, not yet run end to end).
- First bundle: PENDING (runs after P3 setup + benchmark).

## G-DEPLOY / G-PUBLISH (PENDING - owner review)
- Mode M only. Bundle stages at /opt/privacy-dbt/releases/. Live deploy held for owner review. He is asleep; do not deploy.

## G-API-SHADOW (PENDING)
- Six family contracts: config/api-schema-contracts/ (stubs written; fill from GitHub main snapshots).
- Shadow models: models/staging/api, models/intermediate/api, models/marts/api_shadow (skeleton; fill in P7).

## G-OPERATIONS (PENDING - observation windows)
- 7 consecutive scheduled runs: cannot complete tonight.
- 30-day $0 billing: cannot complete tonight.
- Timer: 02:15 UTC, Persistent=false. Enable only after the manual pipeline run passes.
