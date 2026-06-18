import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ["SOUNDMIND_AUTO_INIT_ENGINE"] = "0"
os.environ["SOUNDMIND_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_soundmind.db")

from app.main import create_app  # noqa: E402
from app.services.engine import engine  # noqa: E402
from src.db.schema import get_connection, init_db  # noqa: E402


def _register_and_login(client, username):
    password = "secret123"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "display_name": username},
    )
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    data = response.get_json()
    return data["user_id"], data["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_track(track_id=9101, title="测试歌曲"):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (9101, '测试歌手')")
    conn.execute(
        """INSERT OR REPLACE INTO tracks
           (id, title, artist_id, album, genre, language, preview_url, popularity)
           VALUES (?, ?, 9101, '测试专辑', '华语流行', 'CN', 'http://example.com/test.m4a', 80)""",
        (track_id, title),
    )
    conn.commit()
    conn.close()
    return track_id


def test_user_cannot_read_another_users_history():
    init_db()
    engine.auth_tokens.clear()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    user_a, token_a = _register_and_login(client, "alice")
    user_b, _ = _register_and_login(client, "bob")

    assert user_a != user_b
    response = client.get(
        f"/api/users/{user_b}/history",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 403


def test_track_state_requires_token():
    init_db()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/api/tracks/1/state?user_id=1")

    assert response.status_code == 401


def test_auth_me_returns_current_user_without_password_fields():
    init_db()
    engine.auth_tokens.clear()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    user_id, token = _register_and_login(client, "charlie")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    user = response.get_json()["user"]
    assert user["id"] == user_id
    assert "password_hash" not in user
    assert "salt" not in user


def test_track_language_filter_prefers_language_column_with_genre_fallback():
    init_db()
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (9001, '测试艺人')")
    conn.execute(
        """INSERT OR REPLACE INTO tracks
           (id, title, artist_id, genre, language, preview_url, popularity)
           VALUES (9001, '中文语言字段歌曲', 9001, 'Pop', 'CN', 'http://example.com/a.m4a', 90)"""
    )
    conn.execute(
        """INSERT OR REPLACE INTO tracks
           (id, title, artist_id, genre, language, preview_url, popularity)
           VALUES (9002, '中文流派回退歌曲', 9001, 'CN-Pop', '', 'http://example.com/b.m4a', 80)"""
    )
    conn.execute(
        """INSERT OR REPLACE INTO tracks
           (id, title, artist_id, genre, language, preview_url, popularity)
           VALUES (9003, '日语歌曲', 9001, 'JP-Pop', 'JP', 'http://example.com/c.m4a', 70)"""
    )
    conn.commit()
    conn.close()

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/api/tracks?language=CN&size=20")
    assert response.status_code == 200
    titles = {item["title"] for item in response.get_json()["items"]}
    assert "中文语言字段歌曲" in titles
    assert "中文流派回退歌曲" in titles
    assert "日语歌曲" not in titles


def test_user_playlist_create_list_duplicate_and_delete():
    init_db()
    engine.auth_tokens.clear()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    user_id, token = _register_and_login(client, "playlist_user")
    response = client.post(
        "/api/tracks/user-playlists",
        json={"name": "测试歌单"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    playlist_id = response.get_json()["id"]

    duplicate = client.post(
        "/api/tracks/user-playlists",
        json={"name": "测试歌单"},
        headers=_auth(token),
    )
    assert duplicate.status_code == 409

    listing = client.get(f"/api/tracks/user-playlists/{user_id}", headers=_auth(token))
    assert listing.status_code == 200
    assert any(item["id"] == playlist_id for item in listing.get_json()["items"])

    deleted = client.delete(f"/api/tracks/user-playlist/{playlist_id}", headers=_auth(token))
    assert deleted.status_code == 200


def test_comments_support_like_reply_and_soft_delete():
    init_db()
    engine.auth_tokens.clear()
    track_id = _seed_track(9201, "评论测试歌曲")
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    _, token = _register_and_login(client, "comment_user")
    created = client.post(
        f"/api/tracks/{track_id}/comment",
        json={"content": "第一条评论"},
        headers=_auth(token),
    )
    assert created.status_code == 200
    comment_id = created.get_json()["id"]

    liked = client.post(f"/api/tracks/comments/{comment_id}/like", headers=_auth(token))
    assert liked.status_code == 200
    assert liked.get_json()["liked"] is True
    unliked = client.post(f"/api/tracks/comments/{comment_id}/like", headers=_auth(token))
    assert unliked.status_code == 200
    assert unliked.get_json()["liked"] is False

    reply = client.post(
        f"/api/tracks/{track_id}/comment",
        json={"content": "回复内容", "parent_id": comment_id},
        headers=_auth(token),
    )
    assert reply.status_code == 200
    assert reply.get_json()["parent_id"] == comment_id

    deleted = client.delete(f"/api/tracks/comments/{comment_id}", headers=_auth(token))
    assert deleted.status_code == 200

    listing = client.get(f"/api/tracks/{track_id}/comments?page=1&size=10", headers=_auth(token))
    assert listing.status_code == 200
    item = listing.get_json()["items"][0]
    assert item["content"] == "评论已删除"
    assert item["replies"][0]["content"] == "回复内容"


def test_skip_feedback_adds_and_removes_blacklist_item():
    init_db()
    engine.auth_tokens.clear()
    track_id = _seed_track(9301, "黑名单测试歌曲")
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    user_id, token = _register_and_login(client, "blacklist_user")
    skipped = client.post(
        "/api/users/feedback",
        json={"track_id": track_id, "rating": -1, "model_name": "hybrid"},
        headers=_auth(token),
    )
    assert skipped.status_code == 200
    assert skipped.get_json()["skipped"] is True

    listing = client.get(f"/api/users/{user_id}/blacklist", headers=_auth(token))
    assert listing.status_code == 200
    assert any(item["id"] == track_id for item in listing.get_json()["items"])

    removed = client.delete(f"/api/users/{user_id}/blacklist/{track_id}", headers=_auth(token))
    assert removed.status_code == 200
    listing = client.get(f"/api/users/{user_id}/blacklist", headers=_auth(token))
    assert not any(item["id"] == track_id for item in listing.get_json()["items"])
