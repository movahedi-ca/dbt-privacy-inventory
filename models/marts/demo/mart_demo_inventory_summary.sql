-- mart_demo_inventory_summary: counts and public demo QA.
-- Counts reconcile to upstream. Fictional data. Not a real organization.
select
    (select count(*) from {{ ref('stg_demo_assets') }}) as asset_count,
    (select count(*) from {{ ref('stg_demo_activities') }}) as activity_count,
    (select count(*) from {{ ref('stg_demo_vendors') }}) as vendor_count,
    (select count(*) from {{ ref('stg_demo_retention') }}) as retention_rule_count,
    (select count(*) from {{ ref('int_demo_activity_links') }}) as linked_activity_count,
    (select count(*) from {{ ref('mart_demo_ropa') }}) as ropa_row_count,
    (select count(*) from {{ ref('int_demo_activity_links') }} where asset_missing or vendor_missing or retention_missing) as unresolved_reference_count
