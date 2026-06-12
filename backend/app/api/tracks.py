"""歌曲、评论和歌单 API。"""

from flask import Blueprint, jsonify, request

from app.api.utils import int_arg, require_same_user, require_user
from app.services.engine import engine
from src.db.schema import get_connection

bp = Blueprint("tracks", __name__, url_prefix="/api/tracks")


def _owns_user_playlist(user_id, playlist_id):
    conn = get_connection()
    row = conn.execute("SELECT user_id FROM user_playlists WHERE id=?", (playlist_id,)).fetchone()
    conn.close()
    return row is not None and row["user_id"] == user_id


@bp.route("", methods=["GET"])
def list_tracks():
    page = int_arg("page", 1, min_val=1)
    size = int_arg("size", 20, min_val=1, max_val=100)
    search = request.args.get("search", "")
    genre = request.args.get("genre", "")
    year_from = int_arg("year_from", 0, min_val=0)
    year_to = int_arg("year_to", 0, min_val=0)
    language = request.args.get("language", "")
    sort_by = request.args.get("sort_by", "popularity")
    sort_order = request.args.get("sort_order", "desc")
    return jsonify(engine.get_tracks(page=page, size=size, search=search, genre=genre, year_from=year_from, year_to=year_to, language=language, sort_by=sort_by, sort_order=sort_order))


@bp.route("/trending", methods=["GET"])
def trending():
    limit = int_arg("limit", 20, min_val=1, max_val=100)
    return jsonify(engine.get_trending(limit))


@bp.route("/genres", methods=["GET"])
def genres():
    return jsonify(engine.get_genres())


@bp.route("/<int:track_id>", methods=["GET"])
def get_track(track_id):
    track = engine.get_track(track_id)
    if not track:
        return jsonify({"detail": "歌曲不存在"}), 404
    return jsonify(track)


@bp.route("/<int:track_id>/similar", methods=["GET"])
def similar_tracks(track_id):
    n = int_arg("n", 10, min_val=1, max_val=50)
    return jsonify(engine.similar_tracks(track_id, n=n))


@bp.route("/playlist/generate", methods=["POST"])
def generate_playlist():
    user_id, error = require_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    seed_track_id = data.get("seed_track_id")
    length = data.get("length", 20)
    if not seed_track_id:
        return jsonify({"detail": "缺少 seed_track_id"}), 400
    return jsonify(engine.generate_playlist(seed_track_id, user_id, length))


@bp.route("/playlist/<int:playlist_id>", methods=["GET"])
def get_playlist(playlist_id):
    return jsonify(engine.get_playlist(playlist_id))


@bp.route("/user-playlists", methods=["POST"])
def create_user_playlist():
    user_id, error = require_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"detail": "歌单名称不能为空"}), 400
    return jsonify(engine.create_user_playlist(user_id, name, data.get("description", "")))


@bp.route("/user-playlists/<int:user_id>", methods=["GET"])
def list_user_playlists(user_id):
    _, error = require_same_user(user_id)
    if error:
        return error
    return jsonify(engine.get_user_playlists(user_id))


@bp.route("/user-playlist/<int:playlist_id>", methods=["GET"])
def get_user_playlist(playlist_id):
    result = engine.get_user_playlist(playlist_id)
    if not result:
        return jsonify({"detail": "歌单未找到"}), 404
    return jsonify(result)


@bp.route("/user-playlist/<int:playlist_id>/tracks", methods=["POST"])
def add_to_user_playlist(playlist_id):
    user_id, error = require_user()
    if error:
        return error
    if not _owns_user_playlist(user_id, playlist_id):
        return jsonify({"detail": "不能修改其他用户的歌单"}), 403
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    if not track_id:
        return jsonify({"detail": "缺少 track_id"}), 400
    return jsonify(engine.add_track_to_playlist(playlist_id, track_id))


@bp.route("/user-playlist/<int:playlist_id>/tracks/<int:track_id>", methods=["DELETE"])
def remove_from_user_playlist(playlist_id, track_id):
    user_id, error = require_user()
    if error:
        return error
    if not _owns_user_playlist(user_id, playlist_id):
        return jsonify({"detail": "不能修改其他用户的歌单"}), 403
    return jsonify(engine.remove_track_from_playlist(playlist_id, track_id))


@bp.route("/user-playlist/<int:playlist_id>", methods=["DELETE"])
def delete_user_playlist(playlist_id):
    user_id, error = require_user()
    if error:
        return error
    if not _owns_user_playlist(user_id, playlist_id):
        return jsonify({"detail": "不能删除其他用户的歌单"}), 403
    return jsonify(engine.delete_user_playlist(playlist_id))


@bp.route("/<int:track_id>/favorite", methods=["POST"])
def toggle_favorite(track_id):
    user_id, error = require_user()
    if error:
        return error
    return jsonify(engine.toggle_favorite(user_id, track_id))


@bp.route("/<int:track_id>/favorite", methods=["GET"])
def check_favorite(track_id):
    user_id, error = require_user()
    if error:
        return error
    return jsonify(engine.is_favorited(user_id, track_id))


@bp.route("/<int:track_id>/state", methods=["GET"])
def track_state(track_id):
    user_id, error = require_user()
    if error:
        return error
    return jsonify(engine.get_track_state(user_id, track_id))


@bp.route("/<int:track_id>/comments", methods=["GET"])
def list_comments(track_id):
    return jsonify(engine.get_comments(track_id))


@bp.route("/<int:track_id>/comment", methods=["POST"])
def add_comment(track_id):
    user_id, error = require_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"detail": "评论内容不能为空"}), 400
    if len(content) > 500:
        return jsonify({"detail": "评论不能超过500字"}), 400
    return jsonify(engine.add_comment(user_id, track_id, content))
