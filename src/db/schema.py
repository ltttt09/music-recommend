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


def infer_language_group(language: str = "", title: str = "", artist: str = "", album: str = "", genre: str = "", lyrics: str = "") -> str:
    """Infer a coarse language group from track metadata.

    Uses a multi-layer strategy: genre keywords → lyrics character detection →
    title/artist character detection → Latin fallback → country storefront code.

    When lyrics are available, they are used as the primary source for character
    detection because they directly reflect the song's actual sung language.
    Title and artist names are less reliable (e.g. an English-titled song by a
    Chinese artist may still be sung in Chinese).

    IMPORTANT distinction: genre keywords must be LANGUAGE indicators (describing
    what language the song is sung in), NOT style descriptions. For example:
    - "华语" (Chinese-language music) = language indicator → ZH ✓
    - "民谣" (folk music) = style description → does NOT mean Chinese ✗
    - "K-Pop" (Korean pop) = language indicator → KR ✓
    iTunes genres are localized per storefront, so "民谣摇滚" is just the Chinese
    translation of "Folk Rock" and does not indicate the song is sung in Chinese.
    """
    code = (language or "").strip().upper()
    # Use title + artist for character detection, NOT album.
    # Album names are market-localized translations (e.g. "加州旅馆" for "Hotel California")
    # that don't reflect the song's actual language. Title + artist are more reliable.
    text = f"{title or ''} {artist or ''}"
    lyrics_text = (lyrics or "").strip()
    # When lyrics available, use lyrics as primary source for character detection
    # because lyrics directly reflect the sung language, not just the artist's origin.
    detect_text = lyrics_text if lyrics_text else text
    genre_text = (genre or "").strip().lower()
    has_cjk = _has_char_range(detect_text, 0x4E00, 0x9FFF)
    has_kana = _has_char_range(detect_text, 0x3040, 0x30FF)
    has_hangul = _has_char_range(detect_text, 0xAC00, 0xD7AF)
    has_cyrillic = _has_char_range(detect_text, 0x0400, 0x04FF)
    has_devanagari = _has_char_range(detect_text, 0x0900, 0x097F)
    has_thai = _has_char_range(detect_text, 0x0E00, 0x0E7F)
    has_arabic_script = _has_char_range(detect_text, 0x0600, 0x06FF)

    # Layer 1: genre keyword mapping (highest priority, overrides everything)
    # ONLY language-indicator keywords — NOT music style descriptions
    _genre_map = [
        # Korean (language-specific pop genres)
        (["k-pop", "korean pop", "k hip hop", "k-rap", "k drama ost"], "KR"),
        # Japanese (language-specific pop genres)
        (["j-pop", "j-pop", "j rock", "j-rock", "anime", "vocaloid", "city pop",
          "日本", "anime song", "japanese", "game music", "jpop", "jrock"], "JP"),
        # Chinese (ONLY language-specific: 华语=Chinese-language, not 民谣=folk style)
        (["华语", "華語", "国语", "國語", "粤语", "粵語", "mandopop", "cantopop",
          "chinese pop", "中文歌", "古风", "国语流行", "粤语流行", "中文嘻哈",
          "中文摇滚", "华语流行", "华语音乐", "華語流行", "國語流行", "粵語流行",
          "廣東歌", "广东歌", "香港流行樂", "香港流行乐", "華語流行樂", "华语流行乐",
          "華語音樂", "国语流行乐", "國語流行樂", "粵語流行樂", "粤语流行乐",
          "中文流行", "中文音樂", "中文音乐", "中文流行乐", "chinese music",
          "mandarin pop", "mandarin chinese", "c-pop", "c-pop"], "ZH"),
        # French
        (["chanson", "french pop", "french rap", "français"], "FR"),
        # Spanish (including Mexican music which is sung in Spanish, NOT Portuguese)
        (["flamenco", "spanish pop", "reggaeton", "latin pop", "ranchera",
          "música mexicana", "regional mexicano", "música popular mexicana",
          "corrido", "norteño", "banda", "latin urban", "latin trap"], "ES"),
        # Portuguese / Brazilian (ONLY truly Portuguese-language genres)
        (["bossa nova", "samba", "mpb", "funk carioca", "sertanejo",
          "forró", "música popular brasileira", "axé", "pagode"], "PT"),
        # German
        (["schlager", "german pop", "german rap", "deutsch"], "DE"),
        # Arabic
        (["arabic pop", "khaleeji", "oud"], "AR"),
        # Hindi / Indian
        (["bollywood", "hindi", "punjabi", "tamil songs", "carnatic",
          "filmi", "indian pop"], "IN"),
        # Thai
        (["thai pop", "luk thung", "molam", "string"], "TH"),
        # Russian
        (["russian pop", "russian rap", "shanson", "русская"], "RU"),
    ]
    for keywords, group in _genre_map:
        if any(kw in genre_text for kw in keywords):
            return group

    # Layer 2: Unicode character detection
    if has_hangul:
        return "KR"
    if has_kana:
        return "JP"
    if has_cjk:
        return "ZH"
    if has_cyrillic:
        return "RU"
    if has_devanagari:
        return "IN"
    if has_thai:
        return "TH"
    if has_arabic_script:
        return "AR"

    # Layer 3: Latin character fallback (before country code)
    # Songs with English titles from CN/TW/HK storefronts should be EN, not ZH.
    # The storefront country is not the song's language.
    # When lyrics are available, detect_text already points to lyrics;
    # otherwise it points to title+artist.
    has_latin = any("A" <= ch.upper() <= "Z" for ch in detect_text)
    if has_latin:
        return "EN"

    # Layer 4: country storefront code (only when no character evidence)
    # These are storefront codes, not song language. Only used as fallback
    # when the title has no discernible characters (e.g. numeric/punctuation only).
    if code in {"US", "GB", "CA", "AU", "NZ", "IE"}:
        return "EN"
    if code in {"CN", "TW", "HK", "SG"}:
        return "ZH"
    if code in {"KR", "KO"}:
        return "KR"
    if code in {"JP", "JA"}:
        return "JP"
    if code in {"FR"}:
        return "FR"
    if code in {"ES"}:
        return "ES"
    if code in {"RU"}:
        return "RU"
    if code in {"BR", "PT"}:
        return "PT"
    if code in {"DE"}:
        return "DE"
    if code in {"AR", "SA"}:
        return "AR"
    if code in {"IN"}:
        return "IN"
    if code in {"TH"}:
        return "TH"

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
    cover_url TEXT DEFAULT '',
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
    hit_rate_at_10 REAL DEFAULT 0,
    ndcg_at_10 REAL DEFAULT 0,
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

