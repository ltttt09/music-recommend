"""应用配置。

所有运行环境相关配置集中在这里，避免散落在 API 和服务实现中。
"""

from __future__ import annotations

import os


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SOUNDMIND_ENV = os.getenv("SOUNDMIND_ENV", "development").strip().lower()
IS_PRODUCTION = SOUNDMIND_ENV in {"prod", "production"}

CORS_ORIGINS = _csv_env(
    "SOUNDMIND_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

TOKEN_TTL_SECONDS = _int_env("SOUNDMIND_TOKEN_TTL_SECONDS", 60 * 60 * 24)
AUTO_INIT_ENGINE = _bool_env("SOUNDMIND_AUTO_INIT_ENGINE", True)


def get_admin_username() -> str:
    """Return the admin username used by the separate admin console."""
    username = os.getenv("SOUNDMIND_ADMIN_USERNAME", "").strip()
    if username:
        return username
    if IS_PRODUCTION:
        raise RuntimeError("生产环境必须设置 SOUNDMIND_ADMIN_USERNAME")
    return "admin"


def get_admin_password() -> str:
    """Return the admin password used by the separate admin console."""
    password = os.getenv("SOUNDMIND_ADMIN_PASSWORD", "").strip()
    if password:
        return password
    if IS_PRODUCTION:
        raise RuntimeError("生产环境必须设置 SOUNDMIND_ADMIN_PASSWORD")
    return "admin"
