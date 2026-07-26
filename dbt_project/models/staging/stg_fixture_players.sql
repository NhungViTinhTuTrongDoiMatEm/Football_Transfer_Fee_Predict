{{ config(materialized='view') }}

WITH raw_flattened AS (
    SELECT
        fixture_id,
        league_id,
        season,
        jsonb_array_elements(data_raw->'response') AS team_item,
        extracted_at
    FROM {{ source('raw_football', 'staging_fixture_players_raw') }}
),

player_flattened AS (
    SELECT
        fixture_id,
        league_id,
        season,
        (team_item->'team'->>'id')::INT AS team_id,
        team_item->'team'->>'name' AS team_name,
        jsonb_array_elements(team_item->'players') AS player_item,
        extracted_at
    FROM raw_flattened
)

SELECT
    fixture_id,
    league_id,
    season,
    team_id,
    team_name,
    (player_item->'player'->>'id')::INT AS player_id,
    player_item->'player'->>'name' AS player_name,
    -- Chỉ số thi đấu
    COALESCE(player_item->'statistics'->0->'games'->>'position', 'Unknown') AS position,
    COALESCE((player_item->'statistics'->0->'games'->>'minutes')::INT, 0) AS minutes_played,
    COALESCE((player_item->'statistics'->0->'games'->>'rating')::NUMERIC(5,2), 0.00) AS rating,
    COALESCE((player_item->'statistics'->0->'games'->>'substitute')::BOOLEAN, FALSE) AS is_substitute,
    COALESCE((player_item->'statistics'->0->'goals'->>'total')::INT, 0) AS goals,
    COALESCE((player_item->'statistics'->0->'goals'->>'assists')::INT, 0) AS assists,
    COALESCE((player_item->'statistics'->0->'shots'->>'total')::INT, 0) AS shots_total,
    COALESCE((player_item->'statistics'->0->'shots'->>'on')::INT, 0) AS shots_on,
    COALESCE((player_item->'statistics'->0->'passes'->>'total')::INT, 0) AS passes_total,
    COALESCE((player_item->'statistics'->0->'passes'->>'key')::INT, 0) AS passes_key,
    COALESCE((player_item->'statistics'->0->'tackles'->>'total')::INT, 0) AS tackles_total,
    COALESCE((player_item->'statistics'->0->'tackles'->>'interceptions')::INT, 0) AS tackles_interceptions,
    COALESCE((player_item->'statistics'->0->'duels'->>'total')::INT, 0) AS duels_total,
    COALESCE((player_item->'statistics'->0->'duels'->>'won')::INT, 0) AS duels_won,
    COALESCE((player_item->'statistics'->0->'dribbles'->>'attempts')::INT, 0) AS dribbles_attempts,
    COALESCE((player_item->'statistics'->0->'dribbles'->>'success')::INT, 0) AS dribbles_success,
    COALESCE((player_item->'statistics'->0->'fouls'->>'drawn')::INT, 0) AS fouls_drawn,
    COALESCE((player_item->'statistics'->0->'fouls'->>'committed')::INT, 0) AS fouls_committed,
    COALESCE((player_item->'statistics'->0->'cards'->>'yellow')::INT, 0) AS cards_yellow,
    COALESCE((player_item->'statistics'->0->'cards'->>'red')::INT, 0) AS cards_red,
    COALESCE((player_item->'statistics'->0->'penalty'->>'scored')::INT, 0) AS penalty_scored,
    extracted_at
FROM player_flattened
