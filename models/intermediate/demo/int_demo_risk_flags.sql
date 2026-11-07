-- int_demo_risk_flags: explicit, explainable demo rules.
-- Rule (deterministic, documented, not inferred):
--   high vendor risk tier -> flag "vendor_high_risk"
--   restricted classification -> flag "restricted_data"
--   missing asset/vendor/retention reference -> flag "unresolved_reference"
--   otherwise -> flag "none"
-- Fictional data. Not a real organization.
select
    activity_id,
    activity_name,
    classification,
    risk_tier,
    asset_missing,
    vendor_missing,
    retention_missing,
    case
        when asset_missing or vendor_missing or retention_missing then 'unresolved_reference'
        when risk_tier = 'high' then 'vendor_high_risk'
        when classification = 'restricted' then 'restricted_data'
        else 'none'
    end as risk_flag
from {{ ref('int_demo_activity_links') }}
