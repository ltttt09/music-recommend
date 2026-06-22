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


def diversify(ranked_items, lambda_param=0.7):
    """MMR (Maximal Marginal Relevance) diversity reranking.

    MMR(d) = λ * relevance(d) - (1-λ) * max_sim(d, selected)

    Where:
    - λ = 0.7: 70% weight on relevance, 30% on diversity
    - max_sim: maximum genre similarity to any already-selected item
    - Similarity: 1.0 if same genre, 0.0 otherwise

    Greedy selection: iteratively pick the item with highest MMR score.
    """
    if not ranked_items:
        return []

    selected = []
    candidates = list(ranked_items)

    while candidates:
        best_mmr = -float('inf')
        best_idx = 0

        for idx, (track_id, score, track_obj) in enumerate(candidates):
            genre = (track_obj or {}).get("genre") or "未知"

            # Compute max similarity to already-selected items
            if selected:
                max_sim = 0.0
                for sel_tid, sel_score, sel_obj in selected:
                    sel_genre = (sel_obj or {}).get("genre") or "未知"
                    sim = 1.0 if genre == sel_genre else 0.0
                    if sim > max_sim:
                        max_sim = sim
            else:
                max_sim = 0.0

            # MMR score
            mmr = lambda_param * score - (1 - lambda_param) * max_sim

            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = idx

        # Move best candidate to selected
        selected.append(candidates.pop(best_idx))

    return selected


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
