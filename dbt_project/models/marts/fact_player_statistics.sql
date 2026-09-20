{{ config(materialized='table') }}

-- Chỉ lấy các bản ghi có số phút thi đấu hợp lý và đảm bảo tính toàn vẹn quan hệ
SELECT f.*
FROM {{ ref('int_player_statistics_aggregated') }} f
JOIN {{ ref('dim_players') }} dp ON f.player_id = dp.player_id
JOIN {{ ref('dim_teams') }} dt ON f.team_id = dt.team_id
JOIN {{ ref('dim_leagues') }} dl ON f.league_id = dl.league_id
WHERE NOT (f.games_minutes > (f.games_appearances * 120) AND f.games_appearances > 0)
