{{ config(materialized='view') }}

SELECT DISTINCT ON ((data_raw->'league'->>'id')::INT)
    (data_raw->'league'->>'id')::INT AS league_id,
    data_raw->'league'->>'name' AS name,
    data_raw->'country'->>'name' AS country,
    data_raw->'league'->>'logo' AS logo,
    extracted_at
FROM {{ source('raw_football', 'staging_leagues_raw') }}
