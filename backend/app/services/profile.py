"""用户画像和推荐过滤相关逻辑。"""

import json
import math
from datetime import datetime, timedelta
from collections import Counter

from src.db.repository import FeedbackRepo, ListeningRepo, TrackRepo, UserRepo
from src.db.schema import get_connection


def _row_get(row, key, default=None):
    """Safe accessor for sqlite3.Row objects (no .get() method)."""
    try:
        val = row[key]
        return val if val is not None else default
    except (KeyError, IndexError):
        return default


def _split_genres(value):
    if not value:
        return []
    return [g.strip() for g in value.replace("，", ",").split(",") if g.strip()]


def _action_track_weight(action_type):
    action_type = (action_type or "").lower()
    if any(key in action_type for key in ("dislike", "skip", "blacklist")):
        return 0
    if any(key in action_type for key in ("favorite", "playlist")):
        return 4
    if "like" in action_type or "feedback" in action_type:
        return 3
    if "search" in action_type:
        return 2
    if any(key in action_type for key in ("play", "click", "detail", "view")):
        return 1
    return 0


def _time_decay(days_since, half_life=7):
    """指数时间衰减：半衰期7天，7天前的权重减半，14天前的降到1/4。"""
    if days_since <= 0:
        return 1.0
    return math.exp(-0.1 * days_since)


def build_user_profile(user_id, persist=True):
    conn = get_connection()
    try:
        # ── Fetch all data sources with timestamps for time decay ──
        listened_rows = conn.execute(
            """SELECT track_id, listened_at
               FROM listening_history WHERE user_id=?
               ORDER BY listened_at DESC""",
            (user_id,),
        ).fetchall()

        liked_rows = conn.execute(
            """SELECT f.track_id, f.created_at
               FROM feedback f WHERE f.user_id=? AND f.rating > 0""",
            (user_id,),
        ).fetchall()

        disliked = FeedbackRepo.get_disliked_tracks(user_id)

        favorites_rows = conn.execute(
            """SELECT track_id, created_at FROM favorites WHERE user_id=?""",
            (user_id,),
        ).fetchall()

        commented_rows = conn.execute(
            """SELECT DISTINCT track_id, created_at FROM comments WHERE user_id=?""",
            (user_id,),
        ).fetchall()

        action_rows = conn.execute(
            """SELECT action_type, entity_id, created_at
               FROM user_action_logs
               WHERE user_id=? AND entity_type='track' AND entity_id IS NOT NULL
               ORDER BY created_at DESC LIMIT 200""",
            (user_id,),
        ).fetchall()

        user_row = conn.execute("SELECT preferred_genres FROM users WHERE id=?", (user_id,)).fetchone()
    finally:
        conn.close()

    preferred_genres = _split_genres(user_row["preferred_genres"] if user_row else "")

    # ── Build track IDs sets (for exclusion and dedup) ──
    listened_ids = [r["track_id"] for r in listened_rows]
    liked_ids = set(r["track_id"] for r in liked_rows)
    favorites_ids = set(r["track_id"] for r in favorites_rows)
    commented_ids = set(r["track_id"] for r in commented_rows)

    # ── Build weighted tracks with time decay ──
    now = datetime.utcnow()
    genres = Counter()
    artists = Counter()
    disliked_genres = Counter()

    # Favorites: weight=4 with time decay
    for row in favorites_rows:
        days = 0
        if _row_get(row, "created_at"):
            try:
                ts = datetime.strptime(str(row["created_at"])[:19], "%Y-%m-%d %H:%M:%S")
                days = max(0, (now - ts).days)
            except (ValueError, TypeError):
                days = 0
        effective = 4 * _time_decay(days)
        if effective > 0.01:
            track = TrackRepo.get_by_id(row["track_id"])
            if track:
                if track.get("genre"):
                    genres[track["genre"]] += effective
                if track.get("artist_id"):
                    artists[track["artist_id"]] += effective

    # Liked: weight=3 with time decay
    for row in liked_rows:
        days = 0
        if _row_get(row, "created_at"):
            try:
                ts = datetime.strptime(str(row["created_at"])[:19], "%Y-%m-%d %H:%M:%S")
                days = max(0, (now - ts).days)
            except (ValueError, TypeError):
                days = 0
        effective = 3 * _time_decay(days)
        if effective > 0.01:
            track = TrackRepo.get_by_id(row["track_id"])
            if track:
                if track.get("genre"):
                    genres[track["genre"]] += effective
                if track.get("artist_id"):
                    artists[track["artist_id"]] += effective

    # Commented: weight=2 with time decay
    for row in commented_rows:
        days = 0
        if _row_get(row, "created_at"):
            try:
                ts = datetime.strptime(str(row["created_at"])[:19], "%Y-%m-%d %H:%M:%S")
                days = max(0, (now - ts).days)
            except (ValueError, TypeError):
                days = 0
        effective = 2 * _time_decay(days)
        if effective > 0.01:
            track = TrackRepo.get_by_id(row["track_id"])
            if track:
                if track.get("genre"):
                    genres[track["genre"]] += effective
                if track.get("artist_id"):
                    artists[track["artist_id"]] += effective

    # Listening history: weight=1 with time decay (full history, no hard cutoff)
    for row in listened_rows:
        days = 0
        if _row_get(row, "listened_at"):
            try:
                ts = datetime.strptime(str(row["listened_at"])[:19], "%Y-%m-%d %H:%M:%S")
                days = max(0, (now - ts).days)
            except (ValueError, TypeError):
                days = 0
        effective = 1 * _time_decay(days)
        if effective > 0.01:
            track = TrackRepo.get_by_id(row["track_id"])
            if track:
                if track.get("genre"):
                    genres[track["genre"]] += effective
                if track.get("artist_id"):
                    artists[track["artist_id"]] += effective

    # ── Action logs: deduplicated against direct data sources (H1 fix) ──
    already_counted = set(favorites_ids) | set(liked_ids) | set(commented_ids) | set(listened_ids)
    for row in action_rows:
        base_weight = _action_track_weight(row["action_type"])
        if base_weight <= 0:
            continue
        tid = row["entity_id"]
        # Dedup: skip if already counted from direct DB query
        if tid in already_counted:
            continue
        days = 0
        if _row_get(row, "created_at"):
            try:
                ts = datetime.strptime(str(row["created_at"])[:19], "%Y-%m-%d %H:%M:%S")
                days = max(0, (now - ts).days)
            except (ValueError, TypeError):
                days = 0
        effective = base_weight * _time_decay(days)
        if effective > 0.01:
            track = TrackRepo.get_by_id(tid)
            if track:
                if track.get("genre"):
                    genres[track["genre"]] += effective
                if track.get("artist_id"):
                    artists[track["artist_id"]] += effective

    # ── Disliked genres ──
    for track_id in disliked:
        track = TrackRepo.get_by_id(track_id)
        if track and track.get("genre"):
            disliked_genres[track["genre"]] += 1

    # ── Preferred genres: conditional boost (only if user actually listens to this genre) ──
    user_genres_set = set(genres.keys())
    for genre in preferred_genres:
        if genre in user_genres_set:
            genres[genre] += 3  # Boost declared preference that matches behavior
        # No boost for genres user declared but never listens to

    profile = {
        "listened": listened_ids,
        "liked": liked_ids,
        "disliked": disliked,
        "favorites": favorites_ids,
        "commented": commented_ids,
        "genres": genres,
        "artists": artists,
        "disliked_genres": disliked_genres,
        "preferred_genres": preferred_genres,
    }
    if persist:
        save_user_profile_cache(user_id, profile)
    return profile


