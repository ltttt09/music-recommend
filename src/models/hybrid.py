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
                  recent_tracks: list | None = None) -> list[tuple[int, float]]:
        all_scores = defaultdict(float)

        for model, weight in zip(self.models, self.weights):
            try:
                # Check if model supports recent_tracks
                import inspect
                sig = inspect.signature(model.recommend)
                if "recent_tracks" in sig.parameters:
                    recs = model.recommend(user_id, n=n * 2,
                                           recent_tracks=recent_tracks)
                else:
                    recs = model.recommend(user_id, n=n * 2)
            except Exception:
                continue

            if not recs:
                continue

            scores = [s for _, s in recs]
            s_min, s_max = min(scores), max(scores)
            if s_max > s_min:
                scores = [(s - s_min) / (s_max - s_min) for s in scores]
            else:
                scores = [1.0] * len(scores)

            for (item, _), norm_score in zip(recs, scores):
                all_scores[item] += weight * norm_score

        ranked = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:n]
