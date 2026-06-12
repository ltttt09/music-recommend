"""Repository layer: all database queries for the music recommender."""

import sqlite3
from typing import Optional
from datetime import datetime, timedelta

from src.db.schema import get_connection


class TrackRepo:
    """Track-related database operations."""

    @staticmethod
    def insert_many(tracks: list[dict]):
        conn = get_connection()
        conn.executemany(
            """INSERT OR IGNORE INTO tracks (id, title, artist_id, album, year, duration_ms, genre, popularity, energy, danceability, valence, tempo)
               VALUES (:id, :title, :artist_id, :album, :year, :duration_ms, :genre, :popularity, :energy, :danceability, :valence, :tempo)""",
            tracks,
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(track_id: int) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute(
            """SELECT t.*, a.name AS artist_name, a.genres AS artist_genres
               FROM tracks t JOIN artists a ON t.artist_id = a.id
               WHERE t.id = ?""", (track_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def search(query: str, page: int = 1, size: int = 20, genre: str = "", year_from: int = 0, year_to: int = 0, language: str = "", sort_by: str = "popularity", sort_order: str = "desc"):
        conn = get_connection()
        params = []
        where = ["t.preview_url != ''"]
        if query:
            where.append("(t.title LIKE ? OR a.name LIKE ? OR t.album LIKE ?)")
            like = f"%{query}%"
            params.extend([like, like, like])
        if genre:
            where.append("t.genre LIKE ?")
            params.append(f"%{genre}%")
        if year_from > 0:
            where.append("t.year >= ?")
            params.append(year_from)
        if year_to > 0:
            where.append("t.year <= ?")
            params.append(year_to)
        if language:
            # language is genre prefix like "CN", "JP", etc.
            where.append("(t.genre LIKE ? OR t.genre LIKE ?)")
            params.append(f"{language}-%")
            params.append(f"{language}%")

        count_sql = f"SELECT COUNT(*) FROM tracks t JOIN artists a ON t.artist_id = a.id WHERE {' AND '.join(where)}"
        total = conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * size
        sort_map = {
            "popularity": "t.popularity",
            "year": "t.year",
            "title": "t.title",
            "artist": "a.name",
            "created": "t.created_at",
            "duration": "t.duration_ms",
        }
        order_col = sort_map.get(sort_by, "t.popularity")
        order_dir = "ASC" if str(sort_order).lower() == "asc" else "DESC"
        data_sql = f"""SELECT t.*, a.name AS artist_name FROM tracks t
                        JOIN artists a ON t.artist_id = a.id
                        WHERE {' AND '.join(where)}
                        ORDER BY {order_col} {order_dir}, t.id DESC LIMIT ? OFFSET ?"""
        rows = conn.execute(data_sql, params + [size, offset]).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "size": size}

    @staticmethod
    def get_genres() -> list[str]:
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT genre FROM tracks WHERE genre != '' AND preview_url != ''").fetchall()
        conn.close()
        return sorted(r["genre"] for r in rows)

    @staticmethod
    def get_trending(limit: int = 20):
        conn = get_connection()
        rows = conn.execute(
            """SELECT t.*, a.name AS artist_name, COUNT(lh.id) AS play_count
               FROM tracks t
               JOIN artists a ON t.artist_id = a.id
               LEFT JOIN listening_history lh ON t.id = lh.track_id
               WHERE t.preview_url != ''
               GROUP BY t.id ORDER BY play_count DESC, t.popularity DESC
               LIMIT ?""", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


class ArtistRepo:
    """Artist-related database operations."""

    @staticmethod
    def insert_many(artists: list[dict]):
        conn = get_connection()
        conn.executemany(
            "INSERT OR IGNORE INTO artists (id, name, genres, country) VALUES (:id, :name, :genres, :country)",
            artists,
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(artist_id: int) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM artists WHERE id = ?", (artist_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_tracks(artist_id: int, limit: int = 50):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM tracks WHERE artist_id = ? ORDER BY popularity DESC LIMIT ?",
            (artist_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


class UserRepo:
    """User-related database operations."""

    @staticmethod
    def insert_many(users: list[dict]):
        conn = get_connection()
        conn.executemany(
            "INSERT OR IGNORE INTO users (id, username, display_name, preferred_genres) VALUES (:id, :username, :display_name, :preferred_genres)",
            users,
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("SELECT id, username, display_name, preferred_genres, join_date FROM users ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute(
            "SELECT id, username, display_name, avatar_url, preferred_genres, join_date FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_history(user_id: int, limit: int = 50):
        conn = get_connection()
        rows = conn.execute(
            """SELECT lh.*, t.title AS track_title, t.genre, t.image_url, t.preview_url,
                      a.name AS artist_name
               FROM listening_history lh
               JOIN tracks t ON lh.track_id = t.id
               JOIN artists a ON t.artist_id = a.id
               WHERE lh.user_id = ?
               ORDER BY lh.listened_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_listened_track_ids(user_id: int) -> set[int]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT DISTINCT track_id FROM listening_history WHERE user_id = ?", (user_id,)
        ).fetchall()
        conn.close()
        return {r["track_id"] for r in rows}


class ListeningRepo:
    """Listening history operations."""

    @staticmethod
    def insert_many(records: list[dict]):
        conn = get_connection()
        conn.executemany(
            "INSERT INTO listening_history (user_id, track_id, listened_at, source) VALUES (:user_id, :track_id, :listened_at, :source)",
            records,
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_stats(user_id: int):
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM listening_history WHERE user_id = ?", (user_id,)).fetchone()[0]
        top_genre_row = conn.execute(
            """SELECT t.genre, COUNT(*) AS cnt FROM listening_history lh
               JOIN tracks t ON lh.track_id = t.id
               WHERE lh.user_id = ? AND t.genre != ''
               GROUP BY t.genre ORDER BY cnt DESC LIMIT 1""", (user_id,)
        ).fetchone()
        top_artist_row = conn.execute(
            """SELECT a.name, COUNT(*) AS cnt FROM listening_history lh
               JOIN tracks t ON lh.track_id = t.id
               JOIN artists a ON t.artist_id = a.id
               WHERE lh.user_id = ? GROUP BY a.id ORDER BY cnt DESC LIMIT 1""", (user_id,)
        ).fetchone()
        conn.close()
        return {
            "total_listens": total,
            "top_genre": top_genre_row["genre"] if top_genre_row else "",
            "top_artist": top_artist_row["name"] if top_artist_row else "",
        }



    @staticmethod
    def get_listened_track_ids(user_id: int) -> set[int]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT DISTINCT track_id FROM listening_history WHERE user_id = ?", (user_id,)
        ).fetchall()
        conn.close()
        return {r["track_id"] for r in rows}
class FeedbackRepo:
    """User feedback (like/dislike) operations."""

    @staticmethod
    def upsert(user_id: int, track_id: int, rating: int, model_name: str = ""):
        conn = get_connection()
        existing = conn.execute(
            "SELECT id, skip_count FROM feedback WHERE user_id=? AND track_id=? AND model_name=?",
            (user_id, track_id, model_name),
        ).fetchone()
        max_skip_row = conn.execute(
            "SELECT MAX(skip_count) AS max_skip FROM feedback WHERE user_id=? AND track_id=?",
            (user_id, track_id),
        ).fetchone()
        skip_count = 0
        muted_until = None
        if rating < 0:
            base_skip_count = max(existing["skip_count"] if existing else 0, max_skip_row["max_skip"] or 0)
            skip_count = base_skip_count + 1
            hours = min(24 * (2 ** (skip_count - 1)), 24 * 30)
            muted_until = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        if existing:
            conn.execute(
                """UPDATE feedback
                   SET rating=?, skip_count=?, muted_until=?, created_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (rating, skip_count if rating < 0 else existing["skip_count"], muted_until, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO feedback (user_id, track_id, rating, model_name, skip_count, muted_until)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, track_id, rating, model_name, skip_count, muted_until),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def get_liked_tracks(user_id: int) -> set[int]:
        conn = get_connection()
        rows = conn.execute("SELECT track_id FROM feedback WHERE user_id = ? AND rating > 0", (user_id,)).fetchall()
        conn.close()
        return {r["track_id"] for r in rows}

    @staticmethod
    def get_disliked_tracks(user_id: int) -> set[int]:
        conn = get_connection()
        rows = conn.execute(
            """SELECT track_id FROM feedback
               WHERE user_id = ? AND rating < 0
                 AND muted_until IS NOT NULL
                 AND muted_until > CURRENT_TIMESTAMP""",
            (user_id,),
        ).fetchall()
        conn.close()
        return {r["track_id"] for r in rows}

    @staticmethod
    def get_state(user_id: int, track_id: int) -> dict:
        conn = get_connection()
        liked = conn.execute(
            "SELECT id FROM feedback WHERE user_id=? AND track_id=? AND rating>0 LIMIT 1",
            (user_id, track_id),
        ).fetchone()
        skipped = conn.execute(
            """SELECT skip_count, muted_until FROM feedback
               WHERE user_id=? AND track_id=? AND rating<0
                 AND muted_until IS NOT NULL
                 AND muted_until > CURRENT_TIMESTAMP
               ORDER BY skip_count DESC, created_at DESC LIMIT 1""",
            (user_id, track_id),
        ).fetchone()
        conn.close()
        return {
            "liked": liked is not None,
            "skipped": skipped is not None,
            "skip_count": skipped["skip_count"] if skipped else 0,
            "muted_until": skipped["muted_until"] if skipped else None,
        }


class PlaylistRepo:
    """Playlist operations."""

    @staticmethod
    def create(user_id: Optional[int], name: str, description: str = "", is_system: bool = False, seed_track_id: Optional[int] = None) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO playlists (user_id, name, description, is_system, seed_track_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, description, int(is_system), seed_track_id),
        )
        conn.commit()
        playlist_id = cur.lastrowid
        conn.close()
        return playlist_id

    @staticmethod
    def add_tracks(playlist_id: int, track_ids: list[int]):
        conn = get_connection()
        # Validate track_ids exist
        if track_ids:
            placeholders = ",".join("?" * len(track_ids))
            valid = set(r[0] for r in conn.execute(f"SELECT id FROM tracks WHERE id IN ({placeholders})", track_ids).fetchall())
            for i, tid in enumerate(track_ids):
                if tid in valid:
                    conn.execute("INSERT OR IGNORE INTO playlist_tracks (playlist_id, track_id, position) VALUES (?, ?, ?)", (playlist_id, tid, i))
        conn.commit()
        conn.close()

    @staticmethod
    def get_tracks(playlist_id: int):
        conn = get_connection()
        rows = conn.execute(
            """SELECT pt.*, t.title, t.album, t.genre, t.image_url, t.preview_url, a.name AS artist_name
               FROM playlist_tracks pt
               JOIN tracks t ON pt.track_id = t.id
               JOIN artists a ON t.artist_id = a.id
               WHERE pt.playlist_id = ?
               ORDER BY pt.position""", (playlist_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(playlist_id: int) -> Optional[dict]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_playlists(user_id: int):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM playlists WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
