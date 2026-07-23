{{ config(materialized='view') }}

SELECT DISTINCT ON ((data_raw->'team'->>'id')::INT)
    (data_raw->'team'->>'id')::INT AS team_id,
    data_raw->'team'->>'name' AS name,
    data_raw->'team'->>'code' AS code,
    data_raw->'team'->>'logo' AS logo,
    extracted_at
FROM {{ source('raw_football', 'staging_teams_raw') }}
