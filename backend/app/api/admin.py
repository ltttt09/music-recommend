"""后台管理 API。"""

import os
import time
from functools import wraps

import psutil
from flask import Blueprint, jsonify, request

from app.config import get_admin_password
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
    password = data.get("password", "")
    try:
        admin_password = get_admin_password()
    except RuntimeError as exc:
        return jsonify({"detail": str(exc)}), 500
    if password != admin_password:
        return jsonify({"detail": "密码错误"}), 401
    token = engine.create_admin_token()
    return jsonify({"token": token})


@bp.route("/stats", methods=["GET"])
@require_admin
def stats():
    return jsonify(engine.admin_stats())


@bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 20, min_val=1, max_val=100)
    return jsonify(engine.admin_users(page, size))


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
    try:
        engine.initialize(force_reseed=force)
        return jsonify({"status": "ok", "message": "模型重新训练完成"})
    except Exception as e:
        return jsonify({"detail": str(e)}), 500


@bp.route("/feedback", methods=["GET"])
@require_admin
def feedback_stats():
    return jsonify(engine.admin_feedback_stats())


@bp.route("/comments", methods=["GET"])
@require_admin
def comments():
    page = _int_arg("page", 1, min_val=1)
    size = _int_arg("size", 20, min_val=1, max_val=100)
    return jsonify(engine.admin_comments(page, size))


@bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@require_admin
def delete_comment(comment_id):
    return jsonify(engine.admin_delete_comment(comment_id))


@bp.route("/model-metrics", methods=["GET"])
@require_admin
def model_metrics():
    return jsonify(engine.admin_model_metrics())


@bp.route("/model-metrics/jobs", methods=["POST"])
@require_admin
def start_model_metrics_job():
    data = request.get_json(silent=True) or {}
    try:
        sample_users = max(1, min(int(data.get("sample_users") or 50), 300))
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
