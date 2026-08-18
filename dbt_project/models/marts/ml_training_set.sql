{{ config(materialized='view') }}

WITH seasonal_aggregated_stats AS (
    SELECT
        player_id,
        season,
        SUM(games_appearances) AS games_appearances,
        SUM(games_lineups) AS games_lineups,
        SUM(games_minutes) AS games_minutes,
        ROUND(SUM(games_rating * games_minutes) / NULLIF(SUM(games_minutes), 0), 2) AS games_rating,
        SUM(goals_total) AS goals_total,
        SUM(goals_assists) AS goals_assists,
        SUM(shots_total) AS shots_total,
        SUM(shots_on) AS shots_on,
        SUM(passes_total) AS passes_total,
        SUM(passes_key) AS passes_key,
        SUM(tackles_total) AS tackles_total,
        SUM(tackles_interceptions) AS tackles_interceptions,
        SUM(duels_total) AS duels_total,
        SUM(duels_won) AS duels_won,
        SUM(dribbles_attempts) AS dribbles_attempts,
        SUM(dribbles_success) AS dribbles_success,
        SUM(fouls_drawn) AS fouls_drawn,
        SUM(fouls_committed) AS fouls_committed,
        SUM(cards_yellow) AS cards_yellow,
        SUM(cards_red) AS cards_red,
        SUM(penalty_scored) AS penalty_scored,
        MAX(CASE WHEN league_id = 1 THEN 1 ELSE 0 END) AS is_world_cup
    FROM {{ ref('fact_player_statistics') }}
    GROUP BY player_id, season
),

transfers_with_next_year AS (
    SELECT
        t.player_id,
        t.player_name,
        t.from_team_id,
        t.from_team_name,
        t.to_team_id,
        t.to_team_name,
        t.transfer_date,
        t.transfer_fee_millions,
        EXTRACT(YEAR FROM t.transfer_date)::INT - 1 AS target_stats_season
    FROM {{ ref('fact_player_transfers') }} t
    WHERE t.transfer_fee_millions > 0
)

SELECT
    tr.player_id,
    tr.player_name,
    p.age,
    p.nationality,
    -- Lấy vị trí thi đấu chính thức đầu tiên trong mùa giải của cầu thủ làm đặc trưng
    (
        SELECT games_position 
        FROM {{ ref('fact_player_statistics') }} fps 
        WHERE fps.player_id = tr.player_id AND fps.season = tr.target_stats_season 
        LIMIT 1
    ) AS position,
    tr.target_stats_season AS stats_season,
    s.is_world_cup,
    s.games_appearances,
    s.games_lineups,
    s.games_minutes,
    s.games_rating,
    s.goals_total,
    s.goals_assists,
    s.shots_total,
    s.shots_on,
    s.passes_total,
    s.passes_key,
    s.tackles_total,
    s.tackles_interceptions,
    s.duels_total,
    s.duels_won,
    s.dribbles_attempts,
    s.dribbles_success,
    s.fouls_drawn,
    s.fouls_committed,
    s.cards_yellow,
    s.cards_red,
    s.penalty_scored,
    tr.transfer_date,
    tr.from_team_name,
    tr.to_team_name,
    tr.transfer_fee_millions AS target_transfer_fee_m_eur
FROM transfers_with_next_year tr
JOIN {{ ref('dim_players') }} p ON tr.player_id = p.player_id
JOIN seasonal_aggregated_stats s ON tr.player_id = s.player_id AND tr.target_stats_season = s.season
WHERE s.games_rating > 0

