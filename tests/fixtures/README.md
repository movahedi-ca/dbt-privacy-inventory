# Deliberately invalid fixtures for negative tests (T05, T06, T07, T12, T17).
# Each file is used by the test runner in an isolated copy: swap it in,
# run dbt build, expect FAILURE in the intended way, restore the good seed.
# Never commit a bad fixture as a live seed.

## duplicate_activity_id.csv
# Copy of processing_activities.csv with ACT-001 duplicated.
# Expected: unique test on activity_id fails; no release is promoted.
activity_id,activity_name,purpose,asset_id,vendor_id,retention_rule_id,status
ACT-001,Customer onboarding,Create and verify customer accounts,AST-001,VND-001,RET-001,active
ACT-001,Customer onboarding again,Create and verify customer accounts,AST-001,VND-001,RET-001,active

## missing_vendor_fk.csv
# Activity references a vendor that does not exist (VND-999).
# Expected: relationship test fails; bad fixture cannot be released.
activity_id,activity_name,purpose,asset_id,vendor_id,retention_rule_id,status
ACT-099,Unknown vendor activity,Test missing vendor,AST-001,VND-999,RET-001,active

## unknown_status.csv
# Activity with a status outside the accepted set.
# Expected: accepted_values test on status fails.
activity_id,activity_name,purpose,asset_id,vendor_id,retention_rule_id,status
ACT-098,Unknown status activity,Test unknown status,AST-001,VND-001,RET-001,archived

## pii_contaminant.csv
# A seed row carrying a real-looking email address.
# Expected: the PII scan blocks publication (T12). Never reaches a release.
activity_id,activity_name,purpose,asset_id,vendor_id,retention_rule_id,status
ACT-097,PII contaminant,Contact jane.doe@example.com for details,AST-001,VND-001,RET-001,active

## unsafe_label.csv
# A label carrying markup that must be encoded, never executed.
# Expected: the graph exporter encodes it; the browser shows inert text (T17).
asset_id,asset_name,classification,owner,data_category
AST-099,<script>alert(1)</script>,public,Web Team,website

## oversized_payload.csv
# A single label far beyond the allowed size budget.
# Expected: the graph/bundle validator rejects it (T18).
asset_id,asset_name,classification,owner,data_category
AST-098,PLACEHOLDER_10KB_LABEL,public,Web Team,website
