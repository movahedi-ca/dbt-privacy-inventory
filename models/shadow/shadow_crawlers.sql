-- Shadow model for the crawlers family. Source: TASK-010 snapshot rows
-- (src/data/crawlers.json at 54642b3267c0b11d5e6959077de56e4abf251c25).
-- Stable row key: row_key = token, the snapshot key field.
select
    row_key,
    token,
    operator,
    purpose,
    status,
    first_documented,
    honors_robots_txt,
    nullif(ip_ranges_url, '') as ip_ranges_url,
    vendor_doc_url,
    verified_at,
    nullif(notes, '') as notes,
    nullif(source_note, '') as source_note,
    nullif(successor, '') as successor
from {{ ref('shadow_src_crawlers') }}
