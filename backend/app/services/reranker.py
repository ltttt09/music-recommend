"""在线重排逻辑。"""

from src.db.repository import TrackRepo


def normalize_scores(scored_items):
    if not scored_items:
        return []
    scores = [float(score) for _, score, _ in scored_items]
    low, high = min(scores), max(scores)
    # P2 fix: when spread is too small, use rank-based normalization
    # to preserve ordering signal instead of assigning all 1.0
    if high - low < 0.01:
        n = len(scored_items)
        return [(track_id, round(1.0 - i / max(n - 1, 1), 4), track_obj)
                for i, (track_id, _, track_obj) in enumerate(scored_items)]
    return [(track_id, (float(score) - low) / (high - low), track_obj)
            for track_id, score, track_obj in scored_items]


def profile_boost(track, score, profile):
    if not track:
        return score
    boost = 1.0
    genre = track.get("genre") or ""
    artist_id = track.get("artist_id")
    genres = profile.get("genres") or {}
    disliked_genres = profile.get("disliked_genres") or {}
    artists = profile.get("artists") or {}

    if genre in genres:
        boost += min(genres[genre] * 0.04, 0.35)
    if genre in disliked_genres:
        boost -= min(disliked_genres[genre] * 0.08, 0.35)
    if artist_id in artists:
        boost += min(artists[artist_id] * 0.05, 0.30)
    if not track.get("preview_url"):
        boost -= 0.08
    if track.get("audio_type") == "full":
        boost += 0.05
    # Removed double popularity: score already contains model's implicit popularity
    return max(score * boost, 0)


def diversify(ranked_items, max_same_genre=3):
    """P3 fix: Penalty-based diversity instead of overflow-at-end.
    Items exceeding genre cap get exponential decay penalty but stay
    in their ranked position, preserving ordering while ensuring diversity."""  
    genre_counts = {}
    result = []
    for track_id, score, track_obj in ranked_items:
        genre = (track_obj or {}).get("genre") or "未知"
        count = genre_counts.get(genre, 0)
        if count < max_same_genre:
            result.append((track_id, score, track_obj))
        else:
            # Exponential decay: 0.85^(excess) for each genre over the cap
            penalty = 0.85 ** (count - max_same_genre + 1)
            result.append((track_id, score * penalty, track_obj))
        genre_counts[genre] = count + 1
    return result


def rerank_candidates(candidate_scores, profile, limit):
    scored = []
    for track_id, raw_score in candidate_scores:
        track = TrackRepo.get_by_id(track_id)
        if not track:
            continue
        scored.append((track_id, profile_boost(track, float(raw_score), profile), track))
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    ranked = diversify(ranked)
    normalized = normalize_scores(ranked)[:limit]
    # Return (track_id, score) tuples for backward compatibility
    return [(track_id, score) for track_id, score, _ in normalized]
