"""
Word2Vec-based song embedding recommendation model.

Treats listening sequences as "sentences" and songs as "words",
learning dense vector representations via Gensim Word2Vec.
"""

import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from gensim.models import Word2Vec


class Song2VecRecommender:
    """Learns song embeddings from listening sessions using Word2Vec."""

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

        for _, row in df.iterrows():
            self.user_history[row["user_id_idx"]].add(row["track_id_idx"])

        sessions = self._build_sessions(df)
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

    def recommend(self, user_id: int, n: int = 10) -> list[tuple[int, float]]:
        if self.model is None:
            return [(t, 0.0) for t in self.global_popularity[:n]]

        listened = self.user_history.get(user_id, set())
        valid_vectors = [
            self.track_vectors[t] for t in listened if t in self.track_vectors
        ]

        if not valid_vectors:
            # Cold start: global popular
            return [(t, 0.0) for t in self.global_popularity[:n]]

        user_profile = np.mean(valid_vectors, axis=0)
        user_profile = user_profile / (np.linalg.norm(user_profile) + 1e-8)

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