MODEL_METRICS_MIGRATIONS = {
    "hit_rate_at_10": "REAL DEFAULT 0",
    "ndcg_at_10": "REAL DEFAULT 0",
}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str):
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _fix_stale_fk_refs(conn: sqlite3.Connection):
    """Fix stale FK references in all tables (e.g. REFERENCES _tracks_old after rename)."""
    stale_refs = ["_tracks_old", "_artists_old", '"_tracks_old"', '"_artists_old"']
    replacements = [
        ('REFERENCES "_tracks_old"', 'REFERENCES tracks'),
        ('REFERENCES "_artists_old"', 'REFERENCES artists'),
        ('REFERENCES _tracks_old', 'REFERENCES tracks'),
        ('REFERENCES _artists_old', 'REFERENCES artists'),
    ]
    tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
    affected = []
    for t in tables:
        name, sql = t["name"], (t["sql"] or "")
        if any(stale in sql for stale in stale_refs):
            affected.append((name, sql))

    if not affected:
        return  # nothing to fix

    conn.execute("PRAGMA foreign_keys=OFF")
    for table_name, current_sql in affected:
        # Fix FK references by string replacement on the current schema SQL
        fixed_sql = current_sql
        for old_ref, new_ref in replacements:
            fixed_sql = fixed_sql.replace(old_ref, new_ref)
        if fixed_sql == current_sql:
            continue
        fixed_sql = fixed_sql.replace("IF NOT EXISTS ", "")
        cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
        col_list = ", ".join(cols)
        conn.execute(f"ALTER TABLE {table_name} RENAME TO _stale_{table_name}_tmp")
        conn.execute(fixed_sql)
        conn.execute(f"INSERT INTO {table_name} ({col_list}) SELECT {col_list} FROM _stale_{table_name}_tmp")
        conn.execute(f"DROP TABLE _stale_{table_name}_tmp")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()


