"""
基于序列的推荐模型。

不依赖用户的长期画像，而是根据当前会话中最近播放的歌曲
来预测下一首想听的歌——类似"歌单续播"场景。

使用回退 N-gram 策略：k=3 → k=2 → k=1 → 全局热门
"""

import numpy as np
import pandas as pd
from collections import defaultdict, Counter


class SequenceRecommender:
    """基于会话的序列推荐（回退 N-gram）。

    改进：
    1. 构建多阶转移矩阵（k=1, 2, 3）
    2. 推荐时插值融合多个上下文长度的结果
    3. Laplace 平滑处理零计数
    4. 回退到全局热门作为兜底
    """

    def __init__(self, k: int = 3, session_gap_minutes: int = 60):
        self.k = k  # 最大上下文窗口大小
        self.session_gap_minutes = session_gap_minutes
        self.transition_matrices = {}  # k -> {(prev_k_tracks): {next_track: count}}
        self.user_history = defaultdict(set)
        self.track_popularity = Counter()
        self.all_tracks = set()  # 所有出现过的歌曲

    def _build_sessions(self, df: pd.DataFrame) -> list[list[int]]:
        """按时间间隔切分会话。"""
        df = df.sort_values(["user_id_idx", "timestamp"])
        sessions = []

        for _, group in df.groupby("user_id_idx"):
            group = group.sort_values("timestamp")
            session = [group.iloc[0]["track_id_idx"]]
            for i in range(1, len(group)):
                diff = (group.iloc[i]["timestamp"] -
                        group.iloc[i - 1]["timestamp"]).total_seconds() / 60
                if diff > self.session_gap_minutes:
                    if len(session) >= 2:
                        sessions.append(session)
                    session = []
                session.append(group.iloc[i]["track_id_idx"])
            if len(session) >= 2:
                sessions.append(session)

        return sessions

    def fit(self, df: pd.DataFrame):
        """构建多阶歌曲转移概率矩阵（k=1, 2, 3）。"""
        for _, row in df.iterrows():
            self.user_history[row["user_id_idx"]].add(row["track_id_idx"])
            self.track_popularity[row["track_id_idx"]] += 1

        self.all_tracks = set(self.track_popularity.keys())
        sessions = self._build_sessions(df)
        print(f"  构建了 {len(sessions)} 个会话用于序列建模")

        # 构建多个 k 值的转移矩阵
        for k in range(1, self.k + 1):
            matrix = defaultdict(Counter)
            for session in sessions:
                for i in range(k, len(session)):
                    context = tuple(session[i - k:i])
                    next_track = session[i]
                    matrix[context][next_track] += 1
            self.transition_matrices[k] = matrix
            print(f"    k={k}: {len(matrix)} 个上下文")

    def recommend(
        self, user_id: int, recent_tracks: list[int] | None = None, n: int = 10,
        exclude_track_ids: set[int] | None = None
    ) -> list[tuple[int, float]]:
        """根据最近 k 首歌推荐下一首（回退 N-gram + Laplace 平滑）。

        Args:
            user_id: 用户 ID
            recent_tracks: 最近听过的歌曲列表（最近的在最后）
            n: 推荐数量
            exclude_track_ids: 评估时从"已听过"中排除的曲目（留一法holdout）
        """
        listened = self.user_history.get(user_id, set())
        if exclude_track_ids:
            listened = listened - exclude_track_ids

        scores = defaultdict(float)
        epsilon = 0.1  # Laplace 平滑参数
        vocab_size = len(self.all_tracks)

        if recent_tracks:
            # 不同上下文长度的权重（长上下文更可靠，权重更高）
            weights = {3: 0.5, 2: 0.3, 1: 0.2}

            for k in range(self.k, 0, -1):
                if len(recent_tracks) < k:
                    continue

                context = tuple(recent_tracks[-k:])
                matrix = self.transition_matrices.get(k, {})
                candidates = matrix.get(context, Counter())

                if candidates:
                    # Laplace 平滑：P(track) = (count + ε) / (total + ε * |V|)
                    total = sum(candidates.values()) + epsilon * vocab_size
                    weight = weights.get(k, 0.1)

                    for track, count in candidates.items():
                        if track not in listened:
                            prob = (count + epsilon) / total
                            scores[track] += weight * prob

        # 回退：全局热门（小权重兜底）
        if not scores or len(scores) < n:
            pop_weight = 0.05
            total_pop = sum(self.track_popularity.values()) + epsilon * vocab_size
            for track, count in self.track_popularity.most_common():
                if track not in listened and track not in scores:
                    prob = (count + epsilon) / total_pop
                    scores[track] += pop_weight * prob
                if len(scores) >= n * 2:
                    break

        # 按分数排序返回 top-n
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(track, score) for track, score in ranked[:n]]

    def save(self, path):
        """Save model to disk."""
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        """Load model from disk."""
        import joblib
        return joblib.load(path)
