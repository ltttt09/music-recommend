"""
Hybrid recommendation model.

Weighted fusion of multiple recommenders to combine their strengths.
"""

from collections import defaultdict
import numpy as np


class HybridRecommender:
    """Weighted fusion of multiple recommendation models.

    Strategy:
    1. Collect recommendations from each model
    2. Normalize and weight scores per model
    3. Rank by final weighted score
    """

    def __init__(self, models: list, weights: list[float] | None = None):
        self.models = models
        if weights is None:
            self.weights = [1.0 / len(models)] * len(models)
        else:
            total = sum(weights)
            self.weights = [w / total for w in weights]

    def recommend(self, user_id: int, n: int = 10,
                  recent_tracks: list | None = None,
                  exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        all_scores = defaultdict(float)

        for model, weight in zip(self.models, self.weights):
            try:
                # Check if model supports recent_tracks and exclude_track_ids
                import inspect
                sig = inspect.signature(model.recommend)
                kwargs = {"n": n * 2}
                if "recent_tracks" in sig.parameters:
                    kwargs["recent_tracks"] = recent_tracks
                if "exclude_track_ids" in sig.parameters:
                    kwargs["exclude_track_ids"] = exclude_track_ids
                recs = model.recommend(user_id, **kwargs)
            except Exception:
                continue

            if not recs:
                continue

            scores = [s for _, s in recs]
            s_min, s_max = min(scores), max(scores)
            # P2 fix: use rank-based normalization when spread too small
            if s_max - s_min < 0.01:
                n_recs = len(scores)
                scores = [round(1.0 - i / max(n_recs - 1, 1), 4) for i in range(n_recs)]
            elif s_max > s_min:
                scores = [(s - s_min) / (s_max - s_min) for s in scores]
            else:
                scores = [1.0 / len(scores)] * len(scores)

            for (item, _), norm_score in zip(recs, scores):
                all_scores[item] += weight * norm_score

        ranked = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:n]
