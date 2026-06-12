"""工具函数模块。"""

import pickle
from pathlib import Path


def print_recommendations(
    recommendations: list, df_tracks, title: str = "推荐结果"
):
    """格式化打印推荐列表。"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

    if not recommendations:
        print("  (无推荐结果)")
        return

    for i, item in enumerate(recommendations, 1):
        if isinstance(item, tuple):
            track_id, score = item
        else:
            track_id, score = item, 0.0

        # 查找曲目信息
        track_info = df_tracks[df_tracks["track_id_idx"] == track_id]
        if len(track_info) > 0:
            name = track_info.iloc[0]["track_name"]
            artist = track_info.iloc[0]["artist_name"]
        else:
            name = str(track_id)
            artist = "未知"

        print(f"  {i:2d}. {name[:35]:35s} | {artist[:20]:20s} | score={score:.4f}")
    print(f"{'=' * 60}\n")


def save_model(model, filepath: str):
    """保存模型到文件。"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"模型已保存至: {path}")


def load_model(filepath: str):
    """从文件加载模型。"""
    with open(filepath, "rb") as f:
        return pickle.load(f)
