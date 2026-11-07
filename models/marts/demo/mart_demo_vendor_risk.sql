-- mart_demo_vendor_risk: synthetic vendor examples.
-- Fictional data. Not a real organization.
select
    v.vendor_id,
    v.vendor_name,
    v.vendor_type,
    v.risk_tier,
    v.country,
    count(l.activity_id) as activity_count
from {{ ref('stg_demo_vendors') }} as v
left join {{ ref('int_demo_activity_links') }} as l
    on v.vendor_id = l.vendor_id
group by v.vendor_id, v.vendor_name, v.vendor_type, v.risk_tier, v.country
