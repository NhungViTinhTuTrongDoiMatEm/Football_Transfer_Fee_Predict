{{ config(materialized='table') }}

SELECT
    league_id,
    name,
    country,
    logo
FROM {{ ref('stg_leagues') }}
