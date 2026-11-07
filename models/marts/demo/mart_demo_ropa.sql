-- mart_demo_ropa: one fictional ROPA-like report for the article.
-- A teaching example, not a complete statutory ROPA or proof of compliance.
-- Fictional data. Not a real organization.
select
    l.activity_id,
    l.activity_name,
    l.purpose,
    l.asset_id,
    l.asset_name,
    l.classification,
    l.vendor_id,
    l.vendor_name,
    l.retention_rule_id,
    l.retention_rule_name,
    l.retention_period_value,
    l.retention_period_unit,
    l.status,
    f.risk_flag
from {{ ref('int_demo_activity_links') }} as l
left join {{ ref('int_demo_risk_flags') }} as f
    on l.activity_id = f.activity_id
