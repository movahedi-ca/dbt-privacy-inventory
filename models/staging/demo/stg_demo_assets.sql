-- stg_demo_assets: standardize synthetic asset IDs and classifications.
-- Fictional data. Not a real organization.
select
    cast(asset_id as varchar) as asset_id,
    trim(asset_name) as asset_name,
    lower(trim(classification)) as classification,
    trim(owner) as owner,
    lower(trim(data_category)) as data_category
from {{ ref('assets') }}
