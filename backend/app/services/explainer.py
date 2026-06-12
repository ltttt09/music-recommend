"""推荐解释生成。"""


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
}


def source_models(model_name):
    if model_name == "hybrid":
        return ["itemcf", "usercf", "svd", "song2vec", "sequence"]
    return [model_name]


def recommendation_reason(track, profile, model_name):
    genre = track.get("genre") or ""
    artist_id = track.get("artist_id")
    if genre and genre in profile["genres"]:
        return f"与你偏好的 {genre} 风格相似"
    if artist_id and artist_id in profile["artists"]:
        return "与你常听的艺人风格接近"
    if track.get("audio_type") == "full":
        return "可完整播放，并与当前候选池匹配度较高"
    if model_name == "song2vec":
        return "常与相似歌曲一起被收听"
    if model_name in ("itemcf", "usercf"):
        return "相似用户或相似歌曲也经常关联到它"
    if model_name == "sequence":
        return "适合作为近期播放后的续播歌曲"
    if model_name == "svd":
        return "基于你的历史行为预测匹配度较高"
    return "综合多个模型、用户画像和实时反馈排序"


def explain_recommendation(track, profile, model_name, score):
    models = source_models(model_name)
    return {
        "reason": recommendation_reason(track, profile, model_name),
        "source_models": models,
        "model_labels": [MODEL_NAMES.get(model, model) for model in models],
        "score_text": f"{score * 100:.1f}%",
    }
