"""用户、推荐和反馈 API。"""

from flask import Blueprint, jsonify, request

from app.api.utils import current_user_id, int_arg, require_same_user, require_user
from app.services.engine import engine

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.route("", methods=["GET"])
def list_users():
    user_id, error = require_user()
    if error:
        return error
    return jsonify({"items": [engine.get_user(user_id)["user"]]})


@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    result = engine.get_user(user_id)
    if not result["user"]:
        return jsonify({"detail": "用户不存在"}), 404
    return jsonify(result)


@bp.route("/<int:user_id>/history", methods=["GET"])
def user_history(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    limit = int_arg("limit", 50, min_val=1, max_val=200)
    return jsonify(engine.get_user_history(user_id, limit))


@bp.route("/<int:user_id>/liked", methods=["GET"])
def liked_tracks(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    return jsonify(engine.get_liked_tracks(user_id))


@bp.route("/<int:user_id>/recommend", methods=["GET"])
def recommend(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    model = request.args.get("model", "hybrid")
    n = int_arg("n", 10, min_val=1, max_val=50)
    return jsonify(engine.recommend(user_id, model_name=model, n=n))


@bp.route("/<int:user_id>/artists", methods=["GET"])
def recommend_artists(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    n = int_arg("n", 10, min_val=1, max_val=50)
    return jsonify(engine.recommend_artists(user_id, n))


@bp.route("/<int:user_id>/playlists", methods=["GET"])
def user_playlists(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    return jsonify(engine.get_generated_playlists(user_id))


@bp.route("/feedback", methods=["POST"])
def submit_feedback():
    user_id, error = require_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    rating = data.get("rating")
    model_name = data.get("model_name", "")

    if not track_id:
        return jsonify({"detail": "缺少 track_id"}), 400
    if rating not in (-1, 0, 1):
        return jsonify({"detail": "评分必须是 -1、0 或 1"}), 400

    return jsonify(engine.submit_feedback(user_id, track_id, rating, model_name))


@bp.route("/actions", methods=["POST"])
def log_action():
    user_id = current_user_id()
    data = request.get_json(silent=True) or {}
    result = engine.log_action(user_id, data)
    if "error" in result:
        return jsonify({"detail": result["error"]}), 400
    return jsonify(result)


@bp.route("/cold-start/seeds", methods=["GET"])
def cold_start_seeds():
    n = int_arg("n", 20, min_val=5, max_val=50)
    return jsonify(engine.cold_start_seeds(n))


@bp.route("/<int:user_id>/favorites", methods=["GET"])
def user_favorites(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    return jsonify(engine.get_favorites(user_id))


@bp.route("/<int:user_id>/profile", methods=["PUT"])
def update_profile(user_id):
    current_id, error = require_user()
    if error:
        return error
    if current_id != user_id:
        return jsonify({"detail": "不能修改其他用户资料"}), 403
    data = request.get_json(silent=True) or {}
    display_name = data.get("display_name", "")
    preferred_genres = data.get("preferred_genres", "")
    avatar_url = data.get("avatar_url") if "avatar_url" in data else None
    return jsonify(engine.update_user_profile(user_id, display_name, preferred_genres, avatar_url))


@bp.route("/cold-start/recommend", methods=["POST"])
def cold_start_recommend():
    data = request.get_json(silent=True) or {}
    track_ids = data.get("track_ids", [])
    n = int_arg("n", 10, min_val=1, max_val=50)
    return jsonify(engine.cold_start_recommend(track_ids, n))
