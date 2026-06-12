"""
Recommendation system evaluation module.

Metrics:
- Precision@K / Recall@K
- HitRate@K
- NDCG@K
- Coverage
"""

import numpy as np
import pandas as pd
from collections import defaultdict


def _get_user_ground_truth(df: pd.DataFrame) -> dict:
    """Extract per-user ground truth track sets from test data."""
    gt = defaultdict(set)
    for _, row in df.iterrows():
        gt[row["user_id_idx"]].add(row["track_id_idx"])
    return gt


def precision_recall_at_k(
    recommendations: dict[int, list[int]], ground_truth: dict[int, set[int]], k: int = 10
) -> tuple[float, float]:
    precisions, recalls = [], []
    for user_id, recs in recommendations.items():
        recs_k = recs[:k]
        hits = ground_truth.get(user_id, set()) & set(recs_k)
        precisions.append(len(hits) / k if k > 0 else 0)
        total_gt = len(ground_truth.get(user_id, set()))
        recalls.append(len(hits) / total_gt if total_gt > 0 else 0)
    return np.mean(precisions) if precisions else 0.0, np.mean(recalls) if recalls else 0.0


def hit_rate_at_k(
    recommendations: dict[int, list[int]], ground_truth: dict[int, set[int]], k: int = 10
) -> float:
    hits = 0
    for user_id, recs in recommendations.items():
        if set(recs[:k]) & ground_truth.get(user_id, set()):
            hits += 1
    return hits / len(recommendations) if recommendations else 0.0


def ndcg_at_k(
    recommendations: dict[int, list[int]], ground_truth: dict[int, set[int]], k: int = 10
) -> float:
    ndcgs = []
    for user_id, recs in recommendations.items():
        gt = ground_truth.get(user_id, set())
        dcg = sum(1.0 / np.log2(i + 2) for i, item in enumerate(recs[:k]) if item in gt)
        n_hits = min(len(gt), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(n_hits))
        ndcgs.append(dcg / idcg if idcg > 0 else 0.0)
    return np.mean(ndcgs) if ndcgs else 0.0


def coverage(recommendations: dict[int, list[int]], total_items: int) -> float:
    all_recs = set()
    for recs in recommendations.values():
        all_recs.update(recs)
    return min(len(all_recs) / total_items, 1.0) if total_items > 0 else 0.0


def evaluate_recommender(
    model,
    test_df: pd.DataFrame,
    all_users: list[int],
    k: int = 10,
    verbose: bool = True,
) -> dict:
    """Comprehensive evaluation of a recommendation model.

    Only evaluates on users for which the model actually produces recommendations.
    """
    ground_truth = _get_user_ground_truth(test_df)
    total_items = test_df["track_id_idx"].nunique()

    recommendations = {}
    for user_id in all_users:
        try:
            recs = model.recommend(user_id, n=k)
            if recs and isinstance(recs[0], tuple):
                recs = [r[0] for r in recs]
            recommendations[user_id] = recs
        except Exception:
            recommendations[user_id] = []

    # Filter to users with both recommendations AND ground truth
    valid_recs = {
        u: r for u, r in recommendations.items()
        if r and u in ground_truth and ground_truth[u]
    }

    n_evaluated = len(valid_recs)

    if n_evaluated == 0:
        if verbose:
            print(f"  No valid users to evaluate (model could not recommend for any test user)")
        return {
            f"Precision@{k}": 0.0,
            f"Recall@{k}": 0.0,
            f"HitRate@{k}": 0.0,
            f"NDCG@{k}": 0.0,
            "Coverage": 0.0,
        }

    prec, rec = precision_recall_at_k(valid_recs, ground_truth, k)
    hr = hit_rate_at_k(valid_recs, ground_truth, k)
    ndcg = ndcg_at_k(valid_recs, ground_truth, k)
    cov = coverage(valid_recs, total_items)

    metrics = {
        f"Precision@{k}": round(prec, 4),
        f"Recall@{k}": round(rec, 4),
        f"HitRate@{k}": round(hr, 4),
        f"NDCG@{k}": round(ndcg, 4),
        "Coverage": round(cov, 4),
    }

    if verbose:
        print(f"  Evaluated on {n_evaluated} users:")
        for name, value in metrics.items():
            print(f"    {name}: {value}")

    return metrics
