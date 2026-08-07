{{ config(materialized='table') }}

WITH raw_extracted AS (
    SELECT *,
        -- Chỉ chạy Regex trích xuất số duy nhất 1 lần trên mỗi dòng nếu có chứa chữ số
        CASE 
            WHEN transfer_type ~ '[0-9]' THEN 
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC
            ELSE NULL
        END AS raw_num
    FROM {{ ref('stg_transfers') }}
)

SELECT
    player_id,
    player_name,
    from_team_id,
    from_team_name,
    to_team_id,
    to_team_name,
    transfer_date,
    transfer_type,
    -- Chuẩn hóa phí chuyển nhượng từ số đã trích xuất
    COALESCE(
        CASE 
            WHEN raw_num IS NULL THEN 0.00
            -- Trường hợp chứa M (Triệu Euro)
            WHEN transfer_type ILIKE '%M%' THEN raw_num
            -- Trường hợp chứa K (Nghìn Euro)
            WHEN transfer_type ILIKE '%K%' THEN raw_num / 1000.0
            -- Trường hợp số thuần túy lớn (ví dụ: 500000 -> 0.5M)
            WHEN raw_num >= 1000 THEN raw_num / 1000000.0
            -- Trường hợp số thuần túy nhỏ (ví dụ: 200.00 -> 0.00M)
            ELSE raw_num / 1000000.0
        END,
        0.00
    ) AS transfer_fee_millions,
    extracted_at AS last_updated
FROM raw_extracted
