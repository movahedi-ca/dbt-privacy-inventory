-- stg_demo_activities: validate example activity records.
-- Fictional data. Not a real organization.
select
    cast(activity_id as varchar) as activity_id,
    trim(activity_name) as activity_name,
    trim(purpose) as purpose,
    cast(asset_id as varchar) as asset_id,
    cast(vendor_id as varchar) as vendor_id,
    cast(retention_rule_id as varchar) as retention_rule_id,
    lower(trim(status)) as status
from {{ ref('processing_activities') }}
