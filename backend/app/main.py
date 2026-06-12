"""Flask 应用入口。"""

from flask import Flask
from flask_cors import CORS

from app.services.engine import engine


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    _initialized = False

    @app.before_request
    def init_engine():
        nonlocal _initialized
        if not _initialized:
            print("\n" + "=" * 50)
            print("  音乐推荐 API 启动中...")
            print("=" * 50)
            engine.initialize()
            _initialized = True

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
        return {"status": "ok"}

    return app
