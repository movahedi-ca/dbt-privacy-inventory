-- Shadow model for the glossary family. Source: TASK-010 snapshot rows
-- (src/data/glossary.ts at 54642b3267c0b11d5e6959077de56e4abf251c25).
-- Stable row key: row_key = source id, served as the API slug.
-- related_json holds the source related array (label and href pairs)
-- as canonical JSON, so the row stays complete at row level.
select
    row_key,
    id,
    name,
    definition,
    name_fr,
    definition_fr,
    french_completeness_status,
    nullif(related_json, '') as related_json
from {{ ref('shadow_src_glossary') }}
