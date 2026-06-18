"""
SQLite database schema for SoundMind.

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
DB_PATH = Path(os.getenv("SOUNDMIND_DB_PATH", DB_DIR / "soundmind.db"))


def _has_char_range(text: str, start: int, end: int) -> bool:
    return any(start <= ord(ch) <= end for ch in text)


def infer_language_group(language: str = "", title: str = "", artist: str = "", album: str = "", genre: str = "") -> str:
    """Infer a coarse language group from track metadata.

    iTunes country/storefront codes are not actual song languages. This helper
    stores a normalized field used by filters so the UI does not treat TW/HK
    storefront songs as Chinese unless the song metadata itself supports it.
    """
    code = (language or "").strip().upper()
    text = f"{title or ''} {album or ''}"
    genre_text = genre or ""
    has_cjk = _has_char_range(text, 0x4E00, 0x9FFF)
    has_kana = _has_char_range(text, 0x3040, 0x30FF)
    has_hangul = _has_char_range(text, 0xAC00, 0xD7AF)

    if has_hangul or code in {"KR", "KO"}:
        return "KR"
    if has_kana or code in {"JP", "JA"}:
        return "JP"
    if has_cjk or any(token in genre_text for token in ("华语", "華語", "国语", "國語", "粤语", "粵語")):
        return "ZH"
    if code in {"US", "GB", "CA", "AU", "NZ", "IE"} or any("A" <= ch.upper() <= "Z" for ch in text):
        return "EN"
    if code in {"FR", "ES", "RU", "BR", "PT", "DE", "AR", "SA", "IN"}:
        return {"BR": "PT", "SA": "AR"}.get(code, code)
    return ""

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
    language_group TEXT DEFAULT '',
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
CREATE INDEX IF NOT EXISTS idx_feedback_user_track ON feedback(user_id, track_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
CREATE INDEX IF NOT EXISTS idx_tracks_language ON tracks(language);
CREATE INDEX IF NOT EXISTS idx_tracks_popularity ON tracks(popularity);
CREATE INDEX IF NOT EXISTS idx_tracks_created ON tracks(created_at);
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
    parent_id INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    FOREIGN KEY (parent_id) REFERENCES comments(id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user_track ON favorites(user_id, track_id);
CREATE INDEX IF NOT EXISTS idx_comments_track ON comments(track_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_created ON comments(user_id, created_at);

CREATE TABLE IF NOT EXISTS comment_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    comment_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    UNIQUE(user_id, comment_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_likes_comment ON comment_likes(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_likes_user ON comment_likes(user_id);

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
CREATE INDEX IF NOT EXISTS idx_rec_logs_model_created ON recommendation_logs(model_name, created_at);

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

CREATE TABLE IF NOT EXISTS model_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
CREATE INDEX IF NOT EXISTS idx_action_logs_entity ON user_action_logs(entity_type, entity_id, created_at);

CREATE TABLE IF NOT EXISTS lyrics_cache (
    track_id INTEGER PRIMARY KEY,
    lyrics TEXT DEFAULT '',
    source TEXT DEFAULT '',
    status TEXT DEFAULT 'missing',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
"""

TRACK_MIGRATIONS = {
    "source": "TEXT DEFAULT 'itunes'",
    "external_id": "TEXT DEFAULT ''",
    "source_url": "TEXT DEFAULT ''",
    "license": "TEXT DEFAULT ''",
    "audio_type": "TEXT DEFAULT 'preview'",
    "language": "TEXT DEFAULT ''",
    "language_group": "TEXT DEFAULT ''",
}

FEEDBACK_MIGRATIONS = {
    "skip_count": "INTEGER DEFAULT 0",
    "muted_until": "TIMESTAMP",
}

COMMENT_MIGRATIONS = {
    "parent_id": "INTEGER",
    "deleted_at": "TIMESTAMP",
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
    for column, definition in COMMENT_MIGRATIONS.items():
        _ensure_column(conn, "comments", column, definition)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source, external_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_language ON tracks(language)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_language_group ON tracks(language_group)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_popularity ON tracks(popularity)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_created ON tracks(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_track ON feedback(user_id, track_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user_track ON favorites(user_id, track_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_user_created ON comments(user_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rec_logs_model_created ON recommendation_logs(model_name, created_at)")
    conn.execute("CREATE TABLE IF NOT EXISTS model_config (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_history_user_track_time ON listening_history(user_id, track_id, listened_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_history_track_time ON listening_history(track_id, listened_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_rating_created ON feedback(rating, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_rating_muted ON feedback(user_id, rating, muted_until)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rec_logs_user_model_created ON recommendation_logs(user_id, model_name, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rec_logs_track_created ON recommendation_logs(track_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_action_logs_entity ON user_action_logs(entity_type, entity_id, created_at)")
    rows = conn.execute(
        """SELECT t.id, t.title, t.album, t.genre, t.language, t.language_group, a.name AS artist_name
           FROM tracks t JOIN artists a ON t.artist_id=a.id"""
    ).fetchall()
    for row in rows:
        group = infer_language_group(
            row["language"],
            row["title"],
            row["artist_name"],
            row["album"],
            row["genre"],
        )
        if group != (row["language_group"] or ""):
            conn.execute("UPDATE tracks SET language_group=? WHERE id=?", (group, row["id"]))


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
