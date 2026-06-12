"""Backend launcher - works from any working directory (PyCharm / terminal)."""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so flask can find "app.main"
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    use_reload = "--reload" in sys.argv
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=use_reload,
    )
