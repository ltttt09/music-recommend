import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ["SOUNDMIND_AUTO_INIT_ENGINE"] = "0"
os.environ["SOUNDMIND_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_admin_soundmind.db")
os.environ.pop("SOUNDMIND_ADMIN_USERNAME", None)
os.environ.pop("SOUNDMIND_ADMIN_PASSWORD", None)

from app.main import create_app  # noqa: E402
from app.services.engine import engine  # noqa: E402
from src.db.schema import init_db  # noqa: E402


def test_admin_login_is_separate_from_user_login():
    init_db()
    engine.admin_tokens.clear()
    engine.auth_tokens.clear()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    unauthorized = client.get("/api/admin/stats")
    assert unauthorized.status_code == 401

    logged_in = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin"},
    )
    assert logged_in.status_code == 200
    token = logged_in.get_json()["token"]

    authorized = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert authorized.status_code == 200

    user_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert user_login.status_code == 401


def test_admin_reserved_username_cannot_be_registered_as_user():
    init_db()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "admin", "display_name": "admin"},
    )

    assert response.status_code == 409
