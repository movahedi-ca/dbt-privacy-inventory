-- Singular test: the ROPA mart must hold exactly one row per activity.
-- Returns rows (fails) when the counts differ. Passes on zero rows.
select
    (select count(*) from {{ ref('mart_demo_ropa') }}) as ropa_rows,
    (select count(*) from {{ ref('stg_demo_activities') }}) as activity_rows
where ropa_rows != activity_rows
