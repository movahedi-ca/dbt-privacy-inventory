# Nightly runbook (dbt-privacy-inventory)

## Normal run
- Timer fires 02:15 UTC daily. Service runs run-nightly.sh as dbt-runner.
- Check: `systemctl status dbt-privacy.service`, `journalctl -u dbt-privacy.service -n 50`.
- Run record: /opt/privacy-dbt/runs/<UTC_RUN_ID>/ (dbt-build.log, dbt-docs.log, status.txt).
- Release: /opt/privacy-dbt/releases/rel-<UTC_RUN_ID>/ (public_graph.json, manifest.json, release.json, checksums.sha256).
- Current pointer: /opt/privacy-dbt/state/current.json.

## Failure
- A failed run writes NO release and publishes nothing. The run directory keeps the logs.
- Common causes: git pull conflict (fix by hand, never force-push), dbt test failure (fix the model or the seed, never skip the test), disk full (check df; the DuckDB file is in work/, never published).
- After a fix, run the service once by hand: `systemctl start dbt-privacy.service`. Do not edit the timer.

## Rollback
- Releases are immutable and dated. To roll back the staged bundle, point the deploy at the previous release directory (rel-<earlier>). Nothing is deleted.
- Never delete a release to hide a failure. Record the failure in implementation/evidence-index.md.

## Publish (Mode M only)
- The bundle stages at /opt/privacy-dbt/releases/. It reaches the live site ONLY after owner review and an explicit promotion.
- Promotion copies the bundle to the deploy plane (Muse VM site checkout) via the deploy tool. The Micro never writes to the site.
