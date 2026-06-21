"""推荐解释生成。"""

from src.db.repository import TrackRepo, ArtistRepo


MODEL_NAMES = {
    "hybrid": "混合推荐",
    "itemcf": "物品协同过滤",
    "usercf": "用户协同过滤",
    "svd": "矩阵分解",
    "song2vec": "歌曲嵌入",
    "sequence": "序列推荐",
    "genre": "流派回退",
    "cold_start": "冷启动",
    "popular": "热门兜底",
    "gru4rec": "深度序列推荐",
}


def source_models(model_name):
    if model_name == "hybrid":
        return ["itemcf", "usercf", "svd", "song2vec", "sequence", "gru4rec"]
    return [model_name]


def _get_artist_name(track):
    """从 track dict 中获取艺人名称。

    优先使用 track 已有的 artist_name 字段（TrackRepo.get_by_id 等 JOIN 查询自带），
    若不存在则通过 artist_id 查库兜底。
    """
    name = track.get("artist_name")
    if name:
        return name
    artist_id = track.get("artist_id")
    if artist_id:
        artist = ArtistRepo.get_by_id(artist_id)
        if artist:
            return artist.get("name") or ""
    return ""


def recommendation_reason(track, profile, model_name, score=None):
    """根据 track 属性、用户画像、模型名称和分数生成推荐理由。

    优先级：艺人匹配 > 流派匹配 > 模型专属模板 > 冷门高分 > 默认兜底。
    """
    # ── 1. 艺人匹配（最具体的理由） ──
    artist_id = track.get("artist_id")
    if artist_id and artist_id in profile.get("artists", {}):
        artist_name = _get_artist_name(track)
        if artist_name:
            return f"因为你常听 {artist_name} 的歌"

    # ── 2. 流派匹配 ──
    genre = track.get("genre") or ""
    if genre and genre in profile.get("genres", {}):
        return f"与你偏好的 {genre} 风格相近"

    # ── 3. 模型专属模板 ──
    if model_name == "song2vec":
        return "和你的听歌口味感觉类似"
    if model_name in ("itemcf", "usercf"):
        return "喜欢类似歌曲的用户也在听"
    if model_name == "sequence":
        return "适合接在你最近的播放序列中"
    if model_name == "gru4rec":
        return "深度学习预测你接下来想听的歌"
    if model_name == "svd":
        return "基于你的历史行为预测匹配度较高"
    if model_name == "cold_start":
        return "根据你选择的初始歌曲和流派生成"
    if model_name == "genre":
        return f"基于 {genre or '你偏好'} 流派的精选推荐"
    if model_name == "popular":
        return "近期热门歌曲，值得一听"

    # ── 4. 冷门高分 ──
    popularity = track.get("popularity")
    if popularity is not None and popularity < 30 and score is not None and score > 0.5:
        return "一首你可能没听过的好歌"

    # ── 5. 默认兜底 ──
    return "综合多个模型、用户画像和实时反馈排序"


def _score_level(score):
    """将分数映射为置信等级标签。"""
    if score > 0.7:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def explain_recommendation(track, profile, model_name, score):
    models = source_models(model_name)
    return {
        "reason": recommendation_reason(track, profile, model_name, score=score),
        "source_models": models,
        "model_labels": [MODEL_NAMES.get(m, m) for m in models],
        "score_text": f"{score * 100:.1f}%",
        "score_level": _score_level(score),
    }


def best_contributing_model(track, model_name):
    """为 hybrid 模型推断最可能的贡献子模型，用于解释展示。

    对于非 hybrid 模型直接返回自身；对 hybrid 模型使用启发式判断。
    """
    if model_name != "hybrid":
        return model_name

    # heuristic: if track artist matches a known artist → itemcf 最擅长艺人关联
    artist_id = track.get("artist_id")
    if artist_id:
        # itemcf 的核心逻辑是「喜欢同艺人其他歌的人也喜欢这首歌」
        return "itemcf"

    # heuristic: if track genre is populated → svd 对流派隐因子有较强信号
    genre = track.get("genre")
    if genre:
        return "svd"

    # heuristic: otherwise assume sequence（序列模型捕捉短期偏好）
    return "sequence"
