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
            WHEN transfer_type ILIKE '€%M' THEN 
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC
            WHEN transfer_type ILIKE '€%K' THEN 
                NULLIF(REGEXP_REPLACE(transfer_type, '[^0-9.]', '', 'g'), '')::NUMERIC / 1000.0
            ELSE 0.00
        END,
        0.00
    ) AS transfer_fee_millions,
    extracted_at AS last_updated
FROM {{ ref('stg_transfers') }}
