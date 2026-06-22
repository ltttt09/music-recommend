"""
Collaborative Filtering recommendation models.

Includes:
- UserCF: User-based collaborative filtering (adjusted cosine + time decay)
- ItemCF: Item-based collaborative filtering (normalized scoring + time decay + shrinkage)
- SVDRecommender: ALS implicit feedback matrix factorization
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter


class UserCF:
    """User-based collaborative filtering with adjusted cosine similarity and time decay."""

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
        self._user_interactions = []  # for recommend() exclusion

    def fit(self, df: pd.DataFrame):
        # Time decay weighting
        df = df.copy()
        if "timestamp" in df.columns:
            now = pd.to_datetime(df["timestamp"]).max()
            df["days_ago"] = (now - pd.to_datetime(df["timestamp"])).dt.days.clip(lower=0)
            df["time_weight"] = np.exp(-0.01 * df["days_ago"])
        else:
            df["time_weight"] = 1.0

        # Filter users with enough interactions
        user_counts = df.groupby("user_id_idx").size()
        valid_users = user_counts[user_counts >= self.min_interactions].index
        df = df[df["user_id_idx"].isin(valid_users)]

        users = sorted(df["user_id_idx"].unique())
        items = sorted(df["track_id_idx"].unique())

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        # Aggregate time-weighted interactions per (user, track)
        agg = df.groupby(["user_id_idx", "track_id_idx"]).agg(
            weighted_count=("time_weight", "sum"),
        ).reset_index()

        n_users = len(users)
        n_items = len(items)

        # Build dense matrix for adjusted cosine
        dense = np.zeros((n_users, n_items), dtype=float)
        for _, row in agg.iterrows():
            u = self.user_idx_map[row["user_id_idx"]]
            t = self.item_idx_map[row["track_id_idx"]]
            dense[u, t] = row["weighted_count"]

        # Also build sparse for efficient lookup in recommend()
        rows_list, cols_list, data_list = [], [], []
        for _, row in agg.iterrows():
            u = self.user_idx_map[row["user_id_idx"]]
            t = self.item_idx_map[row["track_id_idx"]]
            rows_list.append(u)
            cols_list.append(t)
            data_list.append(row["weighted_count"])
        self.user_item_matrix = csr_matrix(
            (data_list, (rows_list, cols_list)), shape=(n_users, n_items),
        )

        # Store per-user interactions for recommend()
        self._user_interactions = [set() for _ in range(n_users)]
        for u, t in zip(rows_list, cols_list):
            self._user_interactions[u].add(t)

        # Adjusted cosine similarity: subtract user mean, compute over co-rated items
        user_means = np.zeros(n_users)
        for u in range(n_users):
            nz = dense[u] != 0
            if nz.any():
                user_means[u] = dense[u, nz].mean()

        sim_matrix = np.zeros((n_users, n_users))
        for u in range(n_users):
            u_nz = dense[u] != 0
            if not u_nz.any():
                continue
            for v in range(u + 1, n_users):
                v_nz = dense[v] != 0
                common = u_nz & v_nz
                if common.sum() < 2:
                    continue
                u_adj = dense[u, common] - user_means[u]
                v_adj = dense[v, common] - user_means[v]
                denom = np.linalg.norm(u_adj) * np.linalg.norm(v_adj)
                if denom > 1e-10:
                    sim = np.dot(u_adj, v_adj) / denom
                    sim_matrix[u, v] = sim
                    sim_matrix[v, u] = sim

        self.user_similarity = sim_matrix

        # Global popularity fallback
        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]
        # Store item popularity counts for popularity penalty in recommend()
        self._item_popularity = {}
        for t_idx in range(n_items):
            orig_tid = self.reverse_item_map.get(t_idx)
            self._item_popularity[t_idx] = popularity.get(orig_tid, 0)

    def recommend(self, user_id: int, n: int = 10, exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        listened = self._user_interactions[u_idx].copy()
        if exclude_track_ids:
            for tid in exclude_track_ids:
                if tid in self.item_idx_map:
                    listened.discard(self.item_idx_map[tid])

        sim_scores = self.user_similarity[u_idx]
        top_k_users = np.argsort(sim_scores)[::-1][:self.k]

        scores = defaultdict(float)
        sim_sum = defaultdict(float)
        for v_idx in top_k_users:
            if sim_scores[v_idx] <= 0:
                continue
            v_items = self.user_item_matrix[v_idx].toarray().flatten()
            for item_idx in range(len(v_items)):
                if item_idx in listened or v_items[item_idx] == 0:
                    continue
                scores[item_idx] += sim_scores[v_idx] * v_items[item_idx]
                sim_sum[item_idx] += abs(sim_scores[v_idx])

        for item_idx in scores:
            if sim_sum[item_idx] > 0:
                scores[item_idx] /= sim_sum[item_idx]

        # Popularity penalty: reduce scores for very popular items
        # Use log(1 + popularity) to avoid completely removing popular items
        import math
        for item_idx in list(scores.keys()):
            pop = self._item_popularity.get(item_idx, 0)
            if pop > 0:
                penalty = 1.0 / (1.0 + math.log(1 + pop))
                scores[item_idx] *= penalty

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        if not ranked:
            ranked = [(self.item_idx_map[t], 0.0) for t in self.global_popularity[:n]
                      if t in self.item_idx_map]
        return [(self.reverse_item_map[idx], score) for idx, score in ranked[:n]]

    def save(self, path):
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        import joblib
        return joblib.load(path)


class ItemCF:
    """Item-based collaborative filtering with normalized scoring, time decay, and shrinkage."""

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
        self._user_items = {}  # user_idx -> set of item_idx

    def fit(self, df: pd.DataFrame):
        # Time decay weighting
        df = df.copy()
        if "timestamp" in df.columns:
            now = pd.to_datetime(df["timestamp"]).max()
            df["days_ago"] = (now - pd.to_datetime(df["timestamp"])).dt.days.clip(lower=0)
            df["time_weight"] = np.exp(-0.01 * df["days_ago"])
        else:
            df["time_weight"] = 1.0

        user_counts = df.groupby("user_id_idx").size()
        valid_users = user_counts[user_counts >= self.min_interactions].index
        df = df[df["user_id_idx"].isin(valid_users)]

        users = sorted(df["user_id_idx"].unique())
        items = sorted(df["track_id_idx"].unique())

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        # Aggregate time-weighted interactions
        agg = df.groupby(["user_id_idx", "track_id_idx"]).agg(
            weighted_count=("time_weight", "sum"),
        ).reset_index()

        n_users = len(users)
        n_items = len(items)

        # Build item-user matrix (item x user)
        rows_list, cols_list, data_list = [], [], []
        self._user_items = defaultdict(set)
        for _, row in agg.iterrows():
            u = self.user_idx_map[row["user_id_idx"]]
            t = self.item_idx_map[row["track_id_idx"]]
            rows_list.append(t)
            cols_list.append(u)
            data_list.append(row["weighted_count"])
            self._user_items[u].add(t)

        self.item_user_matrix = csr_matrix(
            (data_list, (rows_list, cols_list)), shape=(n_items, n_users),
        )
        self.item_similarity = cosine_similarity(self.item_user_matrix)
        np.fill_diagonal(self.item_similarity, 0)

        # Precompute co-user counts for shrinkage
        # n_common[i, j] = number of users who interacted with both item i and item j
        binary = (self.item_user_matrix > 0).astype(float)
        self._co_user_counts = (binary @ binary.T).toarray()

        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]
        # Store item popularity counts for popularity penalty in recommend()
        self._item_popularity = {}
        for t_idx in range(n_items):
            orig_tid = self.reverse_item_map.get(t_idx)
            self._item_popularity[t_idx] = popularity.get(orig_tid, 0)

    def recommend(self, user_id: int, n: int = 10, exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        listened = self._user_items.get(u_idx, set()).copy()
        if exclude_track_ids:
            for tid in exclude_track_ids:
                if tid in self.item_idx_map:
                    listened.discard(self.item_idx_map[tid])

        scores = defaultdict(float)
        sim_sums = defaultdict(float)
        for item_idx in listened:
            sim_scores = self.item_similarity[item_idx]
            top_k = np.argsort(sim_scores)[::-1][:self.k + len(listened)]
            for sim_idx in top_k:
                if sim_idx in listened:
                    continue
                raw_sim = sim_scores[sim_idx]
                if raw_sim <= 0:
                    continue
                # Shrinkage: reduce similarity for item pairs with few co-users
                n_common = self._co_user_counts[item_idx, sim_idx]
                shrunk_sim = raw_sim * n_common / (n_common + 10)
                scores[sim_idx] += shrunk_sim * self.item_user_matrix[item_idx, u_idx]
                sim_sums[sim_idx] += abs(shrunk_sim)

        # Normalize by sum of similarities
        for item_idx in scores:
            if sim_sums[item_idx] > 0:
                scores[item_idx] /= sim_sums[item_idx]

        # Popularity penalty: reduce scores for very popular items
        # Use log(1 + popularity) to avoid completely removing popular items
        import math
        for item_idx in list(scores.keys()):
            pop = self._item_popularity.get(item_idx, 0)
            if pop > 0:
                penalty = 1.0 / (1.0 + math.log(1 + pop))
                scores[item_idx] *= penalty

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        if not ranked:
            ranked = [(self.item_idx_map[t], 0.0) for t in self.global_popularity[:n]
                      if t in self.item_idx_map]
        return [(self.reverse_item_map[idx], score) for idx, score in ranked[:n]]

    def save(self, path):
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        import joblib
        return joblib.load(path)


class SVDRecommender:
    """ALS implicit feedback matrix factorization (Hu, Koren, Volinsky 2008)."""

    def __init__(self, n_factors: int = 50, alpha: float = 40.0,
                 regularization: float = 0.1, iterations: int = 20):
        self.n_factors = n_factors
        self.alpha = alpha
        self.regularization = regularization
        self.iterations = iterations
        self.U = None  # user factors (n_users x n_factors)
        self.V = None  # item factors (n_items x n_factors)
        self.user_idx_map = {}
        self.item_idx_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.global_popularity = []
        self._user_interactions = []  # list of sets: items each user interacted with

    def fit(self, df: pd.DataFrame):
        users = sorted(df["user_id_idx"].unique())
        items = sorted(df["track_id_idx"].unique())

        self.user_idx_map = {u: i for i, u in enumerate(users)}
        self.item_idx_map = {t: i for i, t in enumerate(items)}
        self.reverse_user_map = {v: k for k, v in self.user_idx_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_idx_map.items()}

        n_users = len(users)
        n_items = len(items)

        # Aggregate interactions: listen_count per (user, track)
        agg = df.groupby(["user_id_idx", "track_id_idx"]).agg(
            listen_count=("listen_count", "first"),
        ).reset_index()

        # Build interaction lists for ALS
        user_interactions = [[] for _ in range(n_users)]  # [(item_internal_idx, confidence)]
        item_interactions = [[] for _ in range(n_items)]  # [(user_internal_idx, confidence)]

        self._user_interactions = [set() for _ in range(n_users)]

        for _, row in agg.iterrows():
            u = self.user_idx_map[row["user_id_idx"]]
            i = self.item_idx_map[row["track_id_idx"]]
            count = max(row["listen_count"], 1)
            confidence = 1.0 + self.alpha * count
            user_interactions[u].append((i, confidence))
            item_interactions[i].append((u, confidence))
            self._user_interactions[u].add(i)

        # Initialize factors
        np.random.seed(42)
        scale = 0.01
        self.U = np.random.normal(0, scale, (n_users, self.n_factors))
        self.V = np.random.normal(0, scale, (n_items, self.n_factors))

        reg_I = self.regularization * np.eye(self.n_factors)

        # ALS iterations
        for _iteration in range(self.iterations):
            # Fix V, solve for U
            VtV = self.V.T @ self.V  # (n_factors x n_factors)
            for u in range(n_users):
                items_u = user_interactions[u]
                if not items_u:
                    continue
                A = VtV.copy() + reg_I
                b = np.zeros(self.n_factors)
                for i, c_ui in items_u:
                    v_i = self.V[i]
                    A += (c_ui - 1.0) * np.outer(v_i, v_i)
                    b += c_ui * v_i
                self.U[u] = np.linalg.solve(A, b)

            # Fix U, solve for V
            UtU = self.U.T @ self.U
            for i in range(n_items):
                users_i = item_interactions[i]
                if not users_i:
                    continue
                A = UtU.copy() + reg_I
                b = np.zeros(self.n_factors)
                for u, c_ui in users_i:
                    u_vec = self.U[u]
                    A += (c_ui - 1.0) * np.outer(u_vec, u_vec)
                    b += c_ui * u_vec
                self.V[i] = np.linalg.solve(A, b)

        # Global popularity fallback
        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]
        # Store item popularity counts for popularity penalty in recommend()
        self._item_popularity = np.zeros(n_items)
        for t_idx in range(n_items):
            orig_tid = self.reverse_item_map.get(t_idx)
            self._item_popularity[t_idx] = popularity.get(orig_tid, 0)

    def recommend(self, user_id: int, n: int = 10, exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        if user_id not in self.user_idx_map:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        u_idx = self.user_idx_map[user_id]
        user_vec = self.U[u_idx]

        # Score all items: score = u · v
        scores = self.V @ user_vec

        # Popularity penalty: reduce scores for very popular items
        import math
        for i in range(len(scores)):
            pop = self._item_popularity[i]
            if pop > 0:
                penalty = 1.0 / (1.0 + math.log(1 + pop))
                scores[i] *= penalty

        # Exclude items the user has interacted with
        excluded = self._user_interactions[u_idx].copy()
        if exclude_track_ids:
            for tid in exclude_track_ids:
                if tid in self.item_idx_map:
                    excluded.add(self.item_idx_map[tid])

        candidates = [(self.reverse_item_map[i], float(scores[i]))
                      for i in range(len(scores)) if i not in excluded]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:n]

    def save(self, path):
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        import joblib
        return joblib.load(path)