def run_migrations(conn: sqlite3.Connection):
    """Apply lightweight schema migrations for existing SQLite databases."""
    # Fix any stale FK references first (from previous migrations that used ALTER TABLE RENAME)
    _fix_stale_fk_refs(conn)

    # Fix artists table missing PRIMARY KEY (causes FK mismatch on tracks)
    # Use CREATE new → DROP old → RENAME strategy to avoid stale FK refs
    pk_info = conn.execute("PRAGMA table_info(artists)").fetchall()
    has_pk = any(row["pk"] for row in pk_info)
    if not has_pk:
        conn.execute("PRAGMA foreign_keys=OFF")
        old_artists_cols = [row["name"] for row in pk_info]
        col_list = ", ".join(old_artists_cols)
        # Create new artists table with proper PK under temporary name
        conn.execute("""CREATE TABLE _artists_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            genres TEXT DEFAULT '',
            country TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute(f"INSERT INTO _artists_new ({col_list}) SELECT {col_list} FROM artists")
        conn.execute("DROP TABLE artists")
        conn.execute("ALTER TABLE _artists_new RENAME TO artists")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        # Re-fix stale FK refs that may have been introduced by the rename
        _fix_stale_fk_refs(conn)
    # Fix comments table missing PRIMARY KEY (causes FK mismatch on comment_likes)
    # Use CREATE new → DROP old → RENAME strategy
    comments_pk_info = conn.execute("PRAGMA table_info(comments)").fetchall()
    comments_has_pk = any(row["pk"] for row in comments_pk_info)
    if not comments_has_pk:
        conn.execute("PRAGMA foreign_keys=OFF")
        old_comments_cols = [row["name"] for row in comments_pk_info]
        comments_col_list = ", ".join(old_comments_cols)
        conn.execute("""CREATE TABLE _comments_new (
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
        )""")
        conn.execute(f"INSERT INTO _comments_new ({comments_col_list}) SELECT {comments_col_list} FROM comments")
        conn.execute("DROP TABLE comments")
        conn.execute("ALTER TABLE _comments_new RENAME TO comments")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        _fix_stale_fk_refs(conn)

    for column, definition in TRACK_MIGRATIONS.items():
        _ensure_column(conn, "tracks", column, definition)
    for column, definition in FEEDBACK_MIGRATIONS.items():
        _ensure_column(conn, "feedback", column, definition)
    for column, definition in COMMENT_MIGRATIONS.items():
        _ensure_column(conn, "comments", column, definition)
    for column, definition in MODEL_METRICS_MIGRATIONS.items():
        _ensure_column(conn, "model_metrics", column, definition)
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
    """Get a database connection with WAL mode, foreign keys enabled, and busy timeout."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")  # Wait up to 5s for lock release
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


