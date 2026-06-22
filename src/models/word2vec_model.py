"""
Word2Vec-based song embedding recommendation model.

Treats listening sequences as "sentences" and songs as "words",
learning dense vector representations via Gensim Word2Vec.

Improvement: time-weighted user profile (recent plays weighted higher).
"""

import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from gensim.models import Word2Vec


class Song2VecRecommender:
    """Learns song embeddings from listening sessions using Word2Vec.

    Uses time-weighted user profile: recent plays get higher weight
    via exponential decay (lambda=0.02 per day).
    """

    def __init__(self, vector_size: int = 100, window: int = 5,
                 min_count: int = 3, epochs: int = 20,
                 session_gap_minutes: int = 60):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.epochs = epochs
        self.session_gap_minutes = session_gap_minutes
        self.model = None
        self.track_vectors = {}
        self.track_idx_to_id = {}
        self.track_id_to_idx = {}
        self.user_history = defaultdict(set)
        self.global_popularity = []
        self._user_track_times = {}  # user_id -> {track_id: last_timestamp}
        self._max_timestamp = None

    def _build_sessions(self, df: pd.DataFrame) -> list[list[str]]:
        df = df.sort_values(["user_id_idx", "timestamp"])
        sessions = []
        for user_id, group in df.groupby("user_id_idx"):
            group = group.sort_values("timestamp")
            session = [group.iloc[0]["track_id_idx"]]
            for i in range(1, len(group)):
                time_diff = (group.iloc[i]["timestamp"] -
                             group.iloc[i - 1]["timestamp"]).total_seconds() / 60
                if time_diff > self.session_gap_minutes:
                    if len(session) >= 2:
                        sessions.append([str(t) for t in session])
                    session = []
                session.append(group.iloc[i]["track_id_idx"])
            if len(session) >= 2:
                sessions.append([str(t) for t in session])
        return sessions

    def fit(self, df: pd.DataFrame):
        all_tracks = df["track_id_idx"].unique()
        self.track_id_to_idx = {t: str(t) for t in all_tracks}
        self.track_idx_to_id = {str(t): t for t in all_tracks}

        # Store last-played timestamp per (user, track) for time-weighted profile
        self._user_track_times = defaultdict(dict)
        df_ts = df.copy()
        df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"])
        self._max_timestamp = df_ts["timestamp"].max()

        for _, row in df_ts.iterrows():
            uid = row["user_id_idx"]
            tid = row["track_id_idx"]
            ts = row["timestamp"]
            self.user_history[uid].add(tid)
            # Keep the most recent timestamp for each (user, track)
            if tid not in self._user_track_times[uid] or ts > self._user_track_times[uid][tid]:
                self._user_track_times[uid][tid] = ts

        sessions = self._build_sessions(df_ts)
        print(f"  Built {len(sessions)} listening sessions")

        if len(sessions) < 10:
            print("  Warning: too few sessions, Word2Vec may underperform")

        self.model = Word2Vec(
            sentences=sessions,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=4,
            epochs=self.epochs,
            seed=42,
        )

        for track_str in self.model.wv.index_to_key:
            idx = int(track_str)
            self.track_vectors[idx] = self.model.wv[track_str]

        # Global popularity fallback
        popularity = Counter(df["track_id_idx"])
        self.global_popularity = [t for t, _ in popularity.most_common()]

    def _build_time_weighted_profile(self, user_id: int, listened: set) -> np.ndarray | None:
        """Build time-weighted user profile vector.

        Recent plays get exponentially higher weight:
        weight = exp(-0.02 * days_since_played)
        profile = Σ(weight_i * vec_i) / Σ(weight_i)
        """
        track_times = self._user_track_times.get(user_id, {})
        now = self._max_timestamp

        weighted_sum = None
        weight_total = 0.0

        for t in listened:
            if t not in self.track_vectors:
                continue
            vec = self.track_vectors[t]
            # Time decay weight
            if t in track_times and now is not None:
                days_ago = max((now - track_times[t]).days, 0)
                weight = np.exp(-0.02 * days_ago)
            else:
                weight = 0.01  # minimal weight for tracks without timestamp

            if weighted_sum is None:
                weighted_sum = weight * vec
            else:
                weighted_sum += weight * vec
            weight_total += weight

        if weighted_sum is None or weight_total < 1e-10:
            return None

        profile = weighted_sum / weight_total
        norm = np.linalg.norm(profile)
        if norm > 1e-8:
            profile = profile / norm
        return profile

    def recommend(self, user_id: int, n: int = 10,
                  exclude_track_ids: set[int] | None = None) -> list[tuple[int, float]]:
        if self.model is None:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        listened = self.user_history.get(user_id, set())
        if exclude_track_ids:
            listened = listened - exclude_track_ids

        # Build time-weighted user profile
        user_profile = self._build_time_weighted_profile(user_id, listened)

        if user_profile is None:
            # Cold start: global popular
            return [(t, 0.0) for t in self.global_popularity[:n]]

        scores = {}
        for track_idx, vec in self.track_vectors.items():
            if track_idx in listened:
                continue
            sim = np.dot(user_profile, vec) / (
                np.linalg.norm(user_profile) * np.linalg.norm(vec) + 1e-8
            )
            scores[track_idx] = sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        if not ranked:
            return [(t, 0.0) for t in self.global_popularity[:n]]
        return [(idx, score) for idx, score in ranked]

    def similar_tracks(self, track_id: int, n: int = 10) -> list[tuple[int, float]]:
        track_str = str(track_id)
        if track_str not in self.model.wv:
            return []
        results = self.model.wv.most_similar(track_str, topn=n)
        return [(int(t), s) for t, s in results]

    def save(self, path):
        """Save model to disk."""
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        """Load model from disk."""
        import joblib
        return joblib.load(path)
