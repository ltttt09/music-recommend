"""在线重排逻辑。"""

from src.db.repository import TrackRepo


def normalize_scores(scored_items):
    if not scored_items:
        return []
    scores = [float(score) for _, score in scored_items]
    low, high = min(scores), max(scores)
    if high <= low:
        return [(track_id, 1.0) for track_id, _ in scored_items]
    return [(track_id, (float(score) - low) / (high - low)) for track_id, score in scored_items]


def profile_boost(track, score, profile):
    if not track:
        return score
    boost = 1.0
    genre = track.get("genre") or ""
    artist_id = track.get("artist_id")
    if genre in profile["genres"]:
        boost += min(profile["genres"][genre] * 0.04, 0.35)
    if genre in profile.get("disliked_genres", {}):
        boost -= min(profile["disliked_genres"][genre] * 0.08, 0.35)
    if artist_id in profile["artists"]:
        boost += min(profile["artists"][artist_id] * 0.05, 0.30)
    if not track.get("preview_url"):
        boost -= 0.08
    if track.get("audio_type") == "full":
        boost += 0.05
    popularity = min(max(float(track.get("popularity") or 0) / 100.0, 0), 1)
    return max(score * boost + popularity * 0.05, 0)


def diversify(ranked_items, max_same_genre=3):
    genre_counts = {}
    result = []
    overflow = []
    for track_id, score in ranked_items:
        track = TrackRepo.get_by_id(track_id)
        genre = (track or {}).get("genre") or "未知"
        if genre_counts.get(genre, 0) < max_same_genre:
            result.append((track_id, score))
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        else:
            overflow.append((track_id, score * 0.92))
    return result + overflow


def rerank_candidates(candidate_scores, profile, limit):
    scored = []
    for track_id, raw_score in candidate_scores:
        track = TrackRepo.get_by_id(track_id)
        if not track:
            continue
        scored.append((track_id, profile_boost(track, float(raw_score), profile)))
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    ranked = diversify(ranked)
    return normalize_scores(ranked)[:limit]
