"""
基于序列的推荐模型。

不依赖用户的长期画像，而是根据当前会话中最近播放的歌曲
来预测下一首想听的歌——类似"歌单续播"场景。
"""

import numpy as np
import pandas as pd
from collections import defaultdict, Counter


class SequenceRecommender:
    """基于会话的序列推荐。

    思路：
    1. 统计歌曲之间的转移概率（Markov Chain）
    2. 给定当前会话的最后 k 首歌，推荐最可能的下一首
    """

    def __init__(self, k: int = 3, session_gap_minutes: int = 60):
        self.k = k  # 上下文窗口大小
        self.session_gap_minutes = session_gap_minutes
        self.transition_matrix = defaultdict(Counter)  # (prev_k_tracks) -> {next_track: count}
        self.user_history = defaultdict(set)
        self.track_popularity = Counter()

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
        """构建歌曲转移概率矩阵。"""
        for _, row in df.iterrows():
            self.user_history[row["user_id_idx"]].add(row["track_id_idx"])
            self.track_popularity[row["track_id_idx"]] += 1

        sessions = self._build_sessions(df)
        print(f"  构建了 {len(sessions)} 个会话用于序列建模")

        for session in sessions:
            for i in range(self.k, len(session)):
                context = tuple(session[i - self.k:i])
                next_track = session[i]
                self.transition_matrix[context][next_track] += 1

    def recommend(
        self, user_id: int, recent_tracks: list[int] | None = None, n: int = 10
    ) -> list[tuple[int, float]]:
        """根据最近 k 首歌推荐下一首。

        Args:
            user_id: 用户 ID
            recent_tracks: 最近听过的 k 首歌列表（最近的在最后）
            n: 推荐数量
        """
        listened = self.user_history.get(user_id, set())

        if recent_tracks and len(recent_tracks) >= self.k:
            context = tuple(recent_tracks[-self.k:])
            candidates = self.transition_matrix.get(context, Counter())

            if candidates:
                total = sum(candidates.values())
                scored = [(t, c / total) for t, c in
                          candidates.most_common(n + len(listened))]
                # 过滤已听过的
                scored = [(t, s) for t, s in scored if t not in listened]
                return scored[:n]

        # 回退：推荐全局最热门的歌曲
        popular = self.track_popularity.most_common(n + len(listened))
        popular = [(t, c) for t, c in popular if t not in listened]
        return popular[:n]
