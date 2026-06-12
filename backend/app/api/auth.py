"""认证 API。"""

from flask import Blueprint, jsonify, request

from app.services.engine import engine

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    display_name = data.get("display_name", "")

    if len(username) < 3 or len(password) < 4:
        return jsonify({"detail": "用户名至少 3 个字符，密码至少 4 个字符"}), 400

    result = engine.register(username, password, display_name)
    if "error" in result:
        return jsonify({"detail": result["error"]}), 409

    return jsonify(result)


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    result = engine.login(username, password)
    if "error" in result:
        return jsonify({"detail": result["error"]}), 401

    return jsonify(result)
