"""Flask 应用入口。"""

import threading

from flask import Flask
from flask_cors import CORS

from app.config import AUTO_INIT_ENGINE, CORS_ORIGINS
from app.services.engine import engine


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""
    app = Flask(__name__)

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
