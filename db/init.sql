-- Initialize Staging Tables for ELT Football Pipeline

CREATE TABLE IF NOT EXISTS staging_leagues_raw (
    id SERIAL PRIMARY KEY,
    league_id INT NOT NULL,
    season INT NOT NULL,
    data_raw JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_league_season UNIQUE (league_id, season)
);

CREATE TABLE IF NOT EXISTS staging_teams_raw (
    id SERIAL PRIMARY KEY,
    team_id INT NOT NULL,
    league_id INT NOT NULL,
    season INT NOT NULL,
    data_raw JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_team_league_season UNIQUE (team_id, league_id, season)
);

CREATE TABLE IF NOT EXISTS staging_players_raw (
    id SERIAL PRIMARY KEY,
    player_id INT NOT NULL,
    league_id INT NOT NULL,
    season INT NOT NULL,
    data_raw JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_player_league_season UNIQUE (player_id, league_id, season)
);

-- Create GIN Indexes for efficient JSONB querying
CREATE INDEX IF NOT EXISTS idx_staging_leagues_raw_data ON staging_leagues_raw USING gin (data_raw);
CREATE INDEX IF NOT EXISTS idx_staging_teams_raw_data ON staging_teams_raw USING gin (data_raw);
CREATE INDEX IF NOT EXISTS idx_staging_players_raw_data ON staging_players_raw USING gin (data_raw);

CREATE TABLE IF NOT EXISTS staging_transfers_raw (
    player_id INT PRIMARY KEY,
    data_raw JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_staging_transfers_raw_data ON staging_transfers_raw USING gin (data_raw);

CREATE TABLE IF NOT EXISTS staging_fixture_players_raw (
    fixture_id INT PRIMARY KEY,
    league_id INT,
    season INT,
    data_raw JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_staging_fixture_players_raw_data ON staging_fixture_players_raw USING gin (data_raw);
