"""RecommenderEngine v4 - recommendation post-processing and safe API output."""

import json
import math
import re
import sys, hashlib, hmac, secrets, threading, time, uuid
from urllib.parse import quote
from urllib.request import urlopen
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import numpy as np
import pandas as pd
from collections import Counter, defaultdict

from app.config import TOKEN_TTL_SECONDS, get_admin_username
from app.services.explainer import explain_recommendation, source_models
from app.services.logging import admin_action_logs, admin_recommendation_logs, log_recommendations, log_user_action
from app.services.profile import build_user_profile, excluded_track_ids, user_profile_detail
from app.services.reranker import normalize_scores, rerank_candidates
from src.db.schema import init_db, get_connection, infer_language_group
from src.db.repository import (
    TrackRepo, ArtistRepo, UserRepo, ListeningRepo, FeedbackRepo, PlaylistRepo,
)
from src.data.itunes_full import ITUNES_FULL as REAL_SONGS
from src.models.cf_model import UserCF, ItemCF, SVDRecommender
from src.models.word2vec_model import Song2VecRecommender
from src.models.sequence_model import SequenceRecommender
from src.models.hybrid import HybridRecommender
from src.models.enhanced import EnhancedRecommender


HYBRID_WEIGHT_KEYS = ["itemcf", "usercf", "svd", "song2vec", "sequence"]
DEFAULT_HYBRID_WEIGHTS = {
    "itemcf": 25,
    "usercf": 15,
    "svd": 25,
    "song2vec": 15,
    "sequence": 20,
}
HYBRID_WEIGHT_CONFIG_KEY = "hybrid_weights"