def reindex_all_ids():
    """Reindex all primary key IDs to be sequential starting from 1.

    This reassigns IDs in artists, tracks, users, comments, playlists,
    user_playlists and all their foreign-key references so that every
    table's IDs are 1, 2, 3, … without gaps.
    """
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")

    def _rebuild_table(table, id_col, order_col=None):
        """Return a dict mapping old_id -> new_id for *table*."""
        order = order_col or id_col
        rows = conn.execute(f"SELECT {id_col} FROM {table} ORDER BY {order}").fetchall()
        mapping = {}
        for new_id, row in enumerate(rows, start=1):
            old_id = row[id_col]
            if old_id != new_id:
                mapping[old_id] = new_id
        if not mapping:
            return {}
        # Create temp table with new IDs
        all_cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        col_list = ", ".join(all_cols)
        tmp = f"_tmp_reindex_{table}"
        conn.execute(f"DROP TABLE IF EXISTS {tmp}")
        conn.execute(f"CREATE TABLE {tmp} ({col_list})")
        # Build CASE expression for ID substitution
        id_case = f"CASE {id_col} " + " ".join(f"WHEN {old} THEN {new}" for old, new in mapping.items()) + f" ELSE {id_col} END"
        # Substitute ID column in SELECT
        select_cols = []
        for col in all_cols:
            if col == id_col:
                select_cols.append(id_case)
            else:
                select_cols.append(col)
        select_expr = ", ".join(select_cols)
        conn.execute(f"INSERT INTO {tmp} SELECT {select_expr} FROM {table}")
        conn.execute(f"DROP TABLE {table}")
        conn.execute(f"ALTER TABLE {tmp} RENAME TO {table}")
        return mapping

    def _update_fk(table, fk_col, mapping):
        """Update foreign key column using old->new mapping."""
        if not mapping:
            return
        case = f"CASE {fk_col} " + " ".join(f"WHEN {old} THEN {new}" for old, new in mapping.items()) + f" ELSE {fk_col} END"
        conn.execute(f"UPDATE {table} SET {fk_col}={case}")

    # Step 1: Reindex artists (affects tracks.artist_id)
    artist_map = _rebuild_table("artists", "id", "name")
    _update_fk("tracks", "artist_id", artist_map)

    # Step 2: Reindex tracks (affects many FK references)
    track_map = _rebuild_table("tracks", "id", "id")
    for fk_table, fk_col in [
        ("listening_history", "track_id"),
        ("feedback", "track_id"),
        ("favorites", "track_id"),
        ("comments", "track_id"),
        ("playlist_tracks", "track_id"),
        ("user_playlist_tracks", "track_id"),
        ("recommendation_logs", "track_id"),
        ("lyrics_cache", "track_id"),
        ("track_profile_cache", "track_id"),
    ]:
        _update_fk(fk_table, fk_col, track_map)
    # Update entity_id in user_action_logs where entity_type='track'
    if track_map:
        case = "CASE entity_id " + " ".join(f"WHEN {old} THEN {new}" for old, new in track_map.items()) + " ELSE entity_id END"
        conn.execute(f"UPDATE user_action_logs SET entity_id={case} WHERE entity_type='track'")

    # Step 3: Reindex users (affects many FK references)
    user_map = _rebuild_table("users", "id", "id")
    for fk_table, fk_col in [
        ("listening_history", "user_id"),
        ("feedback", "user_id"),
        ("favorites", "user_id"),
        ("comments", "user_id"),
        ("comment_likes", "user_id"),
        ("playlists", "user_id"),
        ("user_playlists", "user_id"),
        ("recommendation_logs", "user_id"),
        ("user_action_logs", "user_id"),
        ("user_profile_cache", "user_id"),
    ]:
        _update_fk(fk_table, fk_col, user_map)

    # Step 4: Reindex comments (affects comment_likes.comment_id, comments.parent_id)
    comment_map = _rebuild_table("comments", "id", "created_at")
    _update_fk("comments", "parent_id", comment_map)
    _update_fk("comment_likes", "comment_id", comment_map)

    # Step 5: Reindex playlists
    playlist_map = _rebuild_table("playlists", "id", "id")
    _update_fk("playlist_tracks", "playlist_id", playlist_map)
    _update_fk("tracks", "seed_track_id", playlist_map) if "seed_track_id" in [r["name"] for r in conn.execute("PRAGMA table_info(playlists)").fetchall()] else None

    # Step 6: Reindex user_playlists
    user_playlist_map = _rebuild_table("user_playlists", "id", "id")
    _update_fk("user_playlist_tracks", "playlist_id", user_playlist_map)

    # Step 7: Reindex other auto-increment tables (listening_history, feedback, favorites, etc.)
    for table in ["listening_history", "feedback", "favorites", "playlist_tracks",
                   "user_playlist_tracks", "recommendation_logs", "user_action_logs",
                   "comment_likes", "model_metrics", "import_runs"]:
        try:
            _rebuild_table(table, "id", "id")
        except Exception:
            pass  # Some tables may not have 'id' column

    # Re-enable foreign keys and recreate indexes
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    conn.close()
    print("[DB] Reindexed all IDs to sequential 1,2,3,…")
