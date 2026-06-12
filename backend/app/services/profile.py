"""用户画像和推荐过滤相关逻辑。"""

import json
from collections import Counter

from src.db.repository import FeedbackRepo, ListeningRepo, TrackRepo, UserRepo
from src.db.schema import get_connection


def _split_genres(value):
    if not value:
        return []
    return [g.strip() for g in value.replace("，", ",").split(",") if g.strip()]


def build_user_profile(user_id, persist=True):
    listened = ListeningRepo.get_listened_track_ids(user_id)
    liked = FeedbackRepo.get_liked_tracks(user_id)
    disliked = FeedbackRepo.get_disliked_tracks(user_id)

    conn = get_connection()
    favorites = {
        row["track_id"]
        for row in conn.execute("SELECT track_id FROM favorites WHERE user_id=?", (user_id,)).fetchall()
    }
    commented = {
        row["track_id"]
        for row in conn.execute("SELECT DISTINCT track_id FROM comments WHERE user_id=?", (user_id,)).fetchall()
    }
    user_row = conn.execute("SELECT preferred_genres FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()

    preferred_genres = _split_genres(user_row["preferred_genres"] if user_row else "")
    genres = Counter()
    artists = Counter()
    disliked_genres = Counter()

    weighted_tracks = (
        [(tid, 4) for tid in favorites]
        + [(tid, 3) for tid in liked]
        + [(tid, 2) for tid in commented]
        + [(tid, 1) for tid in list(listened)[-80:]]
    )
    for track_id, weight in weighted_tracks:
        track = TrackRepo.get_by_id(track_id)
        if not track:
            continue
        if track.get("genre"):
            genres[track["genre"]] += weight
        if track.get("artist_id"):
            artists[track["artist_id"]] += weight

    for track_id in disliked:
        track = TrackRepo.get_by_id(track_id)
        if track and track.get("genre"):
            disliked_genres[track["genre"]] += 1

    for genre in preferred_genres:
        genres[genre] += 3

    profile = {
        "listened": listened,
        "liked": liked,
        "disliked": disliked,
        "favorites": favorites,
        "commented": commented,
        "genres": genres,
        "artists": artists,
        "disliked_genres": disliked_genres,
        "preferred_genres": preferred_genres,
    }
    if persist:
        save_user_profile_cache(user_id, profile)
    return profile


def excluded_track_ids(user_id):
    profile = build_user_profile(user_id)
    excluded = set()
    excluded.update(profile["listened"])
    excluded.update(profile["favorites"])
    excluded.update(profile["liked"])
    excluded.update(profile["disliked"])
    return excluded, profile


def save_user_profile_cache(user_id, profile):
    top_genres = json.dumps(profile["genres"].most_common(10), ensure_ascii=False)
    top_artists = json.dumps(profile["artists"].most_common(10), ensure_ascii=False)
    disliked_genres = json.dumps(profile["disliked_genres"].most_common(10), ensure_ascii=False)
    conn = get_connection()
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
    conn.close()


def get_cached_user_profile(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profile_cache WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        build_user_profile(user_id, persist=True)
        conn = get_connection()
        row = conn.execute("SELECT * FROM user_profile_cache WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
    return dict(row) if row else None


def user_profile_detail(user_id):
    profile = build_user_profile(user_id, persist=True)
    user = UserRepo.get_by_id(user_id)
    top_artists = []
    for artist_id, score in profile["artists"].most_common(10):
        conn = get_connection()
        row = conn.execute("SELECT id, name FROM artists WHERE id=?", (artist_id,)).fetchone()
        conn.close()
        if row:
            top_artists.append({"id": row["id"], "name": row["name"], "score": score})
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