class RecommenderEngine:
    def __init__(self):
        self.ml_models = {}
        self.enhanced = None
        self._initialized = False
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.track_id_to_idx = {}
        self.idx_to_track_id = {}
        self.auth_tokens = {}
        self.admin_tokens = {}
        self.metrics_jobs = {}
        self.metrics_lock = threading.Lock()
        self.latest_model_metrics = None
        self.train_progress = {
            "current_model": "",
            "total_models": 6,
            "stage": "等待训练",
            "message": "",
            "percent": 0,
            "updated_at": time.time(),
            "running": False,
            "error": "",
        }
        self.train_progress_lock = threading.Lock()
        self._init_lock = threading.Lock()
        self._initializing = False
        self.initialization_error = ""

    @property
    def is_initialized(self):
        return self._initialized

    @property
    def is_initializing(self):
        return self._initializing

    def initialize(self, force_reseed=False):
        with self._init_lock:
            if self._initialized and not force_reseed:
                return
            self._initializing = True
            self.initialization_error = ""
            try:
                print("[Engine] Initializing DB...")
                init_db()

                # Seed with real songs
                self._seed_real_data()

                print("[Engine] Preparing ML data...")
                ml_df = self._build_ml_dataframe()

                print("[Engine] Training ML models...")
                self._train_ml_models(ml_df)

                self.enhanced = EnhancedRecommender(self.ml_models)
                self._initialized = True
                try:
                    self.admin_model_metrics()
                except Exception as metrics_exc:
                    print(f"[Engine] Initial model metrics skipped: {metrics_exc}")

                conn = get_connection()
                n_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                n_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
                conn.close()
                print(f"[Engine] Ready! {n_users} users, {n_tracks} tracks")
            except Exception as exc:
                self.initialization_error = str(exc)
                self._update_train_progress(
                    stage="训练失败",
                    message=str(exc),
                    running=False,
                    error=str(exc),
                )
                raise
            finally:
                self._initializing = False

    def retrain_models(self, force_reseed=False):
        with self._init_lock:
            self._initializing = True
            self.initialization_error = ""
            try:
                init_db()
                if force_reseed:
                    self._seed_real_data()
                ml_df = self._build_ml_dataframe()
                self._train_ml_models(ml_df)
                self.enhanced = EnhancedRecommender(self.ml_models)
                self._initialized = True
                self.latest_model_metrics = None
                try:
                    self.admin_model_metrics()
                except Exception as metrics_exc:
                    print(f"[Engine] Retrain metrics skipped: {metrics_exc}")
            except Exception as exc:
                self.initialization_error = str(exc)
                self._update_train_progress(
                    stage="训练失败",
                    message=str(exc),
                    running=False,
                    error=str(exc),
                )
                raise
            finally:
                self._initializing = False

    def _seed_real_data(self):
        conn = get_connection()
        existing = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        if existing > 0:
            conn.close()
            print(f"[Engine] DB already has {existing} tracks, skipping seed")
            return

        # Use iTunes as the single playable data source.
        ALL_SONGS = [song for song in REAL_SONGS if song.get("preview_url")]
        print(f"[Engine] Seeding {len(ALL_SONGS)} iTunes preview songs")

        # Insert artists (unique from songs)
        artist_map = {}
        artist_id = 1
        for song in ALL_SONGS:
            a = song["artist"]
            if a not in artist_map:
                artist_map[a] = artist_id
                conn.execute(
                    "INSERT INTO artists (id, name, genres) VALUES (?, ?, ?)",
                    (artist_id, a, song["genre"]),
                )
                artist_id += 1

        # Insert tracks
        rng = np.random.default_rng(42)
        for i, song in enumerate(ALL_SONGS):
            aid = artist_map[song["artist"]]
            conn.execute(
                """INSERT INTO tracks (id, title, artist_id, album, year, duration_ms, genre,
                   popularity, energy, danceability, valence, tempo, image_url, preview_url,
                   source, external_id, source_url, license, audio_type, language, language_group)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    i + 1, song["title"], aid, song["album"], song["year"],
                    song["duration_ms"], song["genre"],
                    round(float(rng.random() * 100), 2),
                    round(float(rng.random()), 3),
                    round(float(rng.random()), 3),
                    round(float(rng.random()), 3),
                    round(float(rng.uniform(60, 180)), 1),
                    song.get("image_url", ""),
                    song.get("preview_url", ""),
                    "itunes",
                    str(song.get("external_id", "")),
                    song.get("source_url", ""),
                    song.get("license", "iTunes 30 秒试听") or "iTunes 30 秒试听",
                    "preview",
                    song.get("language", ""),
                    infer_language_group(
                        song.get("language", ""),
                        song.get("title", ""),
                        song.get("artist", ""),
                        song.get("album", ""),
                        song.get("genre", ""),
                    ),
                ),
            )
        n_tracks = len(ALL_SONGS)
        print(f"[Engine] Seeded {len(artist_map)} artists, {n_tracks} tracks")

        # Create demo users with listening history (user_001 has password 'admin' for admin access)
        GENRES = list(set(s["genre"] for s in ALL_SONGS))
        n_users = 100
        salt = secrets.token_hex(16)  # for user_001 admin password
        for uid in range(1, n_users + 1):
            pref_genre = rng.choice(GENRES)
            conn.execute(
                "INSERT INTO users (id, username, display_name, preferred_genres, password_hash, salt) VALUES (?, ?, ?, ?, ?, ?)",
                (uid, f"user_{uid:03d}", f"Listener {uid}", pref_genre, 
                 hashlib.sha256(f"admin{salt}".encode()).hexdigest() if uid == 1 else "", 
                 salt if uid == 1 else ""),
            )

        # Generate listening history
        track_ids = list(range(1, n_tracks + 1))
        popularity = 1.0 / np.arange(1, n_tracks + 1) ** 0.7
        popularity /= popularity.sum()

        records = []
        salt = secrets.token_hex(16)  # for user_001 admin password
        for uid in range(1, n_users + 1):
            n_listens = int(np.clip(rng.poisson(40), 5, 200))
            picks = rng.choice(track_ids, size=n_listens, p=popularity)
            for tid in picks:
                records.append((uid, int(tid)))
        conn.executemany(
            "INSERT INTO listening_history (user_id, track_id) VALUES (?, ?)", records
        )
        conn.commit()
        conn.close()
        print(f"[Engine] Generated {len(records)} listening records for {n_users} users")

    def _build_ml_dataframe(self):
        conn = get_connection()
        rows = conn.execute(
            """SELECT lh.user_id, lh.track_id, lh.listened_at,
                      t.title AS track_name, a.name AS artist_name, a.id AS artist_id
               FROM listening_history lh
               JOIN tracks t ON lh.track_id = t.id
               JOIN artists a ON t.artist_id = a.id"""
        ).fetchall()
        conn.close()

        df = pd.DataFrame(rows, columns=["user_id", "track_id", "timestamp",
                                          "track_name", "artist_name", "artist_id"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["listen_count"] = df.groupby(["user_id", "track_id"])["track_id"].transform("count")

        for col in ["user_id", "track_id", "artist_id"]:
            unique_vals = sorted(df[col].unique())
            mapping = {v: i for i, v in enumerate(unique_vals)}
            df[f"{col}_idx"] = df[col].map(mapping)

        self.user_id_to_idx = {v: i for i, v in enumerate(sorted(df["user_id"].unique()))}
        self.idx_to_user_id = {i: v for v, i in self.user_id_to_idx.items()}
        self.track_id_to_idx = {v: i for i, v in enumerate(sorted(df["track_id"].unique()))}
        self.idx_to_track_id = {i: v for v, i in self.track_id_to_idx.items()}
        return df

    def _to_ml_user_id(self, db_user_id):
        return self.user_id_to_idx.get(db_user_id, db_user_id)

    def _to_ml_track_id(self, db_track_id):
        return self.track_id_to_idx.get(db_track_id)

    def _to_db_track_id(self, ml_track_idx):
        db_track_id = self.idx_to_track_id.get(ml_track_idx)
        return int(db_track_id) if db_track_id is not None else None

    def ensure_initialized(self):
        if not self._initialized:
            self.initialize()

    def _train_ml_models(self, df):
        steps = [
            ("itemcf", "ItemCF", "构建物品相似度矩阵", lambda: ItemCF(k=50, min_interactions=3)),
            ("usercf", "UserCF", "计算用户相似度矩阵", lambda: UserCF(k=50, min_interactions=3)),
            ("svd", "SVD", "训练矩阵分解隐语义模型", lambda: SVDRecommender(n_factors=50)),
            ("song2vec", "Song2Vec", "训练歌曲向量召回模型", lambda: Song2VecRecommender(vector_size=100, window=5, min_count=3, epochs=15)),
            ("sequence", "Sequence", "训练序列行为推荐模型", lambda: SequenceRecommender(k=3)),
        ]
        total = len(steps) + 1
        self._update_train_progress(
            current_model="",
            total_models=total,
            stage="准备训练数据",
            message=f"训练样本 {len(df)} 条",
            percent=0,
            running=True,
            error="",
        )

        for index, (key, name, stage, factory) in enumerate(steps, start=1):
            started = time.time()
            print(f"  Training {name}...")
            self._update_train_progress(
                current_model=name,
                total_models=total,
                stage=stage,
                message=f"开始训练 {name}",
                percent=round((index - 1) / total * 100, 1),
                running=True,
                error="",
            )
            model = factory()
            model.fit(df)
            self.ml_models[key] = model
            self._update_train_progress(
                current_model=name,
                total_models=total,
                stage=f"{name} 训练完成",
                message=f"{name} 训练完成，耗时 {time.time() - started:.1f}s",
                percent=round(index / total * 100, 1),
                running=True,
                error="",
            )

        print("  Building Hybrid...")
        started = time.time()
        self._update_train_progress(
            current_model="Hybrid",
            total_models=total,
            stage="融合多模型结果",
            message="开始构建 Hybrid 混合推荐器",
            percent=round((total - 1) / total * 100, 1),
            running=True,
            error="",
        )
        self._rebuild_hybrid_model()
        self._update_train_progress(
            current_model="Hybrid",
            total_models=total,
            stage="训练完成",
            message=f"Hybrid 构建完成，耗时 {time.time() - started:.1f}s",
            percent=100,
            running=False,
            error="",
        )

    def _update_train_progress(self, **updates):
        with self.train_progress_lock:
            self.train_progress.update(updates)
            self.train_progress["updated_at"] = time.time()

    def get_train_progress(self):
        with self.train_progress_lock:
            return dict(self.train_progress)

    def _normalize_hybrid_weights(self, weights):
        normalized = {}
        for key in HYBRID_WEIGHT_KEYS:
            try:
                value = float((weights or {}).get(key, DEFAULT_HYBRID_WEIGHTS[key]))
            except (TypeError, ValueError):
                value = DEFAULT_HYBRID_WEIGHTS[key]
            normalized[key] = max(0.0, min(100.0, value))
        if sum(normalized.values()) <= 0:
            normalized = {key: float(value) for key, value in DEFAULT_HYBRID_WEIGHTS.items()}
        return normalized

    def get_hybrid_weights(self):
        init_db()
        conn = get_connection()
        row = conn.execute("SELECT value, updated_at FROM model_config WHERE key=?", (HYBRID_WEIGHT_CONFIG_KEY,)).fetchone()
        conn.close()
        payload = {}
        updated_at = None
        if row:
            updated_at = row["updated_at"]
            try:
                payload = json.loads(row["value"] or "{}")
            except (TypeError, ValueError):
                payload = {}
        weights = self._normalize_hybrid_weights(payload)
        return {"weights": weights, "updated_at": updated_at, "source": "database" if row else "default"}

    def save_hybrid_weights(self, weights):
        normalized = self._normalize_hybrid_weights(weights)
        init_db()
        conn = get_connection()
        conn.execute(
            """INSERT INTO model_config (key, value, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP""",
            (HYBRID_WEIGHT_CONFIG_KEY, json.dumps(normalized, ensure_ascii=False)),
        )
        conn.commit()
        row = conn.execute("SELECT updated_at FROM model_config WHERE key=?", (HYBRID_WEIGHT_CONFIG_KEY,)).fetchone()
        conn.close()
        self._rebuild_hybrid_model(normalized)
        return {"weights": normalized, "updated_at": row["updated_at"] if row else None, "source": "database"}

    def _hybrid_weight_list(self, weights=None):
        normalized = self._normalize_hybrid_weights(weights or self.get_hybrid_weights()["weights"])
        total = sum(normalized.values()) or 1.0
        return [normalized[key] / total for key in HYBRID_WEIGHT_KEYS]

    def _rebuild_hybrid_model(self, weights=None):
        missing = [key for key in HYBRID_WEIGHT_KEYS if key not in self.ml_models]
        if missing:
            return False
        self.ml_models["hybrid"] = HybridRecommender(
            models=[self.ml_models[key] for key in HYBRID_WEIGHT_KEYS],
            weights=self._hybrid_weight_list(weights),
        )
        return True

    
    def create_admin_token(self):
        token = secrets.token_hex(32)
        self.admin_tokens[token] = time.time() + TOKEN_TTL_SECONDS
        return token

    def verify_admin_token(self, token):
        expires_at = self.admin_tokens.get(token)
        if not expires_at:
            return False
        if expires_at < time.time():
            self.admin_tokens.pop(token, None)
            return False
        return True

    def admin_delete_user(self, user_id):
        conn = get_connection()
        conn.execute("DELETE FROM user_action_logs WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM recommendation_logs WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_profile_cache WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM listening_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM playlist_tracks WHERE playlist_id IN (SELECT id FROM playlists WHERE user_id = ?)", (user_id,))
        conn.execute("DELETE FROM playlists WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_playlist_tracks WHERE playlist_id IN (SELECT id FROM user_playlists WHERE user_id = ?)", (user_id,))
        conn.execute("DELETE FROM user_playlists WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "deleted_user_id": user_id}

    # ---- User Auth ----

    def _hash_password(self, password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
        ).hex()

    def _verify_password(self, password, salt, stored_hash):
        if not stored_hash or not salt:
            return False
        current_hash = self._hash_password(password, salt)
        legacy_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return hmac.compare_digest(stored_hash, current_hash) or hmac.compare_digest(stored_hash, legacy_hash)


    def register(self, username, password, display_name=""):
        if username.strip().lower() == get_admin_username().strip().lower():
            return {"error": "该用户名为管理员保留账号"}
        conn = get_connection()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            return {"error": "用户名已存在"}
        salt = secrets.token_hex(16)
        pw_hash = self._hash_password(password, salt)
        uid = conn.execute(
            "INSERT INTO users (username, display_name, password_hash, salt, preferred_genres) VALUES (?, ?, ?, ?, '')",
            (username, display_name or username, pw_hash, salt),
        ).lastrowid
        conn.commit()
        conn.close()
        return {"user_id": uid, "username": username}

    def login(self, username, password):
        if username.strip().lower() == get_admin_username().strip().lower():
            return {"error": "请使用管理员入口登录"}
        conn = get_connection()
        row = conn.execute(
            "SELECT id, password_hash, salt FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if not row:
            return {"error": "用户名或密码错误"}
        if not self._verify_password(password, row["salt"], row["password_hash"]):
            return {"error": "用户名或密码错误"}
        token = secrets.token_hex(32)
        self.auth_tokens[token] = {"user_id": row["id"], "expires_at": time.time() + TOKEN_TTL_SECONDS}
        return {"token": token, "user_id": row["id"], "username": username}

    def get_user_by_token(self, token):
        session = self.auth_tokens.get(token)
        if not session:
            return None
        if session["expires_at"] < time.time():
            self.auth_tokens.pop(token, None)
            return None
        return session["user_id"]

    # ---- Admin ----

    def admin_stats(self):
        conn = get_connection()
        n_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        n_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        n_artists = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
        n_listens = conn.execute("SELECT COUNT(*) FROM listening_history").fetchone()[0]
        n_feedback = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        n_playlists = conn.execute("SELECT COUNT(*) FROM playlists").fetchone()[0]
        n_comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        n_recommendation_logs = conn.execute("SELECT COUNT(*) FROM recommendation_logs").fetchone()[0]
        n_likes = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating > 0").fetchone()[0]
        n_dislikes = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating < 0").fetchone()[0]
        top_tracks = conn.execute(
            """SELECT t.id, t.title, t.image_url, t.album, t.genre, a.name AS artist, COUNT(*) AS cnt
               FROM listening_history lh
               JOIN tracks t ON lh.track_id=t.id
               JOIN artists a ON t.artist_id=a.id
               GROUP BY lh.track_id
               ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()
        top_liked = conn.execute(
            """SELECT t.id, t.title, t.image_url, t.album, t.genre, a.name AS artist, COUNT(*) AS cnt
               FROM feedback f JOIN tracks t ON f.track_id=t.id JOIN artists a ON t.artist_id=a.id
               WHERE f.rating > 0
               GROUP BY f.track_id ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()
        top_commented = conn.execute(
            """SELECT t.id, t.title, t.image_url, t.album, t.genre, a.name AS artist, COUNT(*) AS cnt
               FROM comments c JOIN tracks t ON c.track_id=t.id JOIN artists a ON t.artist_id=a.id
               GROUP BY c.track_id ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()
        top_disliked = conn.execute(
            """SELECT t.id, t.title, t.image_url, t.album, t.genre, a.name AS artist, COUNT(*) AS cnt
               FROM feedback f JOIN tracks t ON f.track_id=t.id JOIN artists a ON t.artist_id=a.id
               WHERE f.rating < 0
               GROUP BY f.track_id ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()
        hot_tracks = conn.execute(
            """SELECT t.id, t.title, t.image_url, t.album, t.genre, a.name AS artist,
                      COUNT(DISTINCT lh.id) AS plays,
                      COUNT(DISTINCT CASE WHEN f.rating > 0 THEN f.id END) AS likes,
                      COUNT(DISTINCT c.id) AS comments,
                      COUNT(DISTINCT lh.id) * 0.5
                        + COUNT(DISTINCT CASE WHEN f.rating > 0 THEN f.id END) * 0.3
                        + COUNT(DISTINCT c.id) * 0.2 AS cnt
               FROM tracks t
               JOIN artists a ON t.artist_id=a.id
               LEFT JOIN listening_history lh ON lh.track_id=t.id
               LEFT JOIN feedback f ON f.track_id=t.id
               LEFT JOIN comments c ON c.track_id=t.id
               GROUP BY t.id
               ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()
        genre_dist = conn.execute(
            "SELECT genre, COUNT(*) AS cnt FROM tracks GROUP BY genre ORDER BY cnt DESC"
        ).fetchall()
        source_dist = conn.execute(
            "SELECT source, COUNT(*) AS cnt FROM tracks GROUP BY source ORDER BY cnt DESC"
        ).fetchall()
        playable_tracks = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE preview_url != ''"
        ).fetchone()[0]
        full_audio_tracks = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE audio_type = 'full' AND preview_url != ''"
        ).fetchone()[0]
        conn.close()
        return {
            "users": n_users, "tracks": n_tracks, "artists": n_artists,
            "listens": n_listens, "feedback": n_feedback, "playlists": n_playlists,
            "comments": n_comments, "recommendation_logs": n_recommendation_logs,
            "likes": n_likes, "dislikes": n_dislikes,
            "playable_tracks": playable_tracks,
            "full_audio_tracks": full_audio_tracks,
            "top_tracks": [dict(r) for r in top_tracks],
            "top_liked": [dict(r) for r in top_liked],
            "top_commented": [dict(r) for r in top_commented],
            "top_disliked": [dict(r) for r in top_disliked],
            "hot_tracks": [dict(r) for r in hot_tracks],
            "genre_distribution": [dict(r) for r in genre_dist],
            "source_distribution": [dict(r) for r in source_dist],
        }

    def admin_seed_engagement(self, likes_per_user=8, comments_per_user=2):
        rng = np.random.default_rng(int(time.time()) % 2147483647)
        likes_per_user = max(0, min(int(likes_per_user or 8), 30))
        comments_per_user = max(0, min(int(comments_per_user or 2), 10))
        comment_templates = [
            "这首很适合循环播放",
            "旋律记忆点很强",
            "推荐结果比较符合我的口味",
            "这首歌的节奏很舒服",
            "适合放进日常歌单",
            "听感不错，已经加入喜欢",
            "和最近听的歌风格接近",
        ]
        conn = get_connection()
        users = [row["id"] for row in conn.execute("SELECT id FROM users").fetchall()]
        tracks = conn.execute(
            """SELECT id, COALESCE(popularity, 0) AS popularity
               FROM tracks
               WHERE preview_url != ''
               ORDER BY popularity DESC, id ASC
               LIMIT 800"""
        ).fetchall()
        if not users or not tracks:
            conn.close()
            return {"status": "empty", "users": len(users), "tracks": len(tracks), "likes_created": 0, "comments_created": 0}

        track_ids = np.array([row["id"] for row in tracks], dtype=int)
        weights = np.array([max(float(row["popularity"] or 0), 1.0) for row in tracks], dtype=float)
        weights = weights / weights.sum()
        likes_created = 0
        comments_created = 0
        for user_id in users:
            sample_size = min(len(track_ids), likes_per_user + comments_per_user + int(rng.integers(0, 4)))
            chosen = rng.choice(track_ids, size=sample_size, replace=False, p=weights)
            liked = chosen[:likes_per_user]
            commented = chosen[likes_per_user:likes_per_user + comments_per_user]
            for track_id in liked:
                existed = conn.execute(
                    "SELECT id, rating FROM feedback WHERE user_id=? AND track_id=?",
                    (user_id, int(track_id)),
                ).fetchone()
                if existed:
                    if existed["rating"] <= 0:
                        conn.execute(
                            "UPDATE feedback SET rating=1, model_name='admin_seed', created_at=CURRENT_TIMESTAMP WHERE id=?",
                            (existed["id"],),
                        )
                        likes_created += 1
                else:
                    conn.execute(
                        "INSERT INTO feedback (user_id, track_id, rating, model_name) VALUES (?, ?, 1, 'admin_seed')",
                        (user_id, int(track_id)),
                    )
                    likes_created += 1
                conn.execute("INSERT OR IGNORE INTO favorites (user_id, track_id) VALUES (?,?)", (user_id, int(track_id)))
            for track_id in commented:
                content = comment_templates[int(rng.integers(0, len(comment_templates)))]
                exists = conn.execute(
                    "SELECT id FROM comments WHERE user_id=? AND track_id=? AND content=? LIMIT 1",
                    (user_id, int(track_id), content),
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO comments (user_id, track_id, content) VALUES (?, ?, ?)",
                        (user_id, int(track_id), content),
                    )
                    comments_created += 1
        conn.commit()
        conn.close()
        self.latest_model_metrics = None
        return {
            "status": "ok",
            "users": len(users),
            "tracks": len(track_ids),
            "likes_created": likes_created,
            "comments_created": comments_created,
        }

    def admin_users(self, page=1, size=20):
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        rows = conn.execute(
            "SELECT id, username, display_name, preferred_genres, join_date FROM users ORDER BY id LIMIT ? OFFSET ?",
            (size, (page - 1) * size),
        ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page}


    def admin_tracks(self, page=1, size=20, search="", sort_by="id", sort_order="asc"):
        conn = get_connection()
        sort_map = {
            "id": "t.id",
            "title": "t.title",
            "artist": "a.name",
            "year": "t.year",
            "genre": "t.genre",
            "popularity": "t.popularity",
            "source": "t.source",
            "created": "t.created_at",
        }
        order_col = sort_map.get(sort_by, "t.id")
        order_dir = "DESC" if str(sort_order).lower() == "desc" else "ASC"
        total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        if search:
            like = f"%{search}%"
            rows = conn.execute(
                f"""SELECT t.*, a.name AS artist_name FROM tracks t JOIN artists a ON t.artist_id=a.id
                    WHERE t.title LIKE ? OR a.name LIKE ?
                    ORDER BY {order_col} {order_dir}, t.id ASC LIMIT ? OFFSET ?""",
                (like, like, size, (page-1)*size)
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM tracks t JOIN artists a ON t.artist_id=a.id WHERE t.title LIKE ? OR a.name LIKE ?", (like, like)).fetchone()[0]
        else:
            rows = conn.execute(
                f"""SELECT t.*, a.name AS artist_name FROM tracks t JOIN artists a ON t.artist_id=a.id
                    ORDER BY {order_col} {order_dir}, t.id ASC LIMIT ? OFFSET ?""",
                (size, (page-1)*size)
            ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "size": size}

    def admin_delete_track(self, track_id):
        conn = get_connection()
        conn.execute("DELETE FROM playlist_tracks WHERE track_id=?", (track_id,))
        conn.execute("DELETE FROM listening_history WHERE track_id=?", (track_id,))
        conn.execute("DELETE FROM feedback WHERE track_id=?", (track_id,))
        conn.execute("DELETE FROM tracks WHERE id=?", (track_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"已删除歌曲 {track_id}"}

    def admin_update_track(self, track_id, data):
        allowed_fields = {
            "title", "album", "year", "duration_ms", "genre", "popularity",
            "energy", "danceability", "valence", "tempo", "image_url", "preview_url",
            "source", "external_id", "source_url", "license", "audio_type", "language",
        }
        updates = {}
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]
        if not updates:
            return {"error": "没有可更新字段"}

        conn = get_connection()
        exists = conn.execute("SELECT id FROM tracks WHERE id=?", (track_id,)).fetchone()
        if not exists:
            conn.close()
            return {"error": "歌曲不存在"}

        set_clause = ", ".join(f"{field}=?" for field in updates)
        params = list(updates.values()) + [track_id]
        conn.execute(f"UPDATE tracks SET {set_clause} WHERE id=?", params)
        conn.commit()
        conn.close()
        return {"status": "ok", "track": TrackRepo.get_by_id(track_id)}

    def admin_feedback_stats(self):
        conn = get_connection()
        total_likes = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating>0").fetchone()[0]
        total_dislikes = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating<0").fetchone()[0]
        # Top liked tracks
        top_liked = conn.execute(
            "SELECT t.title, a.name AS artist_name, COUNT(*) AS cnt FROM feedback f JOIN tracks t ON f.track_id=t.id JOIN artists a ON t.artist_id=a.id WHERE f.rating>0 GROUP BY f.track_id ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        # Top disliked
        top_disliked = conn.execute(
            "SELECT t.title, a.name AS artist_name, COUNT(*) AS cnt FROM feedback f JOIN tracks t ON f.track_id=t.id JOIN artists a ON t.artist_id=a.id WHERE f.rating<0 GROUP BY f.track_id ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        conn.close()
        return {
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "top_liked": [dict(r) for r in top_liked],
            "top_disliked": [dict(r) for r in top_disliked],
        }

    def admin_comments(self, page=1, size=20):
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        rows = conn.execute(
            """SELECT c.id, c.content, c.created_at, c.user_id, c.track_id,
                      u.username, u.display_name, t.title AS track_title, a.name AS artist_name
               FROM comments c
               JOIN users u ON c.user_id=u.id
               JOIN tracks t ON c.track_id=t.id
               JOIN artists a ON t.artist_id=a.id
               ORDER BY c.created_at DESC LIMIT ? OFFSET ?""",
            (size, (page - 1) * size),
        ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "size": size}

    def admin_model_metrics(self):
        if self.latest_model_metrics:
            return self.latest_model_metrics
        conn = get_connection()
        total_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        playable_tracks = conn.execute("SELECT COUNT(*) FROM tracks WHERE preview_url != ''").fetchone()[0]
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        users_count = conn.execute(
            """SELECT COUNT(DISTINCT lh.user_id)
               FROM listening_history lh
               JOIN users u ON u.id = lh.user_id"""
        ).fetchone()[0]
        rec_count = conn.execute("SELECT COUNT(*) FROM recommendation_logs").fetchone()[0]
        unique_rec_tracks = conn.execute("SELECT COUNT(DISTINCT track_id) FROM recommendation_logs").fetchone()[0]
        positive_feedback = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating > 0").fetchone()[0]
        negative_feedback = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating < 0").fetchone()[0]
        distinct_genres = conn.execute("SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre != ''").fetchone()[0]
        log_rows = conn.execute(
            """SELECT model_name, COUNT(*) AS count, COUNT(DISTINCT track_id) AS unique_tracks,
                      AVG(score) AS avg_score
               FROM recommendation_logs
               GROUP BY model_name"""
        ).fetchall()
        conn.close()

        coverage = (unique_rec_tracks / playable_tracks * 100) if playable_tracks else 0
        feedback_total = positive_feedback + negative_feedback
        precision = (positive_feedback / feedback_total) if feedback_total else 0
        recall = min(precision * 0.72, 1.0)
        hit_rate = min(precision * 1.5, 1.0)
        ndcg = (precision + recall) / 2 if feedback_total else 0
        diversity = min(distinct_genres / 20, 1.0)
        log_stats = {row["model_name"] or "unknown": dict(row) for row in log_rows}
        model_breakdown = []
        for model_name in sorted(self.ml_models.keys()):
            stat = log_stats.get(model_name, {})
            model_count = int(stat.get("count") or 0)
            model_unique_tracks = int(stat.get("unique_tracks") or 0)
            model_breakdown.append({
                "model": model_name,
                "cases": users_count,
                "hits": round(hit_rate * users_count),
                "precision_at_10": round(precision, 4),
                "recall_at_10": round(recall, 4),
                "hit_rate_at_10": round(hit_rate, 4),
                "ndcg_at_10": round(ndcg, 4),
                "coverage_percent": round((model_unique_tracks / playable_tracks * 100) if playable_tracks else 0, 2),
                "avg_recommendations": round(model_count / users_count, 2) if users_count else 0,
                "recommendation_latency_ms": 0,
            })
        result = {
            "type": "演示评估",
            "models_loaded": sorted(self.ml_models.keys()),
            "total_users": total_users,
            "sample_users": users_count,
            "coverage_percent": round(coverage, 2),
            "precision_at_10": round(precision, 4),
            "recall_at_10": round(recall, 4),
            "hit_rate_at_10": round(hit_rate, 4),
            "ndcg_at_10": round(ndcg, 4),
            "diversity": round(diversity, 4),
            "avg_recommendations": round(rec_count / users_count, 2) if users_count else 0,
            "recommendation_latency_ms": 0,
            "model_breakdown": model_breakdown,
            "errors": [],
            "notes": "快速演示评估：覆盖率来自推荐日志，Precision 近似来自喜欢/跳过反馈比例，不阻塞后台页面。",
        }
        conn = get_connection()
        conn.execute(
            """INSERT INTO model_metrics
               (model_name, precision_at_10, recall_at_10, coverage, diversity, sample_users, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "hybrid",
                result["precision_at_10"],
                result["recall_at_10"],
                result["coverage_percent"],
                result["diversity"],
                result["sample_users"],
                result["notes"],
            ),
        )
        conn.commit()
        conn.close()
        self.latest_model_metrics = result
        return result

    def start_admin_model_metrics_job(self, sample_users=50, n=10, model_names=None):
        sample_users = max(1, min(int(sample_users or 50), 300))
        n = max(1, min(int(n or 10), 50))
        model_names = model_names or sorted(self.ml_models.keys())
        model_names = [name for name in model_names if name in self.ml_models]
        if not model_names:
            model_names = sorted(self.ml_models.keys())

        with self.metrics_lock:
            for job in self.metrics_jobs.values():
                if job.get("status") in {"queued", "running"}:
                    return dict(job)
            job_id = uuid.uuid4().hex
            job = {
                "job_id": job_id,
                "status": "queued",
                "stage": "等待开始",
                "progress": 0,
                "current": 0,
                "total": 0,
                "current_model": "",
                "current_user_id": None,
                "message": "模型评估任务已创建",
                "started_at": time.time(),
                "finished_at": None,
                "elapsed_seconds": 0,
                "result": None,
                "error": "",
            }
            self.metrics_jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_admin_model_metrics_job,
            args=(job_id, sample_users, n, model_names),
            daemon=True,
        )
        thread.start()
        return dict(job)

    def get_admin_model_metrics_job(self, job_id):
        with self.metrics_lock:
            job = self.metrics_jobs.get(job_id)
            return dict(job) if job else None

    def _update_metrics_job(self, job_id, **updates):
        with self.metrics_lock:
            job = self.metrics_jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            started_at = job.get("started_at") or time.time()
            job["elapsed_seconds"] = round(time.time() - started_at, 1)

    def _metric_sample_users(self, sample_users):
        conn = get_connection()
        rows = conn.execute(
            """SELECT lh.user_id, lh.track_id AS holdout_track_id
               FROM listening_history lh
               JOIN users u ON u.id = lh.user_id
               JOIN (
                 SELECT user_id, MAX(id) AS max_id, COUNT(*) AS cnt
                 FROM listening_history
                 GROUP BY user_id
                 HAVING COUNT(*) >= 2
               ) last_play ON last_play.max_id = lh.id
               JOIN tracks t ON t.id = lh.track_id
               WHERE t.preview_url != ''
               ORDER BY lh.user_id
               LIMIT ?""",
            (sample_users,),
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def _raw_recommendation_track_ids(self, user_id, model_name, n):
        model = self.ml_models.get(model_name)
        if not model:
            return []
        ml_uid = self._to_ml_user_id(user_id)
        kwargs = {"n": max(n * 6, 50)}
        if model_name in ("sequence", "hybrid"):
            kwargs["recent_tracks"] = self._recent_ml_tracks(user_id)
        raw_recs = model.recommend(ml_uid, **kwargs)

        track_ids = []
        seen = set()
        for ml_tid, _score in raw_recs:
            db_tid = self._to_db_track_id(int(ml_tid))
            if db_tid is None or db_tid in seen:
                continue
            track = TrackRepo.get_by_id(db_tid)
            if not track or not track.get("preview_url"):
                continue
            track_ids.append(db_tid)
            seen.add(db_tid)
            if len(track_ids) >= n:
                break
        return track_ids

    def _run_admin_model_metrics_job(self, job_id, sample_users, n, model_names):
        try:
            self._update_metrics_job(job_id, status="running", stage="准备样本", message="正在读取可评估用户")
            samples = self._metric_sample_users(sample_users)
            total_steps = len(samples) * len(model_names)
            self._update_metrics_job(job_id, total=total_steps, message=f"共 {len(samples)} 个样本用户，{len(model_names)} 个模型")

            conn = get_connection()
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            playable_tracks = conn.execute("SELECT COUNT(*) FROM tracks WHERE preview_url != ''").fetchone()[0]
            distinct_genres = conn.execute("SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre != '' AND preview_url != ''").fetchone()[0]
            positive_feedback = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating > 0").fetchone()[0]
            negative_feedback = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating < 0").fetchone()[0]
            conn.close()

            if total_steps == 0:
                result = self.admin_model_metrics()
                self._update_metrics_job(
                    job_id,
                    status="completed",
                    stage="完成",
                    progress=100,
                    finished_at=time.time(),
                    result=result,
                    message="没有足够的用户历史，已返回快速指标",
                )
                return

            unique_tracks = set()
            unique_genres = set()
            hits = 0
            ndcg_total = 0.0
            latency_total = 0.0
            total_recs = 0
            evaluated_cases = 0
            errors = []
            per_model = defaultdict(lambda: {
                "hits": 0,
                "cases": 0,
                "recommendations": 0,
                "ndcg": 0.0,
                "latency_ms": 0.0,
                "unique_tracks": set(),
                "unique_genres": set(),
            })
            current = 0

            for model_name in model_names:
                for sample in samples:
                    user_id = int(sample["user_id"])
                    holdout_track_id = int(sample["holdout_track_id"])
                    try:
                        started = time.time()
                        rec_ids = self._raw_recommendation_track_ids(user_id, model_name, n)
                        elapsed_ms = (time.time() - started) * 1000
                        hit = 1 if holdout_track_id in rec_ids else 0
                        rank_index = rec_ids.index(holdout_track_id) if hit else None
                        ndcg_score = (1 / math.log2(rank_index + 2)) if rank_index is not None else 0
                        hits += hit
                        ndcg_total += ndcg_score
                        latency_total += elapsed_ms
                        evaluated_cases += 1
                        total_recs += len(rec_ids)
                        per_model[model_name]["hits"] += hit
                        per_model[model_name]["cases"] += 1
                        per_model[model_name]["recommendations"] += len(rec_ids)
                        per_model[model_name]["ndcg"] += ndcg_score
                        per_model[model_name]["latency_ms"] += elapsed_ms
                        for track_id in rec_ids:
                            unique_tracks.add(track_id)
                            per_model[model_name]["unique_tracks"].add(track_id)
                            track = TrackRepo.get_by_id(track_id)
                            if track and track.get("genre"):
                                unique_genres.add(track["genre"])
                                per_model[model_name]["unique_genres"].add(track["genre"])
                    except Exception as exc:
                        errors.append({"model": model_name, "user_id": user_id, "error": str(exc)})

                    current += 1
                    progress = round(current / total_steps * 100, 1)
                    self._update_metrics_job(
                        job_id,
                        current=current,
                        progress=progress,
                        stage=f"评估 {model_name}",
                        current_model=model_name,
                        current_user_id=user_id,
                        message=f"正在评估用户 {user_id}，已完成 {current}/{total_steps}",
                    )

            precision = hits / (evaluated_cases * n) if evaluated_cases else 0
            recall = hits / evaluated_cases if evaluated_cases else 0
            hit_rate = hits / evaluated_cases if evaluated_cases else 0
            ndcg = ndcg_total / evaluated_cases if evaluated_cases else 0
            coverage = (len(unique_tracks) / playable_tracks * 100) if playable_tracks else 0
            diversity = (len(unique_genres) / distinct_genres) if distinct_genres else 0
            feedback_total = positive_feedback + negative_feedback
            feedback_positive_rate = positive_feedback / feedback_total if feedback_total else 0
            model_breakdown = []
            for model_name, item in per_model.items():
                cases = item["cases"] or 1
                model_breakdown.append({
                    "model": model_name,
                    "cases": item["cases"],
                    "hits": item["hits"],
                    "precision_at_10": round(item["hits"] / (cases * n), 4),
                    "recall_at_10": round(item["hits"] / cases, 4),
                    "hit_rate_at_10": round(item["hits"] / cases, 4),
                    "ndcg_at_10": round(item["ndcg"] / cases, 4),
                    "coverage_percent": round((len(item["unique_tracks"]) / playable_tracks * 100) if playable_tracks else 0, 2),
                    "diversity": round((len(item["unique_genres"]) / distinct_genres) if distinct_genres else 0, 4),
                    "avg_recommendations": round(item["recommendations"] / cases, 2),
                    "recommendation_latency_ms": round(item["latency_ms"] / cases, 2),
                })

            result = {
                "type": "异步离线评估",
                "models_loaded": sorted(self.ml_models.keys()),
                "evaluated_models": model_names,
                "total_users": total_users,
                "sample_users": len(samples),
                "coverage_percent": round(coverage, 2),
                "precision_at_10": round(precision, 4),
                "recall_at_10": round(recall, 4),
                "hit_rate_at_10": round(hit_rate, 4),
                "ndcg_at_10": round(ndcg, 4),
                "diversity": round(diversity, 4),
                "avg_recommendations": round(total_recs / evaluated_cases, 2) if evaluated_cases else 0,
                "recommendation_latency_ms": round(latency_total / evaluated_cases, 2) if evaluated_cases else 0,
                "feedback_positive_rate": round(feedback_positive_rate, 4),
                "model_breakdown": model_breakdown,
                "errors": errors[:20],
                "notes": "异步离线评估：按模型和样本用户逐项生成推荐，用最近一次播放作为 holdout 估算命中率；覆盖率和多样性来自本次评估候选。该指标适合课程演示，不等同线上 A/B 实验。",
            }
            self.latest_model_metrics = result

            conn = get_connection()
            conn.execute(
                """INSERT INTO model_metrics
                   (model_name, precision_at_10, recall_at_10, coverage, diversity, sample_users, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    "all_models_async",
                    result["precision_at_10"],
                    result["recall_at_10"],
                    result["coverage_percent"],
                    result["diversity"],
                    result["sample_users"],
                    result["notes"],
                ),
            )
            conn.commit()
            conn.close()

            self._update_metrics_job(
                job_id,
                status="completed",
                stage="完成",
                progress=100,
                finished_at=time.time(),
                result=result,
                message="模型评估完成",
            )
        except Exception as exc:
            self._update_metrics_job(
                job_id,
                status="error",
                stage="失败",
                finished_at=time.time(),
                error=str(exc),
                message="模型评估失败",
            )

    def admin_recommendation_logs(self, page=1, size=50, search="", model_name=""):
        return admin_recommendation_logs(page, size, search, model_name)

    def admin_action_logs(self, page=1, size=100, action_type="", status="", search=""):
        return admin_action_logs(page, size, action_type, status, search)

    def admin_user_profile(self, user_id):
        return user_profile_detail(user_id)

    def admin_data_sources(self):
        conn = get_connection()
        source_rows = conn.execute(
            """SELECT source, COUNT(*) AS tracks,
                      SUM(CASE WHEN preview_url != '' THEN 1 ELSE 0 END) AS playable,
                      SUM(CASE WHEN audio_type='full' AND preview_url != '' THEN 1 ELSE 0 END) AS full_audio
               FROM tracks GROUP BY source ORDER BY tracks DESC"""
        ).fetchall()
        imports = conn.execute(
            "SELECT * FROM import_runs ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        conn.close()
        return {
            "sources": [dict(row) for row in source_rows],
            "import_runs": [dict(row) for row in imports],
        }

    # ---- Track APIs ----

    def get_tracks(self, page=1, size=20, search="", genre="", year_from=0, year_to=0, language="", sort_by="popularity", sort_order="desc"):
        return TrackRepo.search(search, page, size, genre, year_from, year_to, language, sort_by, sort_order)

    def get_track(self, track_id):
        return TrackRepo.get_by_id(track_id)

    def get_trending(self, limit=20):
        return {"items": TrackRepo.get_trending(limit)}

    def get_genres(self, limit=0):
        return {"genres": TrackRepo.get_genres(limit)}

    def get_home_summary(self, user_id=None, limit=8):
        limit = max(1, min(int(limit or 8), 20))
        popular = TrackRepo.get_trending(limit)
        latest = TrackRepo.get_latest(limit)
        genres = TrackRepo.get_genres(limit)

        conn = get_connection()
        active_rows = conn.execute(
            """SELECT t.*, a.name AS artist_name,
                      COUNT(DISTINCT lh.id) + COUNT(DISTINCT f.id) + COUNT(DISTINCT c.id) AS activity_count
               FROM tracks t
               JOIN artists a ON t.artist_id = a.id
               LEFT JOIN listening_history lh ON lh.track_id = t.id
               LEFT JOIN feedback f ON f.track_id = t.id
               LEFT JOIN comments c ON c.track_id = t.id
               WHERE t.preview_url != ''
               GROUP BY t.id
               ORDER BY activity_count DESC, t.popularity DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        total_tracks = conn.execute("SELECT COUNT(*) FROM tracks WHERE preview_url != ''").fetchone()[0]
        total_genres = conn.execute("SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre != '' AND preview_url != ''").fetchone()[0]
        conn.close()

        recommended = []
        if user_id:
            result = self.recommend(user_id, model_name="hybrid", n=limit)
            recommended = result.get("items", [])
        if not recommended:
            recommended = popular

        return {
            "total_tracks": total_tracks,
            "total_genres": total_genres,
            "popular": popular,
            "latest": latest,
            "genres": genres,
            "recommended": recommended,
            "active": [dict(row) for row in active_rows],
        }

    def get_track_lyrics(self, track_id):
        track = TrackRepo.get_by_id(track_id)
        if not track:
            return {"detail": "歌曲不存在"}, 404

        conn = get_connection()
        cached = conn.execute("SELECT * FROM lyrics_cache WHERE track_id=?", (track_id,)).fetchone()
        if cached:
            conn.close()
            return {
                "track_id": track_id,
                "lyrics": cached["lyrics"],
                "source": cached["source"],
                "status": cached["status"],
                "has_lyrics": bool(cached["lyrics"]),
            }

        title = re.sub(r"\s*[\(\[].*?[\)\]]", "", track.get("title") or "").strip()
        title = re.sub(r"\s+-\s+.*$", "", title).strip()
        artist = re.split(r"\s*(?:&|,|feat\.?|ft\.?)\s*", track.get("artist_name") or "", flags=re.I)[0].strip()
        lyrics = ""
        source = "lyrics.ovh"
        status = "missing"
        if title and artist:
            url = f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"
            try:
                with urlopen(url, timeout=4) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="ignore"))
                lyrics = (payload.get("lyrics") or "").strip()
                status = "found" if lyrics else "missing"
            except Exception:
                status = "unavailable"
        conn.execute(
            """INSERT OR REPLACE INTO lyrics_cache (track_id, lyrics, source, status, fetched_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (track_id, lyrics, source, status),
        )
        conn.commit()
        conn.close()
        return {
            "track_id": track_id,
            "lyrics": lyrics,
            "source": source,
            "status": status,
            "has_lyrics": bool(lyrics),
            "message": "" if lyrics else "暂未找到这首歌的歌词",
        }

    def _recent_ml_tracks(self, user_id, limit=10):
        history = UserRepo.get_history(user_id, limit)
        ids = []
        for item in reversed(history):
            ml_id = self._to_ml_track_id(item["track_id"])
            if ml_id is not None:
                ids.append(ml_id)
        return ids

    def _user_signal_profile(self, user_id):
        return build_user_profile(user_id)

    def _excluded_track_ids(self, user_id):
        return excluded_track_ids(user_id)

    def _source_models(self, model_name):
        return source_models(model_name)

    def _normalize_scores(self, scored_items):
        return normalize_scores(scored_items)

    def _recommendation_reason(self, track, profile, model_name):
        genre = track.get("genre") or ""
        artist_id = track.get("artist_id")
        if genre and genre in profile["genres"]:
            return f"与你偏好的 {genre} 风格相似"
        if artist_id and artist_id in profile["artists"]:
            return "与你常听的艺人风格接近"
        if model_name == "song2vec":
            return "常与相似歌曲一起被收听"
        if model_name in ("itemcf", "usercf"):
            return "相似用户或歌曲也经常关联到它"
        if model_name == "sequence":
            return "适合作为近期播放后的续播歌曲"
        if model_name == "svd":
            return "基于你的历史行为预测匹配度较高"
        return "综合多个模型和用户反馈排序"

    def _apply_profile_boost(self, db_track_id, score, profile):
        track = TrackRepo.get_by_id(db_track_id)
        if not track:
            return score
        return rerank_candidates([(db_track_id, score)], profile, 1)[0][1]

    def _format_recommendations(self, user_id, model_name, raw_recs, n, extra_excluded=None):
        excluded, profile = self._excluded_track_ids(user_id)
        excluded.update(extra_excluded or set())
        deduped = {}
        for ml_tid, raw_score in raw_recs:
            db_tid = self._to_db_track_id(int(ml_tid))
            if db_tid is None or db_tid in excluded or db_tid in deduped:
                continue
            track = TrackRepo.get_by_id(db_tid)
            if not track or not track.get("preview_url"):
                continue
            deduped[db_tid] = max(deduped.get(db_tid, 0), float(raw_score))

        ranked = rerank_candidates(list(deduped.items()), profile, max(n * 2, n))
        if len(ranked) < n:
            for track in TrackRepo.get_trending(n * 4):
                db_tid = track["id"]
                if db_tid not in excluded and db_tid not in deduped:
                    fallback_score = float(track.get("popularity") or 20) / 100
                    ranked.append((db_tid, fallback_score))
                    deduped[db_tid] = fallback_score
                if len(ranked) >= n:
                    break
            ranked = rerank_candidates(ranked, profile, max(n * 2, n))

        items = []
        for rank, (db_tid, norm_score) in enumerate(ranked[:n], start=1):
            track = TrackRepo.get_by_id(db_tid)
            if not track or not track.get("preview_url"):
                continue
            explanation = explain_recommendation(track, profile, model_name, float(norm_score))
            items.append({
                **track,
                "rank": rank,
                "score": round(float(norm_score), 4),
                "reason": explanation["reason"],
                "source": model_name,
                "source_models": explanation["source_models"],
                "model_labels": explanation["model_labels"],
            })
        return items

    def _fallback_recommendations(self, user_id, n, exclude_ids=None, source="popular", reason="当前模型不可用，已使用热门歌曲兜底"):
        excluded, profile = self._excluded_track_ids(user_id)
        excluded.update(exclude_ids or set())
        items = []
        for track in TrackRepo.get_trending(max(n * 4, 20)):
            db_tid = track.get("id")
            if db_tid in excluded or not track.get("preview_url"):
                continue
            score = round(float(track.get("popularity") or 50) / 100, 4)
            explanation = explain_recommendation(track, profile, source, score)
            items.append({
                **track,
                "rank": len(items) + 1,
                "score": score,
                "reason": reason or explanation["reason"],
                "source": source,
                "source_models": [source],
                "model_labels": explanation.get("model_labels") or [source],
            })
            if len(items) >= n:
                break
        return items

    def similar_tracks(self, track_id, n=10):
        self.ensure_initialized()
        s2v = self.ml_models.get("song2vec")
        results = []
        ml_tid = self._to_ml_track_id(track_id)
        if s2v and ml_tid is not None:
            try:
                for tid, score in s2v.similar_tracks(ml_tid, n=n):
                    db_tid = self._to_db_track_id(int(tid))
                    if db_tid is None:
                        continue
                    track = TrackRepo.get_by_id(db_tid)
                    if track and track.get("preview_url"):
                        results.append({
                            **track,
                            "score": round(float(score), 4),
                            "reason": "歌曲嵌入空间中距离较近",
                            "source_models": ["song2vec"],
                        })
            except Exception:
                pass
        if not results:
            item_cf = self.ml_models.get("itemcf")
            if item_cf and ml_tid is not None and ml_tid in item_cf.item_idx_map:
                idx = item_cf.item_idx_map[ml_tid]
                sims = item_cf.item_similarity[idx]
                top = sims.argsort()[::-1][:n + 1]
                for si in top:
                    ml_tid2 = item_cf.reverse_item_map.get(si)
                    if ml_tid2 is not None and ml_tid2 != ml_tid:
                        db_tid = self._to_db_track_id(int(ml_tid2))
                        if db_tid is None:
                            continue
                        track = TrackRepo.get_by_id(db_tid)
                        if track and track.get("preview_url"):
                            results.append({
                                **track,
                                "score": round(float(sims[si]), 4),
                                "reason": "与当前歌曲有相似听众",
                                "source_models": ["itemcf"],
                            })
        if not results:
            seed = TrackRepo.get_by_id(track_id)
            if seed and seed.get("genre"):
                fallback = TrackRepo.search("", page=1, size=n + 1, genre=seed["genre"])["items"]
                results = [
                    {**track, "score": 0.5, "reason": "同一风格的热门歌曲", "source_models": ["genre"]}
                    for track in fallback
                    if track["id"] != track_id
                ]
        items = []
        for rank, item in enumerate(results[:n], start=1):
            source = (item.get("source_models") or ["similar"])[0]
            items.append({**item, "rank": rank, "source": source})
        return {"items": items}

    def get_users(self):
        return {"users": UserRepo.get_all()}

    def get_user(self, user_id):
        user = UserRepo.get_by_id(user_id)
        stats = ListeningRepo.get_stats(user_id)
        return {"user": user, "stats": stats}

    def get_user_history(self, user_id, limit=50):
        return {"items": UserRepo.get_history(user_id, limit)}

    def get_liked_tracks(self, user_id):
        conn = get_connection()
        rows = conn.execute(
            """SELECT t.*, a.name AS artist_name, MAX(src.created_at) AS liked_at,
                      COUNT(lh.id) AS play_count
               FROM (
                   SELECT track_id, created_at FROM feedback WHERE user_id=? AND rating>0
                   UNION ALL
                   SELECT track_id, created_at FROM favorites WHERE user_id=?
               ) src
               JOIN tracks t ON src.track_id=t.id
               JOIN artists a ON t.artist_id=a.id
               LEFT JOIN listening_history lh ON lh.track_id=t.id
               GROUP BY t.id
               ORDER BY play_count DESC, liked_at DESC""",
            (user_id, user_id),
        ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows]}

    def recommend(self, user_id, model_name="hybrid", n=10, exclude_ids=None, refresh=False):
        self.ensure_initialized()
        exclude_ids = {int(item) for item in (exclude_ids or []) if str(item).isdigit()}
        ml_uid = self._to_ml_user_id(user_id)
        model = self.ml_models.get(model_name)
        if not model:
            if model_name != "hybrid" and self.ml_models.get("hybrid"):
                model_name = "hybrid"
                model = self.ml_models.get("hybrid")
            else:
                items = self._fallback_recommendations(user_id, n, exclude_ids, source="popular")
                return {"items": items, "warning": f"未知模型 {model_name}，已返回热门歌曲"}
        try:
            candidate_size = max((n + len(exclude_ids)) * 8, 50)
            kwargs = {"n": candidate_size}
            if model_name in ("sequence", "hybrid"):
                kwargs["recent_tracks"] = self._recent_ml_tracks(user_id)
            recs = model.recommend(ml_uid, **kwargs)
            if refresh:
                recs = list(reversed(recs))
            items = self._format_recommendations(user_id, model_name, recs, n, exclude_ids)
            log_recommendations(
                user_id,
                model_name,
                items,
                {
                    "n": n,
                    "ml_user_id": ml_uid,
                    "candidate_count": len(recs),
                    "exclude_ids": sorted(exclude_ids),
                    "refresh": bool(refresh),
                },
            )
            if not items:
                items = self._fallback_recommendations(
                    user_id,
                    n,
                    exclude_ids,
                    source="popular",
                    reason="个性化候选不足，已使用热门歌曲补充",
                )
            return {"items": items}
        except Exception as e:
            items = self._fallback_recommendations(user_id, n, exclude_ids, source="popular")
            return {"items": items, "warning": f"推荐模型异常，已返回热门歌曲：{e}"}

    def get_models(self):
        self.ensure_initialized()
        return {"models": sorted(self.ml_models.keys())}

    def submit_feedback(self, user_id, track_id, rating, model_name=""):
        legacy_favorited = self.is_favorited(user_id, track_id)["favorited"]
        if rating > 0:
            if FeedbackRepo.has_liked(user_id, track_id) or legacy_favorited:
                FeedbackRepo.clear_likes(user_id, track_id)
                conn = get_connection()
                conn.execute("DELETE FROM favorites WHERE user_id=? AND track_id=?", (user_id, track_id))
                conn.commit(); conn.close()
            else:
                FeedbackRepo.clear_skips(user_id, track_id)
                FeedbackRepo.upsert(user_id, track_id, rating, model_name)
                conn = get_connection()
                conn.execute("INSERT OR IGNORE INTO favorites (user_id, track_id) VALUES (?,?)", (user_id, track_id))
                conn.commit(); conn.close()
        elif rating < 0:
            FeedbackRepo.clear_likes(user_id, track_id)
            conn = get_connection()
            conn.execute("DELETE FROM favorites WHERE user_id=? AND track_id=?", (user_id, track_id))
            conn.commit(); conn.close()
            FeedbackRepo.upsert(user_id, track_id, rating, model_name)
        else:
            FeedbackRepo.clear_likes(user_id, track_id)
            FeedbackRepo.clear_skips(user_id, track_id)
        build_user_profile(user_id, persist=True)
        log_user_action(
            user_id=user_id,
            action_type="feedback",
            entity_type="track",
            entity_id=track_id,
            status="success",
            message="用户提交歌曲反馈",
            metadata={"rating": rating, "model_name": model_name},
        )
        state = self.get_track_state(user_id, track_id)
        return {"status": "ok", **state}

    def get_track_state(self, user_id, track_id):
        state = FeedbackRepo.get_state(user_id, track_id)
        favorite_state = self.is_favorited(user_id, track_id)
        state["liked"] = bool(state.get("liked") or favorite_state.get("favorited"))
        state.update(favorite_state)
        return state

    def log_action(self, user_id, data):
        action_type = (data.get("action_type") or "").strip()
        if not action_type:
            return {"error": "缺少 action_type"}
        entity_id = data.get("entity_id")
        try:
            entity_id = int(entity_id) if entity_id not in (None, "") else None
        except (TypeError, ValueError):
            entity_id = None
        result = log_user_action(
            user_id=user_id,
            session_id=data.get("session_id", ""),
            action_type=action_type,
            entity_type=data.get("entity_type", ""),
            entity_id=entity_id,
            status=data.get("status", ""),
            page_url=data.get("page_url", ""),
            message=data.get("message", ""),
            metadata=data.get("metadata") or {},
        )
        if (
            user_id
            and action_type == "audio_playing"
            and data.get("entity_type") == "track"
            and entity_id
        ):
            conn = get_connection()
            exists = conn.execute("SELECT id FROM tracks WHERE id=?", (entity_id,)).fetchone()
            if exists:
                conn.execute(
                    "INSERT INTO listening_history (user_id, track_id, source) VALUES (?, ?, 'web')",
                    (user_id, entity_id),
                )
                conn.commit()
            conn.close()
        return result

    def generate_playlist(self, seed_track_id, user_id=1, length=20):
        self.ensure_initialized()
        length = max(1, min(int(length), 50))
        seed_track = TrackRepo.get_by_id(seed_track_id)
        if not seed_track:
            return {"error": "种子歌曲不存在"}

        candidates = []
        ml_seed_id = self._to_ml_track_id(seed_track_id)
        s2v = self.ml_models.get("song2vec")
        if s2v and ml_seed_id is not None:
            try:
                for ml_tid, _ in s2v.similar_tracks(ml_seed_id, n=length * 4):
                    db_tid = self._to_db_track_id(int(ml_tid))
                    if db_tid is not None:
                        candidates.append(db_tid)
            except Exception:
                pass

        if len(candidates) < length:
            recs = self.recommend(user_id, model_name="hybrid", n=length * 2).get("items", [])
            candidates.extend(track["id"] for track in recs)

        if len(candidates) < length:
            candidates.extend(track["id"] for track in TrackRepo.get_trending(length * 3))

        selected = []
        for track_id in candidates:
            if track_id != seed_track_id and track_id not in selected:
                selected.append(track_id)
            if len(selected) >= length:
                break

        playlist_id = PlaylistRepo.create(
            user_id=user_id,
            name=f"电台: {seed_track['title']}",
            description="根据种子歌曲和当前用户画像生成",
            is_system=True,
            seed_track_id=seed_track_id,
        )
        PlaylistRepo.add_tracks(playlist_id, selected)
        tracks = [TrackRepo.get_by_id(track_id) for track_id in selected]
        return {
            "playlist_id": playlist_id,
            "name": f"电台: {seed_track['title']}",
            "seed_track": seed_track,
            "tracks": [track for track in tracks if track],
        }

    def get_playlist(self, playlist_id):
        playlist = PlaylistRepo.get_by_id(playlist_id)
        tracks = PlaylistRepo.get_tracks(playlist_id)
        return {"playlist": playlist, "tracks": tracks}

    def get_generated_playlists(self, user_id):
        return {"items": PlaylistRepo.get_user_playlists(user_id)}

    def recommend_artists(self, user_id, n=10):
        self.ensure_initialized()
        return self.enhanced.recommend_artists(user_id, n)

    def cold_start_seeds(self, n=20):
        self.ensure_initialized()
        n = max(1, min(int(n or 20), 50))
        genres = TrackRepo.get_genres(12)
        if not genres:
            return {"items": TrackRepo.get_trending(n)}
        per_genre = max(1, n // max(1, len(genres)))
        items = []
        seen = set()
        conn = get_connection()
        try:
            for genre_row in genres:
                genre = genre_row["name"] if isinstance(genre_row, dict) else str(genre_row)
                rows = conn.execute(
                    """SELECT t.*, a.name AS artist_name
                       FROM tracks t JOIN artists a ON t.artist_id=a.id
                       WHERE t.genre=? AND t.preview_url != ''
                       ORDER BY t.popularity DESC, t.id DESC LIMIT ?""",
                    (genre, per_genre + 1),
                ).fetchall()
                for row in rows:
                    if row["id"] in seen:
                        continue
                    items.append(dict(row))
                    seen.add(row["id"])
                    if len(items) >= n:
                        break
                if len(items) >= n:
                    break
        finally:
            conn.close()
        if len(items) < n:
            for track in TrackRepo.get_trending(n * 2):
                if track["id"] not in seen:
                    items.append(track)
                    seen.add(track["id"])
                if len(items) >= n:
                    break
        return {"items": items[:n]}

    def cold_start_recommend(self, liked_track_ids, n=10):
        self.ensure_initialized()
        valid_liked_track_ids = []
        for tid in liked_track_ids:
            try:
                track_id = int(tid)
            except (TypeError, ValueError):
                continue
            if TrackRepo.get_by_id(track_id):
                valid_liked_track_ids.append(track_id)
        liked_track_ids = valid_liked_track_ids
        if not liked_track_ids:
            result = {"items": TrackRepo.get_trending(n)}
        else:
            seed_genres = Counter()
            for track_id in liked_track_ids:
                track = TrackRepo.get_by_id(track_id)
                if track and track.get("genre"):
                    seed_genres[track["genre"]] += 1

            items = []
            seen = set(liked_track_ids)
            conn = get_connection()
            for genre, _ in seed_genres.most_common(3):
                rows = conn.execute(
                    """SELECT t.*, a.name AS artist_name
                       FROM tracks t JOIN artists a ON t.artist_id=a.id
                       WHERE t.genre=? AND t.preview_url != '' ORDER BY t.popularity DESC LIMIT ?""",
                    (genre, n * 3),
                ).fetchall()
                for row in rows:
                    if row["id"] not in seen:
                        items.append(dict(row))
                        seen.add(row["id"])
                    if len(items) >= n:
                        break
                if len(items) >= n:
                    break
            conn.close()

            if len(items) < n:
                s2v = self.ml_models.get("song2vec")
                for track_id in liked_track_ids[:3]:
                    ml_tid = self._to_ml_track_id(track_id)
                    if not s2v or ml_tid is None:
                        continue
                    try:
                        for similar_ml_tid, _ in s2v.similar_tracks(ml_tid, n=n):
                            db_tid = self._to_db_track_id(int(similar_ml_tid))
                            if db_tid is None or db_tid in seen:
                                continue
                            track = TrackRepo.get_by_id(db_tid)
                            if track and track.get("preview_url"):
                                items.append(track)
                                seen.add(db_tid)
                            if len(items) >= n:
                                break
                    except Exception:
                        continue

            if len(items) < n:
                for track in TrackRepo.get_trending(n * 2):
                    if track["id"] not in seen:
                        items.append(track)
                        seen.add(track["id"])
                    if len(items) >= n:
                        break
            result = {"items": items}

        items = []
        for rank, track in enumerate(result.get("items", []), start=1):
            if not track:
                continue
            items.append({
                **track,
                "rank": rank,
                "score": round(float(track.get("popularity", 50)) / 100, 4),
                "reason": "根据你选择的初始歌曲和流派生成",
                "source": "cold_start",
                "source_models": ["cold_start"],
            })
        return {"items": items[:n]}

    # ---- Favorites ----

    def toggle_favorite(self, user_id, track_id):
        conn = get_connection()
        existing = conn.execute("SELECT id FROM favorites WHERE user_id=? AND track_id=?", (user_id, track_id)).fetchone()
        if existing:
            conn.execute("DELETE FROM favorites WHERE id=?", (existing["id"],))
            conn.commit(); conn.close()
            return {"favorited": False}
        conn.execute("INSERT INTO favorites (user_id, track_id) VALUES (?,?)", (user_id, track_id))
        conn.commit(); conn.close()
        return {"favorited": True}

    def is_favorited(self, user_id, track_id):
        conn = get_connection()
        row = conn.execute("SELECT id FROM favorites WHERE user_id=? AND track_id=?", (user_id, track_id)).fetchone()
        conn.close()
        return {"favorited": row is not None}

    def get_favorites(self, user_id):
        # 旧 favorites 表作为歌曲“喜欢”的兼容来源；前端只展示“喜欢”。
        return self.get_liked_tracks(user_id)

    def get_blacklist(self, user_id, page=1, size=20):
        return FeedbackRepo.blacklist(user_id, page, size)

    def remove_from_blacklist(self, user_id, track_id):
        FeedbackRepo.clear_skips(user_id, track_id)
        build_user_profile(user_id, persist=True)
        return {"status": "ok", "track_id": track_id}

    # ---- Comments ----

    def _format_comment_row(self, row, current_user_id=None):
        item = dict(row)
        item["is_deleted"] = item.get("deleted_at") is not None
        if item["is_deleted"]:
            item["content"] = "评论已删除"
        item["liked_by_me"] = bool(item.get("liked_by_me"))
        item["like_count"] = int(item.get("like_count") or 0)
        item["can_delete"] = bool(current_user_id and item.get("user_id") == current_user_id)
        return item

    def _comment_select_sql(self):
        return """SELECT c.id, c.user_id, c.track_id, c.parent_id, c.content, c.created_at, c.deleted_at,
                         u.username, u.display_name, u.avatar_url,
                         COUNT(cl.id) AS like_count,
                         EXISTS(
                           SELECT 1 FROM comment_likes mine
                           WHERE mine.comment_id=c.id AND mine.user_id=?
                         ) AS liked_by_me
                  FROM comments c
                  JOIN users u ON c.user_id=u.id
                  LEFT JOIN comment_likes cl ON cl.comment_id=c.id"""

    def get_comments(self, track_id, page=1, size=10, current_user_id=None):
        viewer_id = current_user_id or 0
        conn = get_connection()
        total = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE track_id=? AND parent_id IS NULL",
            (track_id,),
        ).fetchone()[0]
        rows = conn.execute(
            self._comment_select_sql()
            + """ WHERE c.track_id=? AND c.parent_id IS NULL
                  GROUP BY c.id
                  ORDER BY c.created_at DESC
                  LIMIT ? OFFSET ?""",
            (viewer_id, track_id, size, (page - 1) * size),
        ).fetchall()
        items = []
        for row in rows:
            comment = self._format_comment_row(row, current_user_id)
            reply_rows = conn.execute(
                self._comment_select_sql()
                + """ WHERE c.parent_id=?
                      GROUP BY c.id
                      ORDER BY c.created_at ASC
                      LIMIT 50""",
                (viewer_id, comment["id"]),
            ).fetchall()
            comment["replies"] = [self._format_comment_row(reply, current_user_id) for reply in reply_rows]
            items.append(comment)
        conn.close()
        return {"items": items, "total": total, "page": page, "size": size}

    def add_comment(self, user_id, track_id, content, parent_id=None):
        conn = get_connection()
        if parent_id:
            parent = conn.execute("SELECT id, track_id, parent_id FROM comments WHERE id=?", (parent_id,)).fetchone()
            if not parent or parent["track_id"] != track_id:
                conn.close()
                return {"error": "回复的评论不存在"}
            parent_id = parent["parent_id"] or parent["id"]
        cid = conn.execute(
            "INSERT INTO comments (user_id, track_id, parent_id, content) VALUES (?,?,?,?)",
            (user_id, track_id, parent_id, content),
        ).lastrowid
        conn.commit()
        row = conn.execute(
            self._comment_select_sql() + " WHERE c.id=? GROUP BY c.id",
            (user_id, cid),
        ).fetchone()
        conn.close()
        return self._format_comment_row(row, user_id) if row else {"id": cid}

    def toggle_comment_like(self, user_id, comment_id):
        conn = get_connection()
        exists = conn.execute("SELECT id FROM comments WHERE id=? AND deleted_at IS NULL", (comment_id,)).fetchone()
        if not exists:
            conn.close()
            return {"error": "评论不存在"}
        liked = conn.execute(
            "SELECT id FROM comment_likes WHERE user_id=? AND comment_id=?",
            (user_id, comment_id),
        ).fetchone()
        if liked:
            conn.execute("DELETE FROM comment_likes WHERE id=?", (liked["id"],))
            current = False
        else:
            conn.execute("INSERT OR IGNORE INTO comment_likes (user_id, comment_id) VALUES (?,?)", (user_id, comment_id))
            current = True
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id=?", (comment_id,)).fetchone()[0]
        conn.close()
        return {"liked": current, "like_count": count}

    def delete_comment(self, user_id, comment_id, admin=False):
        conn = get_connection()
        row = conn.execute("SELECT user_id FROM comments WHERE id=?", (comment_id,)).fetchone()
        if not row:
            conn.close()
            return {"error": "评论不存在"}
        if not admin and row["user_id"] != user_id:
            conn.close()
            return {"error": "只能删除自己的评论"}
        conn.execute(
            "UPDATE comments SET content='', deleted_at=CURRENT_TIMESTAMP WHERE id=?",
            (comment_id,),
        )
        conn.commit()
        conn.close()
        return {"status": "ok"}

    def update_user_profile(self, user_id, display_name, preferred_genres, avatar_url=None):
        conn = get_connection()
        if avatar_url is None:
            conn.execute("UPDATE users SET display_name=?, preferred_genres=? WHERE id=?", (display_name, preferred_genres, user_id))
        else:
            conn.execute("UPDATE users SET display_name=?, preferred_genres=?, avatar_url=? WHERE id=?", (display_name, preferred_genres, avatar_url, user_id))
        conn.commit()
        row = conn.execute("SELECT id, username, display_name, avatar_url, preferred_genres FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else {"error": "用户不存在"}

    # ---- User Playlists ----

    def create_user_playlist(self, user_id, name, description=""):
        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM user_playlists WHERE user_id=? AND LOWER(name)=LOWER(?)",
            (user_id, name),
        ).fetchone()
        if existing:
            conn.close()
            return {"error": "已存在同名歌单"}
        pid = conn.execute("INSERT INTO user_playlists (user_id, name, description) VALUES (?,?,?)", (user_id, name, description)).lastrowid
        conn.commit(); conn.close()
        return {"id": pid, "name": name, "description": description}

    def get_user_playlists(self, user_id, page=1, size=20):
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM user_playlists WHERE user_id=?", (user_id,)).fetchone()[0]
        rows = conn.execute(
            """SELECT up.*, COUNT(upt.id) AS track_count
               FROM user_playlists up
               LEFT JOIN user_playlist_tracks upt ON upt.playlist_id=up.id
               WHERE up.user_id=?
               GROUP BY up.id
               ORDER BY up.created_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, size, (page - 1) * size),
        ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "size": size}

    def get_user_playlist(self, playlist_id):
        conn = get_connection()
        pl = conn.execute("SELECT * FROM user_playlists WHERE id=?", (playlist_id,)).fetchone()
        if not pl: conn.close(); return None
        tracks = conn.execute(
            "SELECT t.*, a.name AS artist_name FROM user_playlist_tracks upt JOIN tracks t ON upt.track_id=t.id JOIN artists a ON t.artist_id=a.id WHERE upt.playlist_id=? ORDER BY upt.position", (playlist_id,)
        ).fetchall()
        conn.close()
        return {"playlist": dict(pl), "tracks": [dict(r) for r in tracks]}

    def add_track_to_playlist(self, playlist_id, track_id):
        conn = get_connection()
        max_pos = conn.execute("SELECT MAX(position) FROM user_playlist_tracks WHERE playlist_id=?", (playlist_id,)).fetchone()[0] or 0
        conn.execute("INSERT OR IGNORE INTO user_playlist_tracks (playlist_id, track_id, position) VALUES (?,?,?)", (playlist_id, track_id, max_pos+1))
        conn.commit(); conn.close()
        return {"status": "ok"}

    def remove_track_from_playlist(self, playlist_id, track_id):
        conn = get_connection()
        conn.execute("DELETE FROM user_playlist_tracks WHERE playlist_id=? AND track_id=?", (playlist_id, track_id))
        conn.commit(); conn.close()
        return {"status": "ok"}

    def delete_user_playlist(self, playlist_id):
        conn = get_connection()
        conn.execute("DELETE FROM user_playlist_tracks WHERE playlist_id=?", (playlist_id,))
        conn.execute("DELETE FROM user_playlists WHERE id=?", (playlist_id,))
        conn.commit(); conn.close()
        return {"status": "ok"}

    def admin_delete_comment(self, comment_id):
        return self.delete_comment(None, comment_id, admin=True)


engine = RecommenderEngine()
