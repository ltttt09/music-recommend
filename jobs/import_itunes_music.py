"""导入 iTunes 音乐数据。

数据源策略：
- iTunes Search API：唯一数据源，主流歌曲、封面、30 秒试听。
"""

import argparse
import json
import random
import secrets
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db.schema import get_connection, init_db


ITUNES_COUNTRIES = [
    "US", "GB", "CA", "AU", "NZ", "IE",
    "CN", "TW", "HK", "SG",
    "JP", "KR", "TH", "MY", "ID", "PH", "VN", "IN",
    "FR", "DE", "ES", "IT", "NL", "BE", "SE", "NO", "DK", "FI", "PL",
    "BR", "MX", "AR", "CL", "CO",
    "TR", "ZA", "SA", "AE",
]

ITUNES_GLOBAL_TERMS = [
    "pop", "rock", "hip hop", "rap", "r&b", "soul", "jazz", "blues",
    "classical", "opera", "electronic", "dance", "house", "techno", "trance",
    "ambient", "lofi", "country", "folk", "indie", "alternative", "metal",
    "punk", "reggae", "latin", "salsa", "reggaeton", "flamenco", "bossa nova",
    "world music", "soundtrack", "movie soundtrack", "anime", "game music",
    "christmas", "acoustic", "piano", "guitar", "instrumental", "children music",
]

ITUNES_REGIONAL_TERMS = {
    "CN": ["华语", "中文歌", "流行", "摇滚", "民谣", "说唱", "电子", "古风", "周杰伦", "林俊杰", "邓紫棋", "王菲", "陈奕迅", "五月天", "薛之谦", "张学友", "刘德华", "孙燕姿"],
    "TW": ["华语", "台湾流行", "Mandopop", "周杰伦", "五月天", "蔡依林", "孙燕姿", "张惠妹", "伍佰", "告五人"],
    "HK": ["粤语", "Cantopop", "陈奕迅", "张学友", "Beyond", "容祖儿", "杨千嬅", "林忆莲", "刘德华"],
    "SG": ["Mandopop", "华语", "林俊杰", "孙燕姿", "梁文福"],
    "JP": ["j pop", "j rock", "anime song", "city pop", "vocaloid", "宇多田ヒカル", "米津玄師", "YOASOBI", "Aimer", "King Gnu", "ONE OK ROCK"],
    "KR": ["k pop", "k hip hop", "k drama ost", "BTS", "BLACKPINK", "IU", "NewJeans", "EXO", "TWICE", "SEVENTEEN"],
    "IN": ["bollywood", "hindi songs", "tamil songs", "punjabi pop", "ar rahman", "arijit singh"],
    "FR": ["chanson", "french pop", "french rap", "stromae", "edith piaf"],
    "DE": ["german pop", "german rap", "schlager", "rammstein"],
    "ES": ["spanish pop", "flamenco", "reggaeton", "latin pop"],
    "IT": ["italian pop", "opera", "sanremo"],
    "BR": ["bossa nova", "samba", "mpb", "funk carioca"],
    "MX": ["mariachi", "regional mexicano", "latin pop"],
    "SA": ["arabic pop", "oud", "khaleeji"],
    "TR": ["turkish pop", "anatolian rock"],
    "ZA": ["afrobeats", "amapiano", "south african house"],
}


def build_itunes_queries():
    seen = set()
    for country in ITUNES_COUNTRIES:
        for term in ITUNES_GLOBAL_TERMS:
            key = (term.lower(), country)
            if key not in seen:
                seen.add(key)
                yield term, country
        for term in ITUNES_REGIONAL_TERMS.get(country, []):
            key = (term.lower(), country)
            if key not in seen:
                seen.add(key)
                yield term, country

def fetch_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_year(value):
    if not value:
        return 0
    try:
        return int(str(value)[:4])
    except ValueError:
        return 0


def upsert_artist(conn, name, genre="", country=""):
    row = conn.execute("SELECT id FROM artists WHERE name=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO artists (name, genres, country) VALUES (?, ?, ?)",
        (name or "未知艺人", genre or "", country or ""),
    )
    return cur.lastrowid


