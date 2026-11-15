-- Shadow model for the Law 25 checks family. Source: TASK-010 snapshot
-- rows (src/components/interactive/PolicyGrader.tsx checks at
-- 54642b3267c0b11d5e6959077de56e4abf251c25).
-- Stable row key: row_key = source check id. The live API id is the
-- generator-derived form "law25-" plus this id.
-- The source evaluate field is a function, not data; the TASK-010
-- extractor dropped it by name, so no evaluate column exists here.
select
    row_key,
    id,
    title,
    law,
    weight,
    blurb
from {{ ref('shadow_src_law25') }}
