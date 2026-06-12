"""生成离线推荐缓存。

该脚本用于演示“离线召回 + 在线重排”的离线部分。
运行后会在 data/cache 下生成每个用户的推荐候选结果。
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.services.engine import engine
from src.db.schema import get_connection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="hybrid")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--limit-users", type=int, default=200)
    args = parser.parse_args()

    engine.initialize()
    conn = get_connection()
    rows = conn.execute("SELECT id FROM users ORDER BY id LIMIT ?", (args.limit_users,)).fetchall()
    conn.close()

    cache = {}
    for row in rows:
        user_id = row["id"]
        result = engine.recommend(user_id, args.model, args.n)
        cache[str(user_id)] = [
            {
                "id": item["id"],
                "score": item.get("score", 0),
                "reason": item.get("reason", ""),
                "source_models": item.get("source_models", []),
            }
            for item in result.get("items", [])
        ]

    out_dir = ROOT / "data" / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.model}_candidates.json"
    out_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "model": args.model,
        "users": len(cache),
        "n": args.n,
        "output": str(out_file),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
