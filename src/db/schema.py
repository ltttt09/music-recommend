"""
SQLite database schema for the music recommender.

Tables:
- artists: artist metadata (name, genres, country)
- tracks: track metadata (name, album, year, duration, genre)
- users: user profiles (preferences, join_date)
- listening_history: user-track interactions with timestamps
- feedback: user likes/dislikes on recommendations
- playlists: user-created or system-generated playlists
- playlist_tracks: many-to-many playlist-track mapping
"""

import os
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = Path(os.getenv("MUSIC_DB_PATH", DB_DIR / "music_recommender.db"))

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    genres TEXT DEFAULT '',       -- comma-separated genre tags
    country TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist_id INTEGER NOT NULL,
    album TEXT DEFAULT '',
    year INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    genre TEXT DEFAULT '',
    popularity REAL DEFAULT 0.0,
    energy REAL DEFAULT 0.0,       -- 0-1 audio feature
    danceability REAL DEFAULT 0.0,
    valence REAL DEFAULT 0.0,      -- mood (0=sad, 1=happy)
    tempo REAL DEFAULT 0.0,        -- BPM
    image_url TEXT DEFAULT '',
    preview_url TEXT DEFAULT '',
    source TEXT DEFAULT 'itunes',
    external_id TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    license TEXT DEFAULT '',
    audio_type TEXT DEFAULT 'preview',
    language TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    preferred_genres TEXT DEFAULT '',
    password_hash TEXT DEFAULT '',
    salt TEXT DEFAULT '',
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listening_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    listened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    source TEXT DEFAULT 'organic',   -- organic / recommendation
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    rating INTEGER DEFAULT 0,       -- 1=like, -1=dislike, 0=neutral
    model_name TEXT DEFAULT '',
    skip_count INTEGER DEFAULT 0,
    muted_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE(user_id, track_id, model_name)
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    is_system BOOLEAN DEFAULT 0,
    seed_track_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (seed_track_id) REFERENCES tracks(id)
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE(playlist_id, track_id)
);

CREATE INDEX IF NOT EXISTS idx_history_user ON listening_history(user_id, listened_at);
CREATE INDEX IF NOT EXISTS idx_history_track ON listening_history(track_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks ON playlist_tracks(playlist_id);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE(user_id, track_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_track ON comments(track_id);

CREATE TABLE IF NOT EXISTS user_playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    is_public INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES user_playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE(playlist_id, track_id)
);

CREATE INDEX IF NOT EXISTS idx_upl_user ON user_playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_uplt_playlist ON user_playlist_tracks(playlist_id);

CREATE TABLE IF NOT EXISTS recommendation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    track_id INTEGER NOT NULL,
    model_name TEXT DEFAULT '',
    score REAL DEFAULT 0.0,
    source_models TEXT DEFAULT '',
    reason TEXT DEFAULT '',
    request_context TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

CREATE INDEX IF NOT EXISTS idx_rec_logs_user ON recommendation_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rec_logs_track ON recommendation_logs(track_id);

CREATE TABLE IF NOT EXISTS user_profile_cache (
    user_id INTEGER PRIMARY KEY,
    top_genres TEXT DEFAULT '',
    top_artists TEXT DEFAULT '',
    disliked_genres TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS track_profile_cache (
    track_id INTEGER PRIMARY KEY,
    profile_json TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    precision_at_10 REAL DEFAULT 0.0,
    recall_at_10 REAL DEFAULT 0.0,
    coverage REAL DEFAULT 0.0,
    diversity REAL DEFAULT 0.0,
    sample_users INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    imported_tracks INTEGER DEFAULT 0,
    message TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_id TEXT DEFAULT '',
    action_type TEXT NOT NULL,
    entity_type TEXT DEFAULT '',
    entity_id INTEGER,
    status TEXT DEFAULT '',
    page_url TEXT DEFAULT '',
    message TEXT DEFAULT '',
    metadata TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_action_logs_user ON user_action_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_action_logs_type ON user_action_logs(action_type, created_at);
"""

TRACK_MIGRATIONS = {
    "source": "TEXT DEFAULT 'itunes'",
    "external_id": "TEXT DEFAULT ''",
    "source_url": "TEXT DEFAULT ''",
    "license": "TEXT DEFAULT ''",
    "audio_type": "TEXT DEFAULT 'preview'",
    "language": "TEXT DEFAULT ''",
}

FEEDBACK_MIGRATIONS = {
    "skip_count": "INTEGER DEFAULT 0",
    "muted_until": "TIMESTAMP",
}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str):
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def run_migrations(conn: sqlite3.Connection):
    """Apply lightweight schema migrations for existing SQLite databases."""
    for column, definition in TRACK_MIGRATIONS.items():
        _ensure_column(conn, "tracks", column, definition)
    for column, definition in FEEDBACK_MIGRATIONS.items():
        _ensure_column(conn, "feedback", column, definition)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source, external_id)")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with WAL mode and foreign keys enabled."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    run_migrations(conn)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")
