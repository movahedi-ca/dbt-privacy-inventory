# Backend documentation: dbt privacy inventory system

This document describes the backend system behind this repository. It is
written for any editor of this repository, human or automated, including
editors who also edit the public site and the data map tool.

Read this document before changing the nightly builder, the release
format, the public output, or the shadow models. Changes that ignore the
rules in this document can publish private artifacts, break the public
release chain, or overwrite work by another editor.

Related documentation:

- Site side of this system: `docs/dbt-backend.md` in the
  `movahedi-ca/movahedi-ca` repository. That document describes the site
  files that receive each release.
- Manifest adapter contract: `web/import/MANIFEST-ADAPTER-CONTRACT.md`
  in the `movahedi-ca/AI-data-map` repository. That contract defines how
  a dbt manifest held locally by a visitor is projected and tied to a
  published release of this project. Its privacy and tie rules are part
  of the system invariants in section 4 of this document.

## 1. System map

- An Oracle Cloud micro instance, host name `oracle-micro`, runs the
  nightly build.
- A systemd timer, `dbt-privacy.timer`, starts the build at 02:15 UTC.
  A timer drop-in sets the calendar in explicit UTC and sets
  `Persistent=true`, so a missed slot runs on the next boot.
- The builder is `scripts/run-nightly.sh` in this repository. Deployed
  copies run on the instance.
- The builder builds the demo project with the pinned engine:
  dbt-oss 2.0.11 and DuckDB 1.5.4. The demo project holds 9 models,
  4 seeds, and 32 tests.
- The builder validates the release bundle and stages the bundle on the
  instance. Staging is private. Nothing staged is public by itself.
- The builder never publishes by itself. The script header names this
  rule Mode M. Publication is a separate manual promotion by the
  operator, daily by 04:00 UTC, following the promotion runbook
  summarized in section 5.
- Promotion ships exact files to the site repository,
  `movahedi-ca/movahedi-ca`, by Git Data API pushes in two steps:
  expand, then activate. GitHub Actions then builds and deploys the
  site. Cloudflare serves the result.
- Monitoring runs on the operator machine, not on the instance. See
  section 3 and section 5.

Data flow, in order:

1. Nightly build on the instance.
2. Bundle validation on the instance.
3. Private staging on the instance.
4. Manual promotion by the operator.
5. Two-step push to the site repository.
6. Site build and deploy by GitHub Actions.
7. Public files served by Cloudflare.

## 2. File map: instance

The base directory on the instance is `/opt/privacy-dbt/`.

- `repo/` holds this repository, checked out.
- `scripts/` holds deployed copies of the repository scripts.
- `config/approved-source.sha` holds the approved source pin. This file
  is deliberately outside the checkout. The builder refuses to run when
  the checkout head does not equal the pin.
- Staged bundles and the staged state pointer live under the base
  directory, outside the checkout.
- `shadow/` is the shadow build area. Shadow builds never write the
  live release path.

## 3. File map: repositories and operator machine

In this repository:

- `scripts/run-nightly.sh` is the hardened nightly builder.
- `scripts/export_graph.py` exports the public graph from a build.
- `scripts/validate_bundle.py` validates a staged bundle before any
  promotion can use it.
- `config/public-artifact-policy.yml` defines the public output set.
  See section 4.
- `config/approved-source.sha` in this repository is a fixture default
  only. The deployed pin lives on the instance, outside the checkout.
  Editing the repository copy does not change the deployed pin.
- `ops/` holds the systemd timer and service units.
- `models/shadow/` holds the row-level shadow models. They are
  disabled unless the environment variable `DBT_SHADOW_ENABLED` is
  set to `true`.

In the site repository, `movahedi-ca/movahedi-ca`:

- `public/dbt/releases/` holds the published release tree.
- `src/pages/dbt/index.astro` is the public dbt page.
- `docs/dbt-backend.md` in that repository documents the site side.

On the operator machine:

- A Rust staleness checker runs every 15 minutes. It checks the
  publication deadline in section 5, writes alert records on a breach,
  and a hook delivers alerts to the operator.
- A Rust public-output validator validates the site releases tree
  before and after promotion.
- The rebuild pack lives at
  `~/workspace/dbt-next-steps-work/rebuild-pack/` on the operator
  machine. A restore from that pack was rehearsed and reached a
  working private build in 39 seconds.
- The operations ledger lives at
  `~/workspace/oracle-vm-ops/implementation/dbt-next-steps/` on the
  operator machine. It holds `state.yaml` and `progress.log`.

