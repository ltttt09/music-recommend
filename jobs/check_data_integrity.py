"""检查音乐数据库完整性，不修改数据。

用法：
    python jobs/check_data_integrity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sqlite3  # noqa: E402

from src.db.schema import DB_PATH  # noqa: E402


def scalar(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def rows(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def main() -> int:
    db_uri = "file:" + str(DB_PATH.resolve()).replace("\\", "/") + "?mode=ro&immutable=1"
    conn = sqlite3.connect(db_uri, uri=True)
    conn.row_factory = sqlite3.Row
    report = {
        "counts": {
            "tracks": scalar(conn, "SELECT COUNT(*) FROM tracks"),
            "playable_tracks": scalar(conn, "SELECT COUNT(*) FROM tracks WHERE preview_url != ''"),
            "artists": scalar(conn, "SELECT COUNT(*) FROM artists"),
            "users": scalar(conn, "SELECT COUNT(*) FROM users"),
            "listening_history": scalar(conn, "SELECT COUNT(*) FROM listening_history"),
        },
        "issues": {
            "tracks_without_artist": rows(
                conn,
                """SELECT t.id, t.title, t.artist_id
                   FROM tracks t
                   LEFT JOIN artists a ON a.id = t.artist_id
                   WHERE a.id IS NULL
                   LIMIT 100""",
            ),
            "unplayable_tracks": rows(
                conn,
                "SELECT id, title, source, external_id FROM tracks WHERE preview_url = '' LIMIT 100",
            ),
            "duplicate_external_ids": rows(
                conn,
                """SELECT source, external_id, COUNT(*) AS count
                   FROM tracks
                   WHERE source != '' AND external_id != ''
                   GROUP BY source, external_id
                   HAVING COUNT(*) > 1
                   ORDER BY count DESC
                   LIMIT 100""",
            ),
            "orphan_history": rows(
                conn,
                """SELECT lh.id, lh.user_id, lh.track_id
                   FROM listening_history lh
                   LEFT JOIN users u ON u.id = lh.user_id
                   LEFT JOIN tracks t ON t.id = lh.track_id
                   WHERE u.id IS NULL OR t.id IS NULL
                   LIMIT 100""",
            ),
            "orphan_feedback": rows(
                conn,
                """SELECT f.id, f.user_id, f.track_id
                   FROM feedback f
                   LEFT JOIN users u ON u.id = f.user_id
                   LEFT JOIN tracks t ON t.id = f.track_id
                   WHERE u.id IS NULL OR t.id IS NULL
                   LIMIT 100""",
            ),
            "non_itunes_sources": rows(
                conn,
                """SELECT source, COUNT(*) AS count
                   FROM tracks
                   WHERE LOWER(COALESCE(source, '')) != 'itunes'
                   GROUP BY source
                   ORDER BY count DESC""",
            ),
        },
    }
    conn.close()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(report["issues"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
