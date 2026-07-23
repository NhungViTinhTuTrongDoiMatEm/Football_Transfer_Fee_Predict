{{ config(materialized='view') }}

WITH flattened_transfers AS (
    SELECT
        (data_raw->'player'->>'id')::INT AS player_id,
        data_raw->'player'->>'name' AS player_name,
        jsonb_array_elements(data_raw->'transfers') AS transfer_item,
        extracted_at
    FROM {{ source('raw_football', 'staging_transfers_raw') }}
)

SELECT
    player_id,
    player_name,
    (transfer_item->>'date')::DATE AS transfer_date,
    transfer_item->>'type' AS transfer_type,
    (transfer_item->'teams'->'in'->>'id')::INT AS to_team_id,
    transfer_item->'teams'->'in'->>'name' AS to_team_name,
    (transfer_item->'teams'->'out'->>'id')::INT AS from_team_id,
    transfer_item->'teams'->'out'->>'name' AS from_team_name,
    extracted_at
FROM flattened_transfers