def excluded_track_ids(user_id):
    """排除策略：只排除踩过的歌+近7天内听过的歌。超过7天的可以再推荐。"""
    profile = build_user_profile(user_id)
    excluded = set()

    # Always exclude disliked tracks
    excluded.update(profile["disliked"])

    # Exclude tracks listened within the last 7 days
    conn = get_connection()
    try:
        recent_rows = conn.execute(
            """SELECT track_id FROM listening_history
               WHERE user_id=? AND listened_at >= ?
               ORDER BY listened_at DESC""",
            (user_id, (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        ).fetchall()
        for row in recent_rows:
            excluded.add(row["track_id"])
    finally:
        conn.close()

    return excluded, profile


def save_user_profile_cache(user_id, profile):
    top_genres = json.dumps(profile["genres"].most_common(10), ensure_ascii=False)
    top_artists = json.dumps(profile["artists"].most_common(10), ensure_ascii=False)
    disliked_genres = json.dumps(profile["disliked_genres"].most_common(10), ensure_ascii=False)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO user_profile_cache (user_id, top_genres, top_artists, disliked_genres, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id) DO UPDATE SET
                 top_genres=excluded.top_genres,
                 top_artists=excluded.top_artists,
                 disliked_genres=excluded.disliked_genres,
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id, top_genres, top_artists, disliked_genres),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_user_profile(user_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM user_profile_cache WHERE user_id=?", (user_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        build_user_profile(user_id, persist=True)
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM user_profile_cache WHERE user_id=?", (user_id,)).fetchone()
        finally:
            conn.close()
    return dict(row) if row else None


def user_profile_detail(user_id):
    profile = build_user_profile(user_id, persist=True)
    user = UserRepo.get_by_id(user_id)
    top_artists = []
    if profile["artists"]:
        conn = get_connection()
        try:
            ids = [aid for aid, _ in profile["artists"].most_common(10)]
            placeholders = ",".join("?" * len(ids))
            rows = conn.execute(f"SELECT id, name FROM artists WHERE id IN ({placeholders})", ids).fetchall()
            artist_map = {r["id"]: r["name"] for r in rows}
        finally:
            conn.close()
        for artist_id, score in profile["artists"].most_common(10):
            if artist_id in artist_map:
                top_artists.append({"id": artist_id, "name": artist_map[artist_id], "score": score})
    return {
        "user": user,
        "top_genres": [{"name": name, "score": score} for name, score in profile["genres"].most_common(10)],
        "top_artists": top_artists,
        "disliked_genres": [
            {"name": name, "score": score} for name, score in profile["disliked_genres"].most_common(10)
        ],
        "counts": {
            "listened": len(profile["listened"]),
            "liked": len(profile["liked"]),
            "disliked": len(profile["disliked"]),
            "favorites": len(profile["favorites"]),
        },
    }
