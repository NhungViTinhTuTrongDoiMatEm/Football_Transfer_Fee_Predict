{{ config(materialized='table') }}

WITH aggregated_fixtures AS (
    SELECT
        player_id,
        team_id,
        league_id,
        season,
        position AS games_position,
        COUNT(fixture_id) AS games_appearances,
        SUM(CASE WHEN NOT is_substitute THEN 1 ELSE 0 END) AS games_lineups,
        SUM(minutes_played) AS games_minutes,
        ROUND(AVG(rating), 2) AS games_rating,
        SUM(goals) AS goals_total,
        SUM(assists) AS goals_assists,
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
        MAX(extracted_at) AS last_updated
    FROM {{ ref('stg_fixture_players') }}
    GROUP BY player_id, team_id, league_id, season, position
),

seasonal_stats AS (
    SELECT
        player_id,
        team_id,
        league_id,
        season,
        games_position,
        games_appearances,
        games_lineups,
        games_minutes,
        games_rating,
        goals_total,
        goals_assists,
        shots_total,
        shots_on,
        passes_total,
        passes_key,
        tackles_total,
        tackles_interceptions,
        duels_total,
        duels_won,
        dribbles_attempts,
        dribbles_success,
        fouls_drawn,
        fouls_committed,
        cards_yellow,
        cards_red,
        penalty_scored,
        extracted_at AS last_updated
    FROM {{ ref('stg_player_statistics') }}
)

SELECT
    COALESCE(af.player_id, ss.player_id) AS player_id,
    COALESCE(af.team_id, ss.team_id) AS team_id,
    COALESCE(af.league_id, ss.league_id) AS league_id,
    COALESCE(af.season, ss.season) AS season,
    COALESCE(af.games_position, ss.games_position) AS games_position,
    COALESCE(af.games_appearances, ss.games_appearances) AS games_appearances,
    COALESCE(af.games_lineups, ss.games_lineups) AS games_lineups,
    COALESCE(af.games_minutes, ss.games_minutes) AS games_minutes,
    COALESCE(af.games_rating, ss.games_rating) AS games_rating,
    COALESCE(af.goals_total, ss.goals_total) AS goals_total,
    COALESCE(af.goals_assists, ss.goals_assists) AS goals_assists,
    COALESCE(af.shots_total, ss.shots_total) AS shots_total,
    COALESCE(af.shots_on, ss.shots_on) AS shots_on,
    COALESCE(af.passes_total, ss.passes_total) AS passes_total,
    COALESCE(af.passes_key, ss.passes_key) AS passes_key,
    COALESCE(af.tackles_total, ss.tackles_total) AS tackles_total,
    COALESCE(af.tackles_interceptions, ss.tackles_interceptions) AS tackles_interceptions,
    COALESCE(af.duels_total, ss.duels_total) AS duels_total,
    COALESCE(af.duels_won, ss.duels_won) AS duels_won,
    COALESCE(af.dribbles_attempts, ss.dribbles_attempts) AS dribbles_attempts,
    COALESCE(af.dribbles_success, ss.dribbles_success) AS dribbles_success,
    COALESCE(af.fouls_drawn, ss.fouls_drawn) AS fouls_drawn,
    COALESCE(af.fouls_committed, ss.fouls_committed) AS fouls_committed,
    COALESCE(af.cards_yellow, ss.cards_yellow) AS cards_yellow,
    COALESCE(af.cards_red, ss.cards_red) AS cards_red,
    COALESCE(af.penalty_scored, ss.penalty_scored) AS penalty_scored,
    COALESCE(af.last_updated, ss.last_updated) AS last_updated
FROM seasonal_stats ss
FULL OUTER JOIN aggregated_fixtures af 
    ON ss.player_id = af.player_id 
    AND ss.team_id = af.team_id 
    AND ss.league_id = af.league_id 
    AND ss.season = af.season
