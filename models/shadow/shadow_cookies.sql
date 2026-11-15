-- Shadow model for the cookie patterns family. Source: TASK-010 snapshot
-- rows (src/data/cookie-kb.ts at 54642b3267c0b11d5e6959077de56e4abf251c25).
-- Stable row key: row_key = pattern, the snapshot key field.
-- Source camelCase fields are carried under snake_case column names:
-- legalParty as legal_party, typicalRetention as typical_retention,
-- controlClass as control_class, reviewDate as review_date.
-- cname_targets_json holds the source cnameTargets array as canonical JSON.
select
    row_key,
    pattern,
    match,
    vendor,
    legal_party,
    purpose,
    typical_retention,
    control_class,
    source,
    review_date,
    nullif(cname_targets_json, '') as cname_targets_json
from {{ ref('shadow_src_cookies') }}
