{{ config(materialized='table') }}

SELECT
    player_id,
    name,
    firstname,
    lastname,
    age,
    nationality,
    photo
FROM {{ ref('stg_players') }}
