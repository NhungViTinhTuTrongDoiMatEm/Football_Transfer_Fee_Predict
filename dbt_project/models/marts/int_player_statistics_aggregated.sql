{{ config(materialized='ephemeral') }}

-- 1. Gom nhóm toàn bộ dữ liệu trận đấu cào chi tiết theo (player_id, season)
WITH fixtures_by_player_season AS (
    SELECT
        fp.player_id,
        fp.season,
        -- Ưu tiên CLB hợp lệ (có trong dim_teams và league_id != 1) và thi đấu nhiều phút nhất trong mùa
        (ARRAY_AGG(fp.team_id ORDER BY (fp.league_id != 1 AND dt.team_id IS NOT NULL) DESC, fp.minutes_played DESC))[1] AS team_id,
        (ARRAY_AGG(fp.league_id ORDER BY (fp.league_id != 1 AND dl.league_id IS NOT NULL) DESC, fp.minutes_played DESC))[1] AS league_id,
        (ARRAY_AGG(fp.position ORDER BY (fp.league_id != 1) DESC, fp.minutes_played DESC))[1] AS games_position,
        COUNT(fp.fixture_id) AS games_appearances,
        SUM(CASE WHEN NOT fp.is_substitute THEN 1 ELSE 0 END) AS games_lineups,
        SUM(fp.minutes_played) AS games_minutes,
        SUM(fp.rating * fp.minutes_played) AS total_rating_minutes,
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
    JOIN {{ ref('stg_players') }} p ON fp.player_id = p.player_id
    LEFT JOIN {{ ref('stg_teams') }} dt ON fp.team_id = dt.team_id
    LEFT JOIN {{ ref('stg_leagues') }} dl ON fp.league_id = dl.league_id
    WHERE fp.player_id > 0
    GROUP BY fp.player_id, fp.season
),

-- 2. Gom nhóm toàn bộ dữ liệu tổng kết mùa gốc theo (player_id, season)
seasonal_by_player_season AS (
    SELECT
        ps.player_id,
        ps.season,
        -- Ưu tiên CLB hợp lệ (có trong dim_teams và league_id != 1) và thi đấu nhiều phút nhất trong mùa
        (ARRAY_AGG(ps.team_id ORDER BY (ps.league_id != 1 AND dt.team_id IS NOT NULL) DESC, ps.games_minutes DESC))[1] AS team_id,
        (ARRAY_AGG(ps.league_id ORDER BY (ps.league_id != 1 AND dl.league_id IS NOT NULL) DESC, ps.games_minutes DESC))[1] AS league_id,
        (ARRAY_AGG(ps.games_position ORDER BY (ps.league_id != 1) DESC, ps.games_minutes DESC))[1] AS games_position,
        SUM(ps.games_appearances) AS games_appearances,
        SUM(ps.games_lineups) AS games_lineups,
        SUM(ps.games_minutes) AS games_minutes,
        SUM(ps.games_rating * ps.games_minutes) AS total_rating_minutes,
        SUM(ps.goals_total) AS goals_total,
        SUM(ps.goals_assists) AS goals_assists,
        SUM(ps.shots_total) AS shots_total,
        SUM(ps.shots_on) AS shots_on,
        SUM(ps.passes_total) AS passes_total,
        SUM(ps.passes_key) AS passes_key,
        SUM(ps.tackles_total) AS tackles_total,
        SUM(ps.tackles_interceptions) AS tackles_interceptions,
        SUM(ps.duels_total) AS duels_total,
        SUM(ps.duels_won) AS duels_won,
        SUM(ps.dribbles_attempts) AS dribbles_attempts,
        SUM(ps.dribbles_success) AS dribbles_success,
        SUM(ps.fouls_drawn) AS fouls_drawn,
        SUM(ps.fouls_committed) AS fouls_committed,
        SUM(ps.cards_yellow) AS cards_yellow,
        SUM(ps.cards_red) AS cards_red,
        SUM(ps.penalty_scored) AS penalty_scored,
        MAX(ps.extracted_at) AS last_updated
    FROM {{ ref('stg_player_statistics') }} ps
    LEFT JOIN {{ ref('stg_teams') }} dt ON ps.team_id = dt.team_id
    LEFT JOIN {{ ref('stg_leagues') }} dl ON ps.league_id = dl.league_id
    WHERE ps.player_id > 0
    GROUP BY ps.player_id, ps.season
)

-- 3. Hợp nhất hai nguồn theo đúng 2 khóa cốt lõi (player_id, season)
SELECT
    COALESCE(ss.player_id, af.player_id) AS player_id,
    COALESCE(af.team_id, ss.team_id) AS team_id,
    COALESCE(af.league_id, ss.league_id) AS league_id,
    COALESCE(ss.season, af.season) AS season,
    COALESCE(af.games_position, ss.games_position) AS games_position,
    (COALESCE(ss.games_appearances, 0) + COALESCE(af.games_appearances, 0)) AS games_appearances,
    (COALESCE(ss.games_lineups, 0) + COALESCE(af.games_lineups, 0)) AS games_lineups,
    (COALESCE(ss.games_minutes, 0) + COALESCE(af.games_minutes, 0)) AS games_minutes,
    -- Điểm đánh giá trung bình có trọng số theo số phút thi đấu
    CASE 
        WHEN (COALESCE(ss.games_minutes, 0) + COALESCE(af.games_minutes, 0)) > 0 THEN
            ROUND(
                ((COALESCE(ss.total_rating_minutes, 0.00)) + COALESCE(af.total_rating_minutes, 0.00)) / 
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
FROM seasonal_by_player_season ss
FULL OUTER JOIN fixtures_by_player_season af 
    ON ss.player_id = af.player_id 
    AND ss.season = af.season
