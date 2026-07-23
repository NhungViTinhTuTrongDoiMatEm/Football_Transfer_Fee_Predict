{{ config(
    materialized='incremental',
    unique_key=['player_id', 'team_id', 'league_id', 'season']
) }}

SELECT
    player_id,
    team_id,
    league_id,
    season,
    games_position,
    games_appearances,
    games_lineups,
    games_minutes,
    games_rating,
    goals_total,
    goals_assists,
    shots_total,
    shots_on,
    passes_total,
    passes_key,
    tackles_total,
    tackles_interceptions,
    duels_total,
    duels_won,
    dribbles_attempts,
    dribbles_success,
    fouls_drawn,
    fouls_committed,
    cards_yellow,
    cards_red,
    penalty_scored,
    extracted_at AS last_updated
FROM {{ ref('stg_player_statistics') }}

{% if is_incremental() %}
  WHERE extracted_at > (SELECT MAX(last_updated) FROM {{ this }})
{% endif %}