def track_exists(conn, source, external_id, title, artist_id):
    if source and external_id:
        row = conn.execute(
            "SELECT id FROM tracks WHERE source=? AND external_id=?",
            (source, str(external_id)),
        ).fetchone()
        if row:
            return row["id"]
    row = conn.execute(
        "SELECT id FROM tracks WHERE title=? AND artist_id=?",
        (title, artist_id),
    ).fetchone()
    return row["id"] if row else None


def insert_track(conn, item):
    artist_id = upsert_artist(conn, item["artist"], item.get("genre", ""), item.get("language", ""))
    existing_id = track_exists(conn, item["source"], item["external_id"], item["title"], artist_id)
    params = {
        "title": item["title"],
        "artist_id": artist_id,
        "album": item.get("album", ""),
        "year": item.get("year", 0),
        "duration_ms": item.get("duration_ms", 0),
        "genre": item.get("genre", ""),
        "popularity": item.get("popularity", 50),
        "energy": item.get("energy", 0.5),
        "danceability": item.get("danceability", 0.5),
        "valence": item.get("valence", 0.5),
        "tempo": item.get("tempo", 100),
        "image_url": item.get("image_url", ""),
        "preview_url": item.get("preview_url", ""),
        "source": item.get("source", ""),
        "external_id": str(item.get("external_id", "")),
        "source_url": item.get("source_url", ""),
        "license": item.get("license", ""),
        "audio_type": item.get("audio_type", "preview"),
        "language": item.get("language", ""),
    }
    if existing_id:
        conn.execute(
            """UPDATE tracks SET album=:album, year=:year, duration_ms=:duration_ms, genre=:genre,
               popularity=:popularity, image_url=:image_url, preview_url=:preview_url,
               source_url=:source_url, license=:license, audio_type=:audio_type, language=:language
               WHERE id=:id""",
            {**params, "id": existing_id},
        )
        return False
    conn.execute(
        """INSERT INTO tracks
           (title, artist_id, album, year, duration_ms, genre, popularity,
            energy, danceability, valence, tempo, image_url, preview_url,
            source, external_id, source_url, license, audio_type, language)
           VALUES
           (:title, :artist_id, :album, :year, :duration_ms, :genre, :popularity,
            :energy, :danceability, :valence, :tempo, :image_url, :preview_url,
            :source, :external_id, :source_url, :license, :audio_type, :language)""",
        params,
    )
    return True


def import_itunes(conn, limit_per_query, target_count):
    imported = 0
    rng = random.Random(42)
    query_count = 0
    for term, country in build_itunes_queries():
        query_count += 1
        if imported >= target_count:
            break
        query = urllib.parse.urlencode({
            "term": term,
            "country": country,
            "media": "music",
            "entity": "song",
            "limit": min(limit_per_query, 200),
        })
        url = f"https://itunes.apple.com/search?{query}"
        data = fetch_json(url)
        for row in data.get("results", []):
            if not row.get("trackName") or not row.get("artistName") or not row.get("previewUrl"):
                continue
            image = row.get("artworkUrl100", "")
            if image:
                image = image.replace("100x100bb", "600x600bb").replace("100x100-75", "600x600-75")
            item = {
                "source": "itunes",
                "external_id": row.get("trackId"),
                "title": row.get("trackName", ""),
                "artist": row.get("artistName", ""),
                "album": row.get("collectionName", ""),
                "year": normalize_year(row.get("releaseDate")),
                "duration_ms": row.get("trackTimeMillis", 0),
                "genre": row.get("primaryGenreName", ""),
                "popularity": rng.uniform(45, 95),
                "image_url": image,
                "preview_url": row.get("previewUrl", ""),
                "source_url": row.get("trackViewUrl", ""),
                "license": "iTunes 30 秒试听",
                "audio_type": "preview",
                "language": country,
            }
            if insert_track(conn, item):
                imported += 1
            if imported >= target_count:
                break
        conn.commit()
        time.sleep(0.15)
    return imported, query_count


