{{ config(materialized='ephemeral') }}

WITH aggregated_fixtures AS (
    SELECT
        fp.player_id,
        fp.team_id,
        fp.league_id,
        fp.season,
        fp.position AS games_position,
        COUNT(fp.fixture_id) AS games_appearances,
        SUM(CASE WHEN NOT fp.is_substitute THEN 1 ELSE 0 END) AS games_lineups,
        SUM(fp.minutes_played) AS games_minutes,
        SUM(fp.rating * fp.minutes_played) AS total_rating_minutes, -- Phục vụ tính điểm trung bình có trọng số
        SUM(fp.goals) AS goals_total,
        SUM(fp.assists) AS goals_assists,
        SUM(fp.shots_total) AS shots_total,
        SUM(fp.shots_on) AS shots_on,
        SUM(fp.passes_total) AS passes_total,
        SUM(fp.passes_key) AS passes_key,
        SUM(fp.tackles_total) AS tackles_total,
        SUM(fp.tackles_interceptions) AS tackles_interceptions,
        SUM(fp.duels_total) AS duels_total,
        SUM(fp.duels_won) AS duels_won,
        SUM(fp.dribbles_attempts) AS dribbles_attempts,
        SUM(fp.dribbles_success) AS dribbles_success,
        SUM(fp.fouls_drawn) AS fouls_drawn,
        SUM(fp.fouls_committed) AS fouls_committed,
        SUM(fp.cards_yellow) AS cards_yellow,
        SUM(fp.cards_red) AS cards_red,
        SUM(fp.penalty_scored) AS penalty_scored,
        MAX(fp.extracted_at) AS last_updated
    FROM {{ ref('stg_fixture_players') }} fp
    JOIN {{ ref('stg_player_statistics') }} ps 
        ON fp.player_id = ps.player_id 
        AND fp.team_id = ps.team_id 
        AND fp.league_id = ps.league_id 
        AND fp.season = ps.season
    -- Chỉ cộng dồn các trận đấu cào sau thời điểm cào dữ liệu gốc của giải đấu để tránh trùng lặp
    WHERE fp.extracted_at > ps.extracted_at
    GROUP BY fp.player_id, fp.team_id, fp.league_id, fp.season, fp.position
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
    COALESCE(ss.player_id, af.player_id) AS player_id,
    COALESCE(ss.team_id, af.team_id) AS team_id,
    COALESCE(ss.league_id, af.league_id) AS league_id,
    COALESCE(ss.season, af.season) AS season,
    COALESCE(ss.games_position, af.games_position) AS games_position,
    (COALESCE(ss.games_appearances, 0) + COALESCE(af.games_appearances, 0)) AS games_appearances,
    (COALESCE(ss.games_lineups, 0) + COALESCE(af.games_lineups, 0)) AS games_lineups,
    (COALESCE(ss.games_minutes, 0) + COALESCE(af.games_minutes, 0)) AS games_minutes,
    -- Tính điểm trung bình cộng có trọng số dựa trên số phút đá thực tế
    CASE 
        WHEN (COALESCE(ss.games_minutes, 0) + COALESCE(af.games_minutes, 0)) > 0 THEN
            ROUND(
                ((COALESCE(ss.games_rating, 0.00) * COALESCE(ss.games_minutes, 0)) + COALESCE(af.total_rating_minutes, 0.00)) / 
                (COALESCE(ss.games_minutes, 0) + COALESCE(af.games_minutes, 0)), 
                2
            )
        ELSE 0.00
    END AS games_rating,
    (COALESCE(ss.goals_total, 0) + COALESCE(af.goals_total, 0)) AS goals_total,
    (COALESCE(ss.goals_assists, 0) + COALESCE(af.goals_assists, 0)) AS goals_assists,
    (COALESCE(ss.shots_total, 0) + COALESCE(af.shots_total, 0)) AS shots_total,
    (COALESCE(ss.shots_on, 0) + COALESCE(af.shots_on, 0)) AS shots_on,
    (COALESCE(ss.passes_total, 0) + COALESCE(af.passes_total, 0)) AS passes_total,
    (COALESCE(ss.passes_key, 0) + COALESCE(af.passes_key, 0)) AS passes_key,
    (COALESCE(ss.tackles_total, 0) + COALESCE(af.tackles_total, 0)) AS tackles_total,
    (COALESCE(ss.tackles_interceptions, 0) + COALESCE(af.tackles_interceptions, 0)) AS tackles_interceptions,
    (COALESCE(ss.duels_total, 0) + COALESCE(af.duels_total, 0)) AS duels_total,
    (COALESCE(ss.duels_won, 0) + COALESCE(af.duels_won, 0)) AS duels_won,
    (COALESCE(ss.dribbles_attempts, 0) + COALESCE(af.dribbles_attempts, 0)) AS dribbles_attempts,
    (COALESCE(ss.dribbles_success, 0) + COALESCE(af.dribbles_success, 0)) AS dribbles_success,
    (COALESCE(ss.fouls_drawn, 0) + COALESCE(af.fouls_drawn, 0)) AS fouls_drawn,
    (COALESCE(ss.fouls_committed, 0) + COALESCE(af.fouls_committed, 0)) AS fouls_committed,
    (COALESCE(ss.cards_yellow, 0) + COALESCE(af.cards_yellow, 0)) AS cards_yellow,
    (COALESCE(ss.cards_red, 0) + COALESCE(af.cards_red, 0)) AS cards_red,
    (COALESCE(ss.penalty_scored, 0) + COALESCE(af.penalty_scored, 0)) AS penalty_scored,
    COALESCE(af.last_updated, ss.last_updated) AS last_updated
FROM seasonal_stats ss
FULL OUTER JOIN aggregated_fixtures af 
    ON ss.player_id = af.player_id 
    AND ss.team_id = af.team_id 
    AND ss.league_id = af.league_id 
    AND ss.season = af.season
