-- stg_demo_vendors: fictional processors and risk flags.
-- Fictional data. Not a real organization.
select
    cast(vendor_id as varchar) as vendor_id,
    trim(vendor_name) as vendor_name,
    lower(trim(vendor_type)) as vendor_type,
    lower(trim(risk_tier)) as risk_tier,
    trim(country) as country
from {{ ref('vendors') }}
