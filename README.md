# dbt-privacy-inventory

SYNTHETIC DATA — NOT A REAL ORGANIZATION.

A reproducible, publicly inspectable synthetic demonstration: a dbt + DuckDB
privacy-inventory lineage project, built once per night on an Oracle Always
Free VM, with static documentation and conservative Privacy API shadow
validation.

It is not a production privacy register, regulator-approved assessment, proof
of Law 25 compliance, or guarantee that no future bill could ever occur.
Declared dbt dependency lineage is not observed runtime access, not proof of
deletion or enforcement, and not legal compliance.

## What this proves

- A version-controlled dbt dependency graph (`seed -> staging -> intermediate -> mart`).
- Automated data-quality tests, including deliberately failing fixtures.
- A frozen, checksum-recorded release bundle per nightly build.
- Read-only shadow parity against the six Privacy API dataset families.

## Quickstart (5 minutes)

Requires the pinned engine (see `config/engine-lock.md`).

```bash
uv tool install dbt-oss==2.0.11
dbt --version   # must start with 2.
cp profiles.yml.example profiles.yml
mkdir -p work   # DuckDB cannot create the file if the directory is missing
dbt parse
dbt build
dbt docs generate
```

The DuckDB file lands in `work/` (never committed, never published).

## Layout

- `seeds/synthetic/` — fictional fixtures, all marked FICTIONAL.
- `models/staging/demo/`, `models/intermediate/demo/`, `models/marts/demo/` — demo lineage.
- `models/staging/api/`, `models/intermediate/api/`, `models/marts/api_shadow/` — read-only Privacy API shadow models.
- `scripts/` — nightly runner, bundle validator, graph exporter.
- `ops/` — systemd timer/service and runbooks.
- `config/` — engine lock, public-artifact policy, API schema contracts.
- `implementation/` — state, decisions, evidence index.

## License

Pending owner selection. No license file is included until the owner selects
one. Until then, all rights reserved by default.

## Status

See `implementation/state.yaml`. Engineering status, gate evidence, and the
nightly run record live there and in `implementation/evidence-index.md`.
