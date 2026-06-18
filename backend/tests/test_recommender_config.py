import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ["SOUNDMIND_AUTO_INIT_ENGINE"] = "0"
os.environ["SOUNDMIND_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_recommender_config.db")
os.environ.pop("SOUNDMIND_ADMIN_USERNAME", None)
os.environ.pop("SOUNDMIND_ADMIN_PASSWORD", None)

from app.main import create_app  # noqa: E402
from app.services.engine import DEFAULT_HYBRID_WEIGHTS, engine  # noqa: E402
from src.db.schema import get_connection, init_db  # noqa: E402


def _admin_token(client):
    response = client.post("/api/admin/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.get_json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_hybrid_weight_normalization_uses_defaults_for_invalid_values():
    weights = engine._normalize_hybrid_weights({
        "itemcf": "bad",
        "usercf": -50,
        "svd": 120,
        "song2vec": 0,
        "sequence": 0,
    })

    assert weights["itemcf"] == DEFAULT_HYBRID_WEIGHTS["itemcf"]
    assert weights["usercf"] == 0
    assert weights["svd"] == 100
    assert weights["song2vec"] == 0
    assert weights["sequence"] == 0


def test_admin_hybrid_weight_api_persists_to_database():
    init_db()
    engine.admin_tokens.clear()
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    token = _admin_token(client)

    default_response = client.get("/api/admin/hybrid-weights", headers=_auth(token))
    assert default_response.status_code == 200
    assert default_response.get_json()["weights"]["itemcf"] == DEFAULT_HYBRID_WEIGHTS["itemcf"]

    payload = {"itemcf": 30, "usercf": 10, "svd": 30, "song2vec": 10, "sequence": 20}
    saved = client.put("/api/admin/hybrid-weights", json={"weights": payload}, headers=_auth(token))
    assert saved.status_code == 200
    assert saved.get_json()["weights"] == {key: float(value) for key, value in payload.items()}

    conn = get_connection()
    row = conn.execute("SELECT value FROM model_config WHERE key='hybrid_weights'").fetchone()
    conn.close()
    assert row is not None
    assert json.loads(row["value"]) == {key: float(value) for key, value in payload.items()}

    loaded = client.get("/api/admin/hybrid-weights", headers=_auth(token))
    assert loaded.status_code == 200
    assert loaded.get_json()["source"] == "database"
    assert loaded.get_json()["weights"]["svd"] == 30


def test_recommendation_indexes_are_created_by_schema_migration():
    init_db()
    conn = get_connection()

    def index_names(table):
        return {row["name"] for row in conn.execute(f"PRAGMA index_list({table})").fetchall()}

    assert "idx_history_user_track_time" in index_names("listening_history")
    assert "idx_feedback_rating_created" in index_names("feedback")
    assert "idx_feedback_user_rating_muted" in index_names("feedback")
    assert "idx_rec_logs_user_model_created" in index_names("recommendation_logs")
    assert "idx_rec_logs_track_created" in index_names("recommendation_logs")
    assert "idx_action_logs_entity" in index_names("user_action_logs")
    conn.close()
