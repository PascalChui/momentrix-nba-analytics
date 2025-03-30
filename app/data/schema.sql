-- Schéma de base de données pour Momentrix NBA Analytics

PRAGMA foreign_keys = ON;

-- Table des équipes
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    conference TEXT NOT NULL,
    division TEXT NOT NULL,
    logo_url TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des joueurs
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    jersey_number TEXT,
    position TEXT,
    height TEXT,
    weight TEXT,
    birth_date TIMESTAMP,
    college TEXT,
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

-- Table des matchs
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT DEFAULT 'scheduled',
    arena TEXT,
    season TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams (id),
    FOREIGN KEY (away_team_id) REFERENCES teams (id)
);

-- Table des quart-temps
CREATE TABLE IF NOT EXISTS game_quarters (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    quarter INTEGER NOT NULL, -- 1-4 pour quart-temps, 5+ pour prolongations
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games (id)
);

-- Table des badges attribués aux équipes
CREATE TABLE IF NOT EXISTS team_badges (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    badge_code TEXT NOT NULL,
    attribution_date TIMESTAMP NOT NULL,
    justification TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

-- Table des définitions de badges
CREATE TABLE IF NOT EXISTS badge_definitions (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    persistence TEXT NOT NULL, -- 'dynamic', 'semi-permanent', 'permanent'
    color_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des prédictions de matchs
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    home_win_probability REAL NOT NULL,
    predicted_home_score INTEGER,
    predicted_away_score INTEGER,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_level REAL DEFAULT 0.0,
    key_factors TEXT,
    FOREIGN KEY (game_id) REFERENCES games (id)
);

-- Table des profils de performance par quart-temps
CREATE TABLE IF NOT EXISTS quarter_profiles (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    quarter INTEGER NOT NULL, -- 1-4
    avg_points_for REAL NOT NULL,
    avg_points_against REAL NOT NULL,
    std_points_for REAL NOT NULL,
    std_points_against REAL NOT NULL,
    win_percentage REAL NOT NULL,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams (id),
    UNIQUE(team_id, quarter)
);

-- Table de cache des données API
CREATE TABLE IF NOT EXISTS api_cache (
    id INTEGER PRIMARY KEY,
    endpoint TEXT NOT NULL,
    parameters TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry TIMESTAMP NOT NULL
);

-- Table des statistiques d'équipe par match
CREATE TABLE IF NOT EXISTS team_game_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    points INTEGER NOT NULL,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    field_goals_percentage REAL,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    three_pointers_percentage REAL,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    free_throws_percentage REAL,
    rebounds_offensive INTEGER,
    rebounds_defensive INTEGER,
    rebounds_total INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    fast_break_points INTEGER,
    points_in_paint INTEGER,
    second_chance_points INTEGER,
    points_off_turnovers INTEGER,
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (team_id) REFERENCES teams (id),
    UNIQUE(game_id, team_id)
);

-- Insertions de données initiales pour les définitions de badges
INSERT OR IGNORE INTO badge_definitions (code, name, description, category, persistence, color_code) VALUES
('SCORER', 'Scorer', 'Équipes dépassant 25 points par quart-temps dans plus de 60% des cas', 'offensive', 'dynamic', '#DC3545'),
('FAST_BREAK', 'Fast Break', 'Équipes avec plus de 15 points en contre-attaque par match en moyenne', 'offensive', 'dynamic', '#FD7E14'),
('DEFENSIVE', 'Defensive', 'Équipes limitant leurs adversaires à moins de 20 points par quart-temps dans plus de 50% des cas', 'defensive', 'dynamic', '#F7931E'),
('SOLID', 'Solid', 'Équipes maintenant un différentiel défensif positif dans plus de 70% des quart-temps', 'defensive', 'dynamic', '#17A2B8'),
('CONSISTENT', 'Consistent', 'Équipes maintenant un écart-type de performance inférieur à 5 points entre quart-temps', 'consistency', 'semi-permanent', '#28A745'),
('OVERTURNER', 'Overturner', 'Équipes ayant remporté au moins 30% de leurs matchs après avoir été menées de 10 points ou plus', 'performance', 'semi-permanent', '#1A365D'),
('RESISTANT', 'Resistant', 'Équipes ne perdant jamais par plus de 15 points d''écart', 'performance', 'dynamic', '#6610F2'),
('CLUTCH', 'Clutch', 'Équipes avec un différentiel positif dans les 5 dernières minutes des matchs serrés', 'performance', 'dynamic', '#20C997'),
('HOME_FORCE', 'Home Force', 'Équipes gagnant plus de 70% de leurs matchs à domicile', 'performance', 'semi-permanent', '#007BFF'),
('DISAPPOINTMENT', 'Disappointment', 'Équipes avec des performances significativement inférieures aux attentes basées sur leur classement', 'performance', 'semi-permanent', '#6C757D');

-- Création d'index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_games_date ON games (date);
CREATE INDEX IF NOT EXISTS idx_games_teams ON games (home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_game_quarters_game ON game_quarters (game_id);
CREATE INDEX IF NOT EXISTS idx_team_badges_team ON team_badges (team_id);
CREATE INDEX IF NOT EXISTS idx_predictions_game ON predictions (game_id);
CREATE INDEX IF NOT EXISTS idx_quarter_profiles_team ON quarter_profiles (team_id);
CREATE INDEX IF NOT EXISTS idx_api_cache_endpoint ON api_cache (endpoint, parameters);
