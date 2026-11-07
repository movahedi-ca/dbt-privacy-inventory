-- int_demo_activity_links: derived activity-to-asset/vendor dependencies.
-- Left joins so an unresolved reference is visible, not silently dropped.
-- Fictional data. Not a real organization.
select
    a.activity_id,
    a.activity_name,
    a.purpose,
    a.asset_id,
    s.asset_name,
    s.classification,
    a.vendor_id,
    v.vendor_name,
    v.risk_tier,
    a.retention_rule_id,
    r.rule_name as retention_rule_name,
    r.period_value as retention_period_value,
    r.period_unit as retention_period_unit,
    a.status,
    case when s.asset_id is null then true else false end as asset_missing,
    case when a.vendor_id is not null and v.vendor_id is null then true else false end as vendor_missing,
    case when r.rule_id is null then true else false end as retention_missing
from {{ ref('stg_demo_activities') }} as a
left join {{ ref('stg_demo_assets') }} as s
    on a.asset_id = s.asset_id
left join {{ ref('stg_demo_vendors') }} as v
    on a.vendor_id = v.vendor_id
left join {{ ref('stg_demo_retention') }} as r
    on a.retention_rule_id = r.rule_id
