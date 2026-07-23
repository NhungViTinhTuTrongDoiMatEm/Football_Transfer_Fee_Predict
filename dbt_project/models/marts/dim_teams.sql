{{ config(materialized='table') }}

WITH teams_from_teams_raw AS (
    SELECT
        team_id,
        name,
        code,
        logo
    FROM {{ ref('stg_teams') }}
),

teams_from_players_raw AS (
    SELECT DISTINCT ON ((data_raw->'statistics'->0->'team'->>'id')::INT)
        (data_raw->'statistics'->0->'team'->>'id')::INT AS team_id,
        data_raw->'statistics'->0->'team'->>'name' AS name,
        NULL::VARCHAR AS code,
        data_raw->'statistics'->0->'team'->>'logo' AS logo
    FROM {{ source('raw_football', 'staging_players_raw') }}
    WHERE data_raw->'statistics'->0 IS NOT NULL
),

unioned_teams AS (
    SELECT * FROM teams_from_teams_raw
    UNION ALL
    SELECT * FROM teams_from_players_raw
)

SELECT DISTINCT ON (team_id)
    team_id,
    name,
    code,
    logo
FROM unioned_teams
ORDER BY team_id, code NULLS LAST
