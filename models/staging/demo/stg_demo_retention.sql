-- stg_demo_retention: fictional retention policy references.
-- Fictional data. Not a real organization.
select
    cast(rule_id as varchar) as rule_id,
    trim(rule_name) as rule_name,
    cast(period_value as integer) as period_value,
    lower(trim(period_unit)) as period_unit,
    lower(trim(applies_to)) as applies_to
from {{ ref('retention_rules') }}
