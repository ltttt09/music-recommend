"""
Hybrid recommendation model.

Weighted fusion of multiple recommenders to combine their strengths.

Improvements:
- Expanded candidate pool (n*4 instead of n*2)
- Model agreement boost: items recommended by multiple models get extra weight
- Exploration mechanism: 10% random tracks to improve coverage
"""

from collections import defaultdict
import numpy as np
import random


class HybridRecommender:
    """Weighted fusion of multiple recommendation models.

    Strategy:
    1. Collect recommendations from each model (n*4 candidates each)
    2. Normalize and weight scores per model
    3. Apply model agreement boost (items in multiple models' lists get extra weight)
    4. Inject 10% exploration tracks (random catalog items with low scores)
    5. Rank by final weighted score
    """

    def __init__(self, models: list, weights: list[float] | None = None):
        self.models = models
        if weights is None:
            self.weights = [1.0 / len(models)] * len(models)
        else:
            total = sum(weights)
            self.weights = [w / total for w in weights]
        self._all_tracks = None  # Lazy-load all known tracks

    def _collect_all_tracks(self):
        """Collect all known track IDs from sub-models."""
        if self._all_tracks is not None:
            return self._all_tracks
        all_tracks = set()
        for model in self.models:
            if hasattr(model, 'global_popularity'):
                all_tracks.update(model.global_popularity)
            if hasattr(model, 'track_popularity'):
                all_tracks.update(model.track_popularity.keys())
            if hasattr(model, 'all_tracks'):
                all_tracks.update(model.all_tracks)
        self._all_tracks = list(all_tracks)
        return self._all_tracks

    def recommend(self, user_id: int, n: int = 10,
                  recent_tracks: list | None = None,
                  exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        all_scores = defaultdict(float)
        model_agreement = defaultdict(int)  # count how many models recommend each item

        for model, weight in zip(self.models, self.weights):
            try:
                # Check if model supports recent_tracks and exclude_track_ids
                import inspect
                sig = inspect.signature(model.recommend)
                kwargs = {"n": n * 4}  # Expanded from n*2 to n*4
                if "recent_tracks" in sig.parameters:
                    kwargs["recent_tracks"] = recent_tracks
                if "exclude_track_ids" in sig.parameters:
                    kwargs["exclude_track_ids"] = exclude_track_ids
                recs = model.recommend(user_id, **kwargs)
            except Exception:
                continue

            if not recs:
                continue

            # Track which items this model recommended (for agreement counting)
            for item, _ in recs:
                model_agreement[item] += 1

            scores = [s for _, s in recs]
            # Always use rank-based normalization for robust fusion
            # This ensures each model contributes equally regardless of score scale
            n_recs = len(scores)
            scores = [round(1.0 - i / max(n_recs - 1, 1), 4) for i in range(n_recs)]

            for (item, _), norm_score in zip(recs, scores):
                all_scores[item] += weight * norm_score

        # Apply model agreement boost
        # Items recommended by multiple models get extra weight
        for item in list(all_scores.keys()):
            agreement_count = model_agreement.get(item, 0)
            if agreement_count > 1:
                # Boost: 10% extra per additional model agreement (reduced from 20%)
                boost = 1.0 + 0.1 * (agreement_count - 1)
                all_scores[item] *= boost

        # Exploration: inject 10% random tracks with low scores
        all_tracks = self._collect_all_tracks()
        if all_tracks:
            listened = set()
            if exclude_track_ids:
                listened = exclude_track_ids.copy()
            # Add tracks already recommended to avoid duplicates
            already_recommended = set(all_scores.keys())
            candidates = [t for t in all_tracks if t not in listened and t not in already_recommended]
            n_explore = max(1, n // 10)  # 10% exploration (reduced from 20%)
            if candidates:
                explore_tracks = random.sample(candidates, min(n_explore, len(candidates)))
                # Give exploration tracks very low scores (0.01-0.05 range)
                for track in explore_tracks:
                    all_scores[track] = random.uniform(0.01, 0.05)

        ranked = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:n]
