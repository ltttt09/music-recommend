"""Flask 应用入口。"""

import os
import threading

from flask import Flask, send_from_directory
from flask_cors import CORS

from app.config import AUTO_INIT_ENGINE, CORS_ORIGINS
from app.services.engine import engine

# 前端打包产物的路径（相对于 backend/ 目录）
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""
    app = Flask(__name__, static_folder=os.path.join(_frontend_dist, "assets"), static_url_path="/assets")

    # ---- 提供前端页面 ----
    @app.route("/")
    def serve_index():
        return send_from_directory(_frontend_dist, "index.html")

    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

    if AUTO_INIT_ENGINE:
        threading.Thread(target=engine.initialize, name="engine-warmup", daemon=True).start()

    from app.api.tracks import bp as tracks_bp
    from app.api.users import bp as users_bp
    from app.api.auth import bp as auth_bp
    from app.api.admin import bp as admin_bp

    app.register_blueprint(tracks_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.route("/api/models")
    def list_models():
        return engine.get_models()

    @app.route("/api/health")
    def health():
        return {
            "status": "ok",
            "engine_initialized": engine.is_initialized,
            "engine_initializing": engine.is_initializing,
            "engine_error": engine.initialization_error,
        }

    return app
