-- Shadow model for the enforcement family. Source: TASK-010 snapshot rows
-- (src/data/cai-enforcement.json at 54642b3267c0b11d5e6959077de56e4abf251c25).
-- Source rows carry no id; the API id is generator-derived.
-- Stable row key: row_key = source_url, unique across the source set.
select
    row_key,
    date,
    respondent,
    issue,
    type,
    outcome,
    penalty_cad,
    source_url,
    source_label,
    notes,
    regulator
from {{ ref('shadow_src_enforcement') }}
