# Decisions

## DEC-01 (repo + license)
- Repo: movahedi-ca/dbt-privacy-inventory (created 2026-11-07, public).
- License: PENDING owner selection. No license file until he selects one.

## DEC-02 (engine)
- Preferred: dbt OSS v2 (Apache 2.0-only), bundled DuckDB, no adapter install.
- Pin candidate: 2.0.11 (latest v2, released 2026-11-03; PyPI sdist SHA-256 ed5cccb16863d25b1c358ee2f2d2ef6288043b7e4fa9e81acc5763a4317a871e).
- Install: `uv tool install dbt-oss==2.0.11` (uv via pip --user).
- Fallback: dbt Core v1.11.17 + matching dbt-duckdb (only if v2 fails an essential acceptance test; never mixed).
- Acceptance record: config/engine-lock.md (filled from the live run).

## DEC-03 (canonical source per Privacy API family)
- Canonical source is workers/public-api/src/api/data.ts (movahedi-ca/movahedi-ca, main).
- Glossary, enforcement, Law 25, cookie patterns, crawlers: exported constants in data.ts.
- Vendor KB: the vendor/legalParty dimension of src/data/cookie-kb.ts (no standalone API constant).
- Snapshots come from GitHub main, not the local checkout (local HEAD is behind main).

## DEC-04 (artifact relay + deploy)
- Build plane (Micro) and deploy plane (Muse VM site checkout + deploy_site.py) are separate.
- No production credentials on the Micro. Release bundles stage privately; Mode M (owner-reviewed) promotion only.

## DEC-05 (unattended publication)
- NO unless explicitly approved and tested. Mode M stands.

## DEC-06 (article ROPA example)
- Pending: select the fictional activity after the test build. Article draft only, separate owner approval to publish.

## DEC-07 (API cutover)
- NO. Phase 1 shadow only.

## DEC-08 (shared free-service allocations)
- Tenancy inventory (2026-11-07): 1 Micro instance, 1 boot volume (50 GB), 0 block volumes. No other billable resources.
