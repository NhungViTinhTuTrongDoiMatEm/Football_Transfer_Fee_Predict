{{ config(materialized='table') }}

-- Chỉ lấy các bản ghi có số phút thi đấu hợp lý
SELECT *
FROM {{ ref('int_player_statistics_aggregated') }}
WHERE NOT (games_minutes > (games_appearances * 120) AND games_appearances > 0)
