# Engine lock: dbt OSS v2 (pinned after the Linux x86_64 acceptance test)
# Playbook V3-B / V2 section 4. One pinned distribution, never mixed.
# Fill every field from the acceptance run. No field may stay PENDING
# in a released lock.

product: dbt-oss
distribution: dbt OSS v2 (Apache 2.0-only subset of dbt v2)
license: Apache-2.0
version: PENDING (acceptance test)
source_url: https://pypi.org/project/dbt-oss/
pypi_sdist_sha256: PENDING (acceptance test; 2.0.11 sdist hash from PyPI)
install_method: uv tool install dbt-oss==<version> (uv via pip --user)
architecture: x86_64 (Micro; playbook A1/aarch64 target is owner-deviated)
os: Ubuntu 24.04.5 LTS
uname_m: PENDING
dbt_version_output: PENDING
dbt_debug_output: PENDING
dbt_parse: PENDING
dbt_build: PENDING
docs_smoke_test: PENDING
duckdb_version: PENDING (bundled; from dbt debug or the adapter report)
manifest_schema_version: PENDING (metadata.dbt_schema_version in target/manifest.json)
docs_file_inventory: PENDING (find target -type f after docs generate)
binary_sha256_observed: PENDING (sha256sum of the installed dbt binary)
binary_path: PENDING
du_sh: PENDING
approval: PENDING (owner)
fallback: dbt Core v1.11.17 + matching dbt-duckdb adapter (only if v2 fails an essential acceptance test; never mixed in one environment)
