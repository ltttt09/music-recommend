"""清理没有试听地址的歌曲及其关联数据。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db.schema import get_connection, init_db


def main():
    init_db()
    conn = get_connection()
    bad_ids_sql = "SELECT id FROM tracks WHERE preview_url IS NULL OR TRIM(preview_url) = ''"
    before = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    bad_count = conn.execute(f"SELECT COUNT(*) FROM ({bad_ids_sql})").fetchone()[0]

    if bad_count:
        conn.execute(f"DELETE FROM recommendation_logs WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM track_profile_cache WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM playlist_tracks WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM user_playlist_tracks WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM favorites WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM comments WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM feedback WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM listening_history WHERE track_id IN ({bad_ids_sql})")
        conn.execute(f"UPDATE playlists SET seed_track_id=NULL WHERE seed_track_id IN ({bad_ids_sql})")
        conn.execute(f"DELETE FROM tracks WHERE id IN ({bad_ids_sql})")
        conn.execute("DELETE FROM artists WHERE id NOT IN (SELECT DISTINCT artist_id FROM tracks)")
        conn.commit()

    after = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    playable = conn.execute("SELECT COUNT(*) FROM tracks WHERE preview_url IS NOT NULL AND TRIM(preview_url) != ''").fetchone()[0]
    conn.close()
    print(f"清理前歌曲数: {before}")
    print(f"删除不可播放歌曲: {bad_count}")
    print(f"清理后歌曲数: {after}")
    print(f"可播放歌曲数: {playable}")


if __name__ == "__main__":
    main()
