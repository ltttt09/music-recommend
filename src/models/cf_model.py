"""
Collaborative Filtering recommendation models.

Includes:
- UserCF: User-based collaborative filtering
- ItemCF: Item-based collaborative filtering
- SVDRecommender: Pure NumPy SVD matrix factorization
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter


class UserCF:
    """User-based collaborative filtering."""

    def __init__(self, k: int = 50, min_interactions: int = 5):
        self.k = k
        self.min_interactions = min_interactions
        self.user_item_matrix = None
        self.user_similarity = None
        self.user_idx_map = {}
        self.item_idx_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.global_popularity = []

    def fit(self, df: pd.DataFrame):
        user_counts = df.groupby("user_id_idx").size()
        valid_users = user_counts[user_counts >= self.min_interactions].index
        df = df[df["user_id_idx"].isin(valid_users)]

        users = df["user_id_idx"].unique()
        items = df["track_id_idx"].unique()

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        rows = [self.user_idx_map[u] for u in df["user_id_idx"]]
        cols = [self.item_idx_map[t] for t in df["track_id_idx"]]
        data = df.get("listen_count", [1] * len(df)).values

        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(users), len(items)),
        )
        self.user_similarity = cosine_similarity(self.user_item_matrix)
        np.fill_diagonal(self.user_similarity, 0)

        # Global popularity fallback
        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]

    def recommend(self, user_id: int, n: int = 10) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            # Cold start: return global popular tracks
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        listened = set(self.user_item_matrix[u_idx].indices)

        sim_scores = self.user_similarity[u_idx]
        top_k_users = np.argsort(sim_scores)[::-1][:self.k]

        scores = defaultdict(float)
        sim_sum = defaultdict(float)
        for v_idx in top_k_users:
            if sim_scores[v_idx] <= 0:
                continue
            v_items = self.user_item_matrix[v_idx].toarray().flatten()
            for item_idx, rating in enumerate(v_items):
                if item_idx in listened or rating == 0:
                    continue
                scores[item_idx] += sim_scores[v_idx] * rating
                sim_sum[item_idx] += sim_scores[v_idx]

        for item_idx in scores:
            if sim_sum[item_idx] > 0:
                scores[item_idx] /= sim_sum[item_idx]

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        if not ranked:
            ranked = [(self.item_idx_map[t], 0.0) for t in self.global_popularity[:n]
                      if t in self.item_idx_map]
        return [(self.reverse_item_map[idx], score) for idx, score in ranked[:n]]


class ItemCF:
    """Item-based collaborative filtering."""

    def __init__(self, k: int = 50, min_interactions: int = 5):
        self.k = k
        self.min_interactions = min_interactions
        self.item_similarity = None
        self.user_idx_map = {}
        self.item_idx_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.item_user_matrix = None
        self.global_popularity = []

    def fit(self, df: pd.DataFrame):
        user_counts = df.groupby("user_id_idx").size()
        valid_users = user_counts[user_counts >= self.min_interactions].index
        df = df[df["user_id_idx"].isin(valid_users)]

        users = df["user_id_idx"].unique()
        items = df["track_id_idx"].unique()

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        rows = [self.item_idx_map[t] for t in df["track_id_idx"]]
        cols = [self.user_idx_map[u] for u in df["user_id_idx"]]
        data = df.get("listen_count", [1] * len(df)).values

        self.item_user_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(items), len(users)),
        )
        self.item_similarity = cosine_similarity(self.item_user_matrix)
        np.fill_diagonal(self.item_similarity, 0)

        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]

    def recommend(self, user_id: int, n: int = 10) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        listened = set(np.where(
            self.item_user_matrix[:, u_idx].toarray().flatten() > 0
        )[0])

        scores = defaultdict(float)
        for item_idx in listened:
            sim_scores = self.item_similarity[item_idx]
            top_k = np.argsort(sim_scores)[::-1][:self.k + len(listened)]
            for sim_idx in top_k:
                if sim_idx in listened:
                    continue
                scores[sim_idx] += sim_scores[sim_idx]

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        if not ranked:
            ranked = [(self.item_idx_map[t], 0.0) for t in self.global_popularity[:n]
                      if t in self.item_idx_map]
        return [(self.reverse_item_map[idx], score) for idx, score in ranked[:n]]


class SVDRecommender:
    """Pure NumPy truncated SVD matrix factorization."""

    def __init__(self, n_factors: int = 50):
        self.n_factors = n_factors
        self.U = None
        self.Sigma = None
        self.Vt = None
        self.user_idx_map = {}
        self.item_idx_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.global_mean = 0.0
        self.global_popularity = []

    def fit(self, df: pd.DataFrame):
        users = df["user_id_idx"].unique()
        items = df["track_id_idx"].unique()

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        n_users = len(users)
        n_items = len(items)

        ratings = np.zeros((n_users, n_items))
        for _, row in df.iterrows():
            u = self.user_idx_map[row["user_id_idx"]]
            t = self.item_idx_map[row["track_id_idx"]]
            ratings[u, t] = np.clip(row["listen_count"], 1, 5)

        self.global_mean = ratings[ratings > 0].mean()
        ratings_centered = ratings.copy()
        ratings_centered[ratings > 0] -= self.global_mean

        U_full, sigma_full, Vt_full = np.linalg.svd(ratings_centered, full_matrices=False)
        k = min(self.n_factors, len(sigma_full))
        self.U = U_full[:, :k]
        self.Sigma = np.diag(sigma_full[:k])
        self.Vt = Vt_full[:k, :]

        # Global popularity
        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]

    def recommend(self, user_id: int, n: int = 10) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        user_vec = self.U[u_idx]
        predicted = user_vec @ self.Sigma @ self.Vt + self.global_mean

        scores = [(self.reverse_item_map.get(t_idx, t_idx), predicted[t_idx])
                  for t_idx in range(len(predicted))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]
