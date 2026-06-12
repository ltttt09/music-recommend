"""API 层公共工具。"""

from __future__ import annotations

from flask import jsonify, request

from app.services.engine import engine


def int_arg(name: str, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    value = request.args.get(name, default, type=int)
    if min_val is not None and value < min_val:
        value = min_val
    if max_val is not None and value > max_val:
        value = max_val
    return value


def current_user_id() -> int | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return engine.get_user_by_token(auth[7:])


def require_user():
    user_id = current_user_id()
    if not user_id:
        return None, (jsonify({"detail": "请先登录"}), 401)
    return user_id, None


def require_same_user(path_user_id: int):
    current_id, error = require_user()
    if error:
        return None, error
    if current_id != path_user_id:
        return None, (jsonify({"detail": "不能访问其他用户的数据"}), 403)
    return current_id, None
