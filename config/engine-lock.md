# Engine lock: dbt OSS v2 (pinned after the Linux x86_64 acceptance test)
# Playbook V3-B / V2 section 4. One pinned distribution, never mixed.
# All values below are from the live acceptance run on the Micro,
# 2026-11-07 05:17-05:24 UTC. Evidence: ~/jobs/dbt-build.log on the Micro.

product: dbt-oss
distribution: dbt OSS v2 (Apache 2.0-only subset of dbt v2)
license: Apache-2.0
version: 2.0.11
source_url: https://pypi.org/project/dbt-oss/
pypi_sdist_sha256: ed5cccb16863d25b1c358ee2f2d2ef6288043b7e4fa9e81acc5763a4317a871e
pypi_sdist: dbt_oss-2.0.11.tar.gz (4957 bytes, requires_python >=3.10, requires mashumaro[msgpack]>=3.14)
install_method: uv tool install dbt-oss==2.0.11 (uv 0.13.7 via pip --user --break-system-packages; uv tool env 214 MB)
architecture: x86_64 (Micro; playbook A1/aarch64 target is owner-deviated, DEV-001)
os: Ubuntu 24.04.5 LTS
uname_m: x86_64
dbt_version_output: dbt-oss 2.0.11
dbt_debug_output: "Debugging connection test: OK. Debugged All checks passed!" (adapter duckdb (remote), path work/dbt_privacy_inventory.duckdb)
dbt_parse: passed (dbt build runs parse; explicit dbt parse ran 2026-11-07 05:21 UTC)
dbt_build: 45 total, 45 success (9 models, 32 tests, 4 seeds) on 2026-11-07 05:24 UTC
docs_smoke_test: dbt docs generate succeeded (8.5 s); target/ holds manifest.json, catalog.json, index.html
duckdb_version: v1.5.4 (bundled; from dbt show --inline "select version()")
manifest_schema_version: https://schemas.getdbt.com/dbt/manifest/v12.json
docs_file_inventory: target/manifest.json, target/catalog.json, target/run_results.json, target/semantic_manifest.json, target/index.html, target/assets/** (see run log)
binary_sha256_observed:
  dbt shim (/home/ubuntu/.local/bin/dbt): e0fa0f89c3f1ea89fa273a38c888a4b171a61e85f6e36db64531dcf4a0b0d6d2
  Rust core (/home/ubuntu/.local/share/uv/tools/dbt-oss/lib/python3.12/site-packages/dbt/_core.abi3.so, 219,588,576 bytes): f10493462cccb22d8de25a7a7878d92994264f3b2f1ba511f796f823d5482585
binary_path: /home/ubuntu/.local/bin/dbt (Python shim -> dbt.cli.main.cli; Rust core is the _core.abi3.so extension)
installed_packages: dbt-oss==2.0.11, mashumaro==3.23, msgpack==1.2.4, typing-extensions==4.16.0
negative_tests:
  T05 duplicate activity_id: build fails (unique test, 1 failed row) - VERIFIED 2026-11-07
  T06 missing vendor FK (VND-999): build fails (relationships test, 1 failed row) - VERIFIED 2026-11-07 (required adding the vendor_id relationship test; nulls are ignored by the test, so ACT-004 still passes)
  T07 unknown status: not yet run (accepted_values test covers it; same mechanism as T05/T06)
approval: PENDING (owner; gate sign-off stays with him)
fallback: dbt Core v1.12.6 + dbt-duckdb 1.11.1 (per docs.getdbt.com/docs/dbt-versions; the GitHub releases page listed dbt-core 1.11.17 as latest v1 — the two sources disagree; the docs page is the pin). Only if v2 fails an essential acceptance test; never mixed in one environment. NOT NEEDED: v2 passed.
catalog_note: "dbt-oss writes no catalog.json by default. `dbt build --write-catalog` writes target/catalog.json (fixed in 2.0.8). The first release (rel-2026-11-07T05-39-23Z) lacked catalog.json because the build ran without the flag. run-nightly.sh now passes --write-catalog. NOT verified live on the Micro yet (SSH ingress removed at end of run); verify on the next Micro access."
