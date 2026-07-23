{{ config(materialized='view') }}

SELECT DISTINCT ON (
    (data_raw->'player'->>'id')::INT,
    (data_raw->'statistics'->0->'team'->>'id')::INT,
    (data_raw->'statistics'->0->'league'->>'id')::INT,
    (data_raw->'statistics'->0->'league'->>'season')::INT
)
    (data_raw->'player'->>'id')::INT AS player_id,
    (data_raw->'statistics'->0->'team'->>'id')::INT AS team_id,
    (data_raw->'statistics'->0->'league'->>'id')::INT AS league_id,
    (data_raw->'statistics'->0->'league'->>'season')::INT AS season,
    COALESCE((data_raw->'statistics'->0->'games'->>'position')::VARCHAR, 'Unknown') AS games_position,
    COALESCE((data_raw->'statistics'->0->'games'->>'appearences')::INT, 0) AS games_appearances,
    COALESCE((data_raw->'statistics'->0->'games'->>'lineups')::INT, 0) AS games_lineups,
    COALESCE((data_raw->'statistics'->0->'games'->>'minutes')::INT, 0) AS games_minutes,
    COALESCE((data_raw->'statistics'->0->'games'->>'rating')::NUMERIC(5,2), 0.00) AS games_rating,
    COALESCE((data_raw->'statistics'->0->'goals'->>'total')::INT, 0) AS goals_total,
    COALESCE((data_raw->'statistics'->0->'goals'->>'assists')::INT, 0) AS goals_assists,
    COALESCE((data_raw->'statistics'->0->'shots'->>'total')::INT, 0) AS shots_total,
    COALESCE((data_raw->'statistics'->0->'shots'->>'on')::INT, 0) AS shots_on,
    COALESCE((data_raw->'statistics'->0->'passes'->>'total')::INT, 0) AS passes_total,
    COALESCE((data_raw->'statistics'->0->'passes'->>'key')::INT, 0) AS passes_key,
    COALESCE((data_raw->'statistics'->0->'tackles'->>'total')::INT, 0) AS tackles_total,
    COALESCE((data_raw->'statistics'->0->'tackles'->>'interceptions')::INT, 0) AS tackles_interceptions,
    COALESCE((data_raw->'statistics'->0->'duels'->>'total')::INT, 0) AS duels_total,
    COALESCE((data_raw->'statistics'->0->'duels'->>'won')::INT, 0) AS duels_won,
    COALESCE((data_raw->'statistics'->0->'dribbles'->>'attempts')::INT, 0) AS dribbles_attempts,
    COALESCE((data_raw->'statistics'->0->'dribbles'->>'success')::INT, 0) AS dribbles_success,
    COALESCE((data_raw->'statistics'->0->'fouls'->>'drawn')::INT, 0) AS fouls_drawn,
    COALESCE((data_raw->'statistics'->0->'fouls'->>'committed')::INT, 0) AS fouls_committed,
    COALESCE((data_raw->'statistics'->0->'cards'->>'yellow')::INT, 0) AS cards_yellow,
    COALESCE((data_raw->'statistics'->0->'cards'->>'red')::INT, 0) AS cards_red,
    COALESCE((data_raw->'statistics'->0->'penalty'->>'scored')::INT, 0) AS penalty_scored,
    extracted_at
FROM {{ source('raw_football', 'staging_players_raw') }}
WHERE data_raw->'statistics'->0 IS NOT NULL
