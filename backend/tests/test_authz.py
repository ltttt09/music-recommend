import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ["MUSIC_AUTO_INIT_ENGINE"] = "0"
os.environ["MUSIC_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_music.db")

from app.main import create_app  # noqa: E402
from app.services.engine import engine  # noqa: E402
from src.db.schema import init_db  # noqa: E402


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
