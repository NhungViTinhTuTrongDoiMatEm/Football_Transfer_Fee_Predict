{{ config(materialized='table') }}

-- Chỉ lấy các bản ghi bị lỗi số phút thi đấu để cách ly đối soát
SELECT *
FROM {{ ref('int_player_statistics_aggregated') }}
WHERE (games_minutes > (games_appearances * 120) AND games_appearances > 0)