## 4. Invariants and do-not-touch rules

Every editor must keep these rules. They are design rules, not gaps
waiting for a fix.

1. Never add publication, deploy, or push steps to the nightly
   builder. The builder stages only. Mode M is a design rule, not a
   missing feature.
2. Never store any credential on the instance. The instance holds no
   site credential, no GitHub credential, and no deploy credential.
3. The `run_results.json` file in a bundle must come from a real build
   invocation, never from a compile. The bundle validator enforces
   invocation match and full result coverage, and rejects the bundle
   otherwise. Do not weaken that check.
4. Release creation is exclusive, and the staged pointer moves
   atomically. Do not simplify these back to a plain `mkdir` or a
   plain `cp`.
5. The approved-source pin must stay outside the checkout. Do not move
   it into the repository and do not make the builder read the pin
   from the checkout it is verifying.
6. Public output is exactly four files, per
   `config/public-artifact-policy.yml`:
   - `current.json` at the releases root.
   - `index.json` at the releases root.
   - `release.json` inside one release folder. This is the public
     descriptor, generated from the bundle at promotion time.
   - `public_graph.json` inside one release folder.
   No other file is public output.
7. Internal bundle artifacts are private and never published. The
   private set includes `manifest.json`, `catalog.json`,
   `run_results.json`, the internal `release.json` inside a bundle,
   DuckDB files, logs, and compiled SQL. The public descriptor in
   rule 6 is a generated file. It is not a copy of the internal
   descriptor.
8. Shadow models stay disabled by default. Shadow work never writes
   the live application programming interface and never writes the
   release path. A parity program proved source, shadow, and live
   rows equal on 2026-11-15. No cutover is approved. Any cutover
   needs its own plan and its own approval.
9. The demo node set is 45 nodes and 55 edges. A change to models or
   seeds changes the public graph. That change is a release event,
   not a quiet edit. Expect the graph counts, the projection hash,
   and the adapter fixtures to move with it.
10. The manifest adapter contract in the `AI-data-map` repository
    shares these invariants, and editors must keep both sides
    consistent:
    - Import is browser-local only.
    - No upload or network send carries file content.
    - The projection hash ties a local manifest to a published
      release.
    - Verification fails closed. No verified tie, no render.
    Changing the public graph format, the release descriptor fields,
    or the release naming in this repository can break that contract.

## 5. Operations

### 5.1 Promotion runbook summary

- The candidate comes from a validated staged bundle. An unvalidated
  bundle is never promoted.
- The public descriptor is generated from the bundle. The operator
  never copies the internal bundle descriptor into the public tree.
- The push to the site repository runs in two steps: expand, then
  activate.
- After the push, the operator verifies live hashes against the
  candidate before calling the promotion done.
- Rollback works by pointer restoration. One rule binds rollback: a
  rollback push that must pass the public-output validator also
  removes the new release folder. A rollback that leaves the new
  folder in place does not pass validation.

### 5.2 Validation and monitoring

- The Rust public-output validator validates the releases tree before
  and after promotion.
- The Rust staleness checker runs every 15 minutes on the operator
  machine. Deadline rule: the build for the day must be published by
  04:00 UTC. A breach writes an alert record, and delivery of alerts
  to the operator is proved, not assumed.

### 5.3 License

- This repository is licensed under Apache License 2.0. The `LICENSE`
  and `NOTICE` files sit at the repository root. The holder named in
  `NOTICE` is Mohammad Movahedi.

### 5.4 Observation windows running now

- Seven consecutive nightly slots run from 2026-11-16. The run window
  ends at 2026-11-22T04:00Z.
- The thirty-day cost window ends at 2026-12-15T17:15:23Z.
- Both windows close in real time. Neither window can be reported as
  complete before its end time.

## 6. Change protocol

Any future editor, human or automated, follows this protocol:

1. Read this document and the site document,
   `docs/dbt-backend.md` in `movahedi-ca/movahedi-ca`, before editing.
2. Check the repository head before pushing. Parent every commit on
   the live head.
3. Never revert another editor's commits. Build on top of them, or
   stop and record the conflict.
4. Record changes in the operations ledger on the operator machine at
   `~/workspace/oracle-vm-ops/implementation/dbt-next-steps/`, in
   `state.yaml` and `progress.log`.
5. Site changes go through a deploy claim plus exact-file pushes.
   Never deploy the site from a local tree.
6. Keep the cost at zero. This system runs on free tiers and local
   machines by design.
