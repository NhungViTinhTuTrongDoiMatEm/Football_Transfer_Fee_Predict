{{ config(materialized='view') }}

WITH transfers_with_next_year AS (
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
    s.games_position AS position,
    s.league_id AS stats_league_id,
    s.season AS stats_season,
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
JOIN {{ ref('fact_player_statistics') }} s ON tr.player_id = s.player_id AND tr.target_stats_season = s.season
