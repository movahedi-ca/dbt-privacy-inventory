-- Singular test: no unresolved references may reach the ROPA mart.
-- The intermediate layer flags them; the mart must not carry them.
-- Returns rows (fails) when an unresolved reference exists.
select activity_id, asset_id, vendor_id, retention_rule_id
from {{ ref('mart_demo_ropa') }}
where asset_id is null or retention_rule_id is null
