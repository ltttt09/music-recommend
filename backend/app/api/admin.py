"""后台管理 API。"""

import os
import time
from functools import wraps

import psutil
from flask import Blueprint, jsonify, request

from app.config import get_admin_password, get_admin_username
from app.services.engine import engine

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

_start_time = time.time()


def _int_arg(name, default, min_val=None, max_val=None):
    val = request.args.get(name, default, type=int)
    if min_val is not None and val < min_val:
        val = min_val
    if max_val is not None and val > max_val:
        val = max_val
    return val


def require_admin(fn):
    """要求后台 Bearer token。"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"detail": "未授权访问"}), 401
        token = auth[7:]
        if not engine.verify_admin_token(token):
            return jsonify({"detail": "未授权访问"}), 401
        return fn(*args, **kwargs)
    return wrapper


@bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    try:
        admin_username = get_admin_username()
        admin_password = get_admin_password()
    except RuntimeError as exc:
        return jsonify({"detail": str(exc)}), 500
    if username != admin_username or password != admin_password:
        return jsonify({"detail": "管理员账号或密码错误"}), 401
    token = engine.create_admin_token()
    return jsonify({"token": token, "username": admin_username})


@bp.route("/stats", methods=["GET"])
@require_admin
def stats():
    return jsonify(engine.admin_stats())


@bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 20, min_val=1, max_val=100)
    search = request.args.get("search", "").strip()
    genre = request.args.get("genre", "").strip()
    sort_by = request.args.get("sort_by", "id").strip()
    sort_order = request.args.get("sort_order", "asc").strip()
    return jsonify(engine.admin_users(page, size, search=search, genre=genre, sort_by=sort_by, sort_order=sort_order))


@bp.route("/users/delete", methods=["POST"])
@require_admin
def delete_user():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"detail": "缺少 user_id"}), 400
    return jsonify(engine.admin_delete_user(user_id))


@bp.route("/tracks", methods=["GET"])
@require_admin
def list_tracks():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 20, min_val=1, max_val=100)
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc")
    return jsonify(engine.admin_tracks(page, size, search, sort_by, sort_order))


@bp.route("/tracks/delete", methods=["POST"])
@require_admin
def delete_track():
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    if not track_id:
        return jsonify({"detail": "缺少 track_id"}), 400
    return jsonify(engine.admin_delete_track(track_id))


@bp.route("/tracks/<int:track_id>", methods=["PUT"])
@require_admin
def update_track(track_id):
    data = request.get_json(silent=True) or {}
    result = engine.admin_update_track(track_id, data)
    if "error" in result:
        return jsonify({"detail": result["error"]}), 400
    return jsonify(result)


@bp.route("/system", methods=["GET"])
@require_admin
def system_info():
    process = psutil.Process(os.getpid())
    mem = process.memory_info()
    return jsonify({
        "uptime_seconds": round(time.time() - _start_time),
        "memory_mb": round(mem.rss / 1024 / 1024, 1),
        "cpu_percent": process.cpu_percent(),
        "python_version": os.sys.version,
        "models_loaded": list(engine.ml_models.keys()),
    })


@bp.route("/retrain", methods=["POST"])
@require_admin
def retrain():
    data = request.get_json(silent=True) or {}
    force = data.get("force", False)
    scope = data.get("scope", "all")
    model_names = None if scope == "all" else [scope] if scope else None
    try:
        engine.retrain_models(force_reseed=force, model_names=model_names)
        return jsonify({"status": "ok", "message": "模型重新训练完成"})
    except Exception as e:
        return jsonify({"detail": str(e)}), 500


@bp.route("/retrain-progress", methods=["GET"])
@require_admin
def retrain_progress():
    return jsonify(engine.get_train_progress())


@bp.route("/feedback", methods=["GET"])
@require_admin
def feedback_stats():
    return jsonify(engine.admin_feedback_stats())


@bp.route("/import-itunes", methods=["POST"])
@require_admin
def import_itunes():
    data = request.get_json(silent=True) or {}
    target = data.get("target", 10000)
    limit_per_query = data.get("limit_per_query", 200)
    return jsonify(engine.admin_import_itunes(target, limit_per_query))


@bp.route("/import-progress", methods=["GET"])
@require_admin
def import_progress():
    return jsonify(engine.admin_import_progress())


@bp.route("/import-cancel", methods=["POST"])
@require_admin
def import_cancel():
    return jsonify(engine.admin_cancel_import())


@bp.route("/model-metrics/cancel", methods=["POST"])
@require_admin
def metrics_cancel():
    """Cancel an in-progress model metrics evaluation job."""
    return jsonify(engine.cancel_metrics_job())


@bp.route("/retrain-cancel", methods=["POST"])
@require_admin
def retrain_cancel():
    """Cancel an in-progress model retraining."""
    return jsonify(engine.cancel_retrain())


@bp.route("/seed-engagement", methods=["POST"])
@require_admin
def seed_engagement():
    data = request.get_json(silent=True) or {}
    likes_per_user = data.get("likes_per_user", 8)
    comments_per_user = data.get("comments_per_user", 2)
    comment_likes_per_user = data.get("comment_likes_per_user", 3)
    playlists_per_user = data.get("playlists_per_user", 1)
    return jsonify(engine.admin_seed_engagement(likes_per_user, comments_per_user, comment_likes_per_user, playlists_per_user))


@bp.route("/comments", methods=["GET"])
@require_admin
def comments():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 20, min_val=1, max_val=100)
    search = request.args.get("search", "").strip()
    return jsonify(engine.admin_comments(page, size, search))


@bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@require_admin
def delete_comment(comment_id):
    return jsonify(engine.admin_delete_comment(comment_id))


@bp.route("/model-metrics", methods=["GET"])
@require_admin
def model_metrics():
    return jsonify(engine.admin_model_metrics())


@bp.route("/hybrid-weights", methods=["GET"])
@require_admin
def get_hybrid_weights():
    return jsonify(engine.get_hybrid_weights())


@bp.route("/hybrid-weights", methods=["PUT"])
@require_admin
def update_hybrid_weights():
    data = request.get_json(silent=True) or {}
    weights = data.get("weights", data)
    if not isinstance(weights, dict):
        return jsonify({"detail": "weights 必须是对象"}), 400
    return jsonify(engine.save_hybrid_weights(weights))


@bp.route("/model-metrics/jobs", methods=["POST"])
@require_admin
def start_model_metrics_job():
    data = request.get_json(silent=True) or {}
    try:
        sample_users = max(1, min(int(data.get("sample_users") or 80), 300))
        n = max(1, min(int(data.get("n") or 10), 50))
    except (TypeError, ValueError):
        return jsonify({"detail": "sample_users 和 n 必须是数字"}), 400
    model_names = data.get("models") or None
    if model_names is not None and not isinstance(model_names, list):
        return jsonify({"detail": "models 必须是数组"}), 400
    return jsonify(engine.start_admin_model_metrics_job(sample_users, n, model_names))


@bp.route("/model-metrics/jobs/<job_id>", methods=["GET"])
@require_admin
def model_metrics_job(job_id):
    job = engine.get_admin_model_metrics_job(job_id)
    if not job:
        return jsonify({"detail": "任务不存在或已过期"}), 404
    return jsonify(job)


@bp.route("/recommendation-logs", methods=["GET"])
@require_admin
def recommendation_logs():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 50, min_val=1, max_val=200)
    search = request.args.get("search", "")
    model_name = request.args.get("model_name", "")
    return jsonify(engine.admin_recommendation_logs(page, size, search, model_name))


@bp.route("/action-logs", methods=["GET"])
@require_admin
def action_logs():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 100, min_val=1, max_val=200)
    action_type = request.args.get("action_type", "")
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    return jsonify(engine.admin_action_logs(page, size, action_type, status, search))


@bp.route("/users/<int:user_id>/profile", methods=["GET"])
@require_admin
def user_profile(user_id):
    return jsonify(engine.admin_user_profile(user_id))


@bp.route("/data-sources", methods=["GET"])
@require_admin
def data_sources():
    return jsonify(engine.admin_data_sources())