def reset_music_data(conn):
    for table in [
        "recommendation_logs", "playlist_tracks", "playlists", "user_playlist_tracks",
        "user_playlists", "favorites", "comments", "feedback", "listening_history",
        "tracks", "artists",
    ]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def synthesize_user_behavior(conn, users=120, seed=42):
    rng = random.Random(seed)
    existing_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_users == 0:
        genres = [row["genre"] for row in conn.execute("SELECT DISTINCT genre FROM tracks WHERE genre != ''").fetchall()]
        for i in range(1, users + 1):
            pref = rng.choice(genres) if genres else ""
            salt = secrets.token_hex(16)
            conn.execute(
                """INSERT INTO users (username, display_name, preferred_genres, password_hash, salt)
                   VALUES (?, ?, ?, '', ?)""",
                (f"user_{i:03d}", f"用户 {i}", pref, salt),
            )
        conn.commit()

    track_rows = conn.execute("SELECT id, genre, popularity FROM tracks").fetchall()
    if not track_rows:
        return 0
    users_rows = conn.execute("SELECT id, preferred_genres FROM users").fetchall()
    records = []
    feedback = []
    favorites = []
    for user in users_rows:
        pref = user["preferred_genres"] or ""
        weighted = []
        for track in track_rows:
            weight = 1.0 + float(track["popularity"] or 0) / 100
            if pref and track["genre"] == pref:
                weight *= 4.0
            weighted.append((track["id"], weight))
        ids = [x[0] for x in weighted]
        weights = [x[1] for x in weighted]
        listen_count = rng.randint(35, 90)
        picks = rng.choices(ids, weights=weights, k=min(listen_count, len(ids)))
        for track_id in picks:
            records.append((user["id"], track_id))
            roll = rng.random()
            if roll < 0.12:
                feedback.append((user["id"], track_id, 1, "synthetic"))
            elif roll < 0.16:
                feedback.append((user["id"], track_id, -1, "synthetic"))
            if roll < 0.06:
                favorites.append((user["id"], track_id))
    conn.executemany("INSERT INTO listening_history (user_id, track_id) VALUES (?, ?)", records)
    conn.executemany(
        "INSERT OR IGNORE INTO feedback (user_id, track_id, rating, model_name) VALUES (?, ?, ?, ?)",
        feedback,
    )
    conn.executemany("INSERT OR IGNORE INTO favorites (user_id, track_id) VALUES (?, ?)", favorites)
    conn.commit()
    return len(records)


def log_import_run(conn, source, status, count, message):
    conn.execute(
        "INSERT INTO import_runs (source, status, imported_tracks, message) VALUES (?, ?, ?, ?)",
        (source, status, count, message),
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空歌曲和行为数据后重新导入")
    parser.add_argument("--itunes-limit-per-query", type=int, default=200)
    parser.add_argument("--itunes-target", type=int, default=10000)
    parser.add_argument("--synthetic-users", type=int, default=120)
    args = parser.parse_args()

    init_db()
    conn = get_connection()
    if args.reset:
        reset_music_data(conn)

    itunes_count, itunes_queries = import_itunes(conn, args.itunes_limit_per_query, args.itunes_target)
    log_import_run(conn, "itunes", "ok", itunes_count, f"导入 iTunes 30 秒试听数据，查询 {itunes_queries} 组关键词")

    behavior_count = synthesize_user_behavior(conn, args.synthetic_users)
    log_import_run(conn, "synthetic_behavior", "ok", behavior_count, "生成本地用户行为数据")

    total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    playable = conn.execute("SELECT COUNT(*) FROM tracks WHERE preview_url != ''").fetchone()[0]
    full_audio = conn.execute("SELECT COUNT(*) FROM tracks WHERE audio_type='full' AND preview_url != ''").fetchone()[0]
    conn.close()
    print(json.dumps({
        "tracks": total,
        "playable_tracks": playable,
        "full_audio_tracks": full_audio,
        "itunes_imported": itunes_count,
        "behavior_records": behavior_count,
        "itunes_queries": itunes_queries,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
