-- Dữ liệu lỗi là dữ liệu có số phút thi đấu vượt quá số trận ra sân nhân với 120 phút (cho phép bù giờ tối đa)
-- dbt test sẽ cảnh báo thất bại nếu truy vấn này trả về bất kỳ dòng dữ liệu nào.

SELECT 
    player_id,
    season,
    games_appearances,
    games_minutes
FROM {{ ref('fact_player_statistics') }}
WHERE games_minutes > (games_appearances * 120)
  AND games_appearances > 0
