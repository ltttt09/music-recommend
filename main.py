#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SoundMind CLI

Usage:
    python main.py demo              Quick demo
    python main.py train             Train all models
    python main.py eval              Evaluate all models
    python main.py recommend <uid>   Recommend for a user
"""

import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data.dataset import load_dataset, preprocess, split_data
from src.models.cf_model import UserCF, ItemCF, SVDRecommender
from src.models.word2vec_model import Song2VecRecommender
from src.models.sequence_model import SequenceRecommender
from src.models.hybrid import HybridRecommender
from src.evaluation.metrics import evaluate_recommender
from src.utils.helpers import print_recommendations


def load_and_prepare():
    """Load and preprocess data."""
    print("\n[1/3] Loading data ...")
    df = load_dataset(source="synthetic", n_users=300, n_tracks=1000,
                       n_artists=100, avg_interactions=60, seed=42)
    print(f"  Records: {len(df)}")

    print("\n[2/3] Preprocessing ...")
    df = preprocess(df)
    print(f"  Users: {df['user_id'].nunique()}")
    print(f"  Tracks: {df['track_id'].nunique()}")
    print(f"  Artists: {df['artist_id'].nunique()}")

    print("\n[3/3] Splitting datasets (leave-last-out per user) ...")
    splits = split_data(df, method="leave_last_out")
    for name, sdf in splits.items():
        print(f"  {name}: {len(sdf)} records, {sdf['user_id'].nunique()} users")

    return splits, df


def train_models(train_df):
    """Train all models."""
    models = {}

    print("\n>>> Training ItemCF ...")
    t0 = time.time()
    item_cf = ItemCF(k=50, min_interactions=5)
    item_cf.fit(train_df)
    print(f"  Done ({time.time() - t0:.1f}s)")
    models["ItemCF"] = item_cf

    print("\n>>> Training UserCF ...")
    t0 = time.time()
    user_cf = UserCF(k=50, min_interactions=5)
    user_cf.fit(train_df)
    print(f"  Done ({time.time() - t0:.1f}s)")
    models["UserCF"] = user_cf

    print("\n>>> Training SVD ...")
    t0 = time.time()
    svd = SVDRecommender(n_factors=50)
    svd.fit(train_df)
    print(f"  Done ({time.time() - t0:.1f}s)")
    models["SVD"] = svd

    print("\n>>> Training Song2Vec ...")
    t0 = time.time()
    s2v = Song2VecRecommender(vector_size=100, window=5, min_count=3, epochs=15)
    s2v.fit(train_df)
    print(f"  Done ({time.time() - t0:.1f}s)")
    models["Song2Vec"] = s2v

    print("\n>>> Training SequenceRecommender ...")
    t0 = time.time()
    seq = SequenceRecommender(k=3)
    seq.fit(train_df)
    print(f"  Done ({time.time() - t0:.1f}s)")
    models["Sequence"] = seq

    print("\n>>> Building Hybrid model ...")
    hybrid = HybridRecommender(
        models=[item_cf, user_cf, svd, s2v, seq],
        weights=[0.25, 0.15, 0.25, 0.15, 0.20],
    )
    print(f"  Done")
    models["Hybrid"] = hybrid

    return models


def demo():
    """Quick demo: train models and show recommendations."""
    splits, df = load_and_prepare()
    train_df = splits["train"]

    models = train_models(train_df)

    sample_users = train_df["user_id_idx"].sample(
        min(3, train_df["user_id_idx"].nunique())
    ).tolist()

    track_info = train_df[
        ["track_id_idx", "track_name", "artist_name"]
    ].drop_duplicates("track_id_idx")

    for uid in sample_users:
        user_tracks = train_df[train_df["user_id_idx"] == uid]
        print(f"\n{'=' * 60}")
        print(f"  User {uid}")
        print(f"  Listened to {len(user_tracks)} tracks, e.g.:")
        for _, row in user_tracks.head(5).iterrows():
            print(f"    - {row['track_name'][:40]} / {row['artist_name'][:20]}")
        print()

        for name in ["ItemCF", "UserCF", "SVD", "Song2Vec", "Sequence", "Hybrid"]:
            model = models[name]
            try:
                recs = model.recommend(uid, n=10)
                print_recommendations(recs, track_info, f"{name} Recommendations")
            except Exception as e:
                print(f"  {name}: Failed - {e}")


def evaluate():
    """Evaluate all models."""
    splits, _ = load_and_prepare()
    train_df = splits["train"]
    test_df = splits["test"]

    all_test_users = test_df["user_id_idx"].unique().tolist()

    models = train_models(train_df)

    print("\n\nModel Evaluation")
    print("=" * 60)
    results = {}
    for name, model in models.items():
        print(f"\n>> {name}:")
        metrics = evaluate_recommender(model, test_df, all_test_users, k=10)
        results[name] = metrics

    print("\n\nSummary")
    print("-" * 80)
    header = (f"{'Model':<15} {'Precision@10':<14} {'Recall@10':<14} "
              f"{'HitRate@10':<14} {'NDCG@10':<12} {'Coverage':<10}")
    print(header)
    print("-" * 80)
    for name, m in results.items():
        print(f"{name:<15} {m['Precision@10']:<14} {m['Recall@10']:<14} "
              f"{m['HitRate@10']:<14} {m['NDCG@10']:<12} {m['Coverage']:<10}")


def recommend_for_user(user_id: str):
    """Generate recommendations for a specific user."""
    splits, df = load_and_prepare()
    train_df = splits["train"]

    try:
        uid = int(user_id)
    except ValueError:
        match = train_df[train_df["user_id"] == user_id]
        if len(match) == 0:
            print(f"User not found: {user_id}")
            return
        uid = match.iloc[0]["user_id_idx"]

    models = train_models(train_df)
    track_info = train_df[
        ["track_id_idx", "track_name", "artist_name"]
    ].drop_duplicates("track_id_idx")

    user_tracks = train_df[train_df["user_id_idx"] == uid]
    print(f"\nUser {uid} has listened to {len(user_tracks)} tracks")

    hybrid = models["Hybrid"]
    recs = hybrid.recommend(uid, n=10)
    print_recommendations(recs, track_info, "Hybrid Recommendations")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "demo":
        demo()
    elif cmd == "train":
        splits, _ = load_and_prepare()
        train_models(splits["train"])
        print("\nAll models trained!")
    elif cmd == "eval":
        evaluate()
    elif cmd == "recommend":
        if len(sys.argv) < 3:
            print("Usage: python main.py recommend <user_id>")
            sys.exit(1)
        recommend_for_user(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
