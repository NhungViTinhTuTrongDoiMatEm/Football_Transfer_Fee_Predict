{{ config(materialized='table') }}

SELECT
    player_id,
    player_name,
    from_team_id,
    from_team_name,
    to_team_id,
    to_team_name,
    transfer_date,
    transfer_type,
    -- Chuẩn hóa phí chuyển nhượng sang triệu Euro (EUR Millions)
    COALESCE(
        CASE 
            -- Trường hợp chứa số và ký tự 'M' hoặc 'm' (ví dụ: € 94M, 2.4M, 73.5M €, &pound; 3M)
            WHEN transfer_type ~ '[0-9]' AND transfer_type ILIKE '%M%' THEN 
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC
            -- Trường hợp chứa số và ký tự 'K' hoặc 'k' (ví dụ: 750K €, € 210K, 250K)
            WHEN transfer_type ~ '[0-9]' AND transfer_type ILIKE '%K%' THEN 
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC / 1000.0
            -- Trường hợp số thuần túy lớn hơn hoặc bằng 1000 (ví dụ: 500000)
            WHEN transfer_type ~ '[0-9]' AND NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC >= 1000 THEN
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC / 1000000.0
            -- Trường hợp số thuần túy nhỏ hơn 1000 (ví dụ: € 200.00)
            WHEN transfer_type ~ '[0-9]' THEN
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC / 1000000.0
            ELSE 0.00
        END,
        0.00
    ) AS transfer_fee_millions,
    extracted_at AS last_updated
FROM {{ ref('stg_transfers') }}
