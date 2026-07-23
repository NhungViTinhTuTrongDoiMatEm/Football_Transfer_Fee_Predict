{{ config(materialized='view') }}

SELECT DISTINCT ON ((data_raw->'player'->>'id')::INT)
    (data_raw->'player'->>'id')::INT AS player_id,
    data_raw->'player'->>'name' AS name,
    data_raw->'player'->>'firstname' AS firstname,
    data_raw->'player'->>'lastname' AS lastname,
    (data_raw->'player'->>'age')::INT AS age,
    data_raw->'player'->>'nationality' AS nationality,
    data_raw->'player'->>'photo' AS photo,
    extracted_at
FROM {{ source('raw_football', 'staging_players_raw') }}
