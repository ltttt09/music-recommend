"""
Dataset loading and preprocessing module.

Supported sources:
- Last.fm 1K users dataset
- Synthetic data generation (for demo & testing)
"""

import os
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def download_lastfm(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Download Last.fm 1K users dataset."""
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    url = "http://mtg.upf.edu/static/datasets/last.fm/lastfm-dataset-1K.tar.gz"
    mirror_url = (
        "https://github.com/odsc2018/"
        "ODSC-West-2018-Last-Fm-Data/raw/master/lastfm-dataset-1K.tar.gz"
    )

    archive_path = raw_dir / "lastfm-dataset-1K.tar.gz"

    if not archive_path.exists():
        print("Downloading Last.fm 1K dataset ...")
        try:
            urllib.request.urlretrieve(url, archive_path)
        except Exception:
            print("Primary link failed, trying mirror ...")
            urllib.request.urlretrieve(mirror_url, archive_path)

    import tarfile
    extract_dir = raw_dir / "lastfm-dataset-1K"
    if not extract_dir.exists():
        print("Extracting ...")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=raw_dir)

    tsv_path = extract_dir / "userid-timestamp-artid-artname-traid-traname.tsv"
    if not tsv_path.exists():
        raise FileNotFoundError(f"TSV file not found: {tsv_path}")

    columns = ["user_id", "timestamp", "artist_id", "artist_name",
               "track_id", "track_name"]
    df = pd.read_csv(tsv_path, sep="\t", header=None, names=columns,
                     on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def generate_synthetic_data(
    n_users: int = 500,
    n_tracks: int = 2000,
    n_artists: int = 200,
    avg_interactions: int = 40,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic listening data for quick demo and testing."""
    rng = np.random.default_rng(seed)

    artists = [f"artist_{i}" for i in range(n_artists)]
    tracks = []
    for i in range(n_tracks):
        artist_idx = i % n_artists
        tracks.append({
            "track_id": f"track_{i:04d}",
            "track_name": f"Song {i:04d}",
            "artist_id": artists[artist_idx],
            "artist_name": f"Artist {artist_idx}",
        })

    user_activity = rng.poisson(avg_interactions, n_users)
    user_activity = np.clip(user_activity, 5, 500)

    track_popularity = 1.0 / (np.arange(1, n_tracks + 1) ** 0.8)
    track_popularity /= track_popularity.sum()

    records = []
    timestamps = pd.date_range("2023-01-01", "2024-06-01", freq="h")

    for user_id in range(n_users):
        n_listens = int(user_activity[user_id])
        sampled_tracks = rng.choice(n_tracks, size=n_listens, p=track_popularity)
        sampled_times = sorted(rng.choice(timestamps, size=n_listens, replace=False))

        for i, (track_idx, ts) in enumerate(zip(sampled_tracks, sampled_times)):
            records.append({
                "user_id": f"user_{user_id:04d}",
                "timestamp": ts,
                "track_id": tracks[track_idx]["track_id"],
                "track_name": tracks[track_idx]["track_name"],
                "artist_id": tracks[track_idx]["artist_id"],
                "artist_name": tracks[track_idx]["artist_name"],
                "play_count": int(rng.integers(1, 5)),
            })

    df = pd.DataFrame(records)
    return df


def load_dataset(source: str = "synthetic", **kwargs) -> pd.DataFrame:
    """Unified data loading entry point."""
    if source == "lastfm":
        return download_lastfm()
    elif source == "synthetic":
        return generate_synthetic_data(**kwargs)
    else:
        raise ValueError(f"Unknown data source: {source}")


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Data cleaning and preprocessing."""
    df = df.copy()
    df = df.dropna(subset=["user_id", "track_id"])

    for col in ["user_id", "track_id", "artist_id"]:
        if col in df.columns:
            unique_vals = df[col].unique()
            mapping = {v: i for i, v in enumerate(unique_vals)}
            df[f"{col}_idx"] = df[col].map(mapping)

    df["listen_count"] = df.groupby(["user_id", "track_id"])["track_id"].transform("count")
    return df


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
    method: str = "leave_last_out",
) -> dict:
    """Split data into train/val/test.

    Args:
        method: "leave_last_out" (each user's last interaction goes to test,
                second-to-last to val) OR "by_user" (split users into disjoint sets)
    """
    if method == "by_user":
        unique_users = df["user_id"].unique()
        train_users, test_users = train_test_split(
            unique_users, test_size=test_size, random_state=random_state
        )
        train_users, val_users = train_test_split(
            train_users, test_size=val_size / (1 - test_size),
            random_state=random_state,
        )
        train_df = df[df["user_id"].isin(train_users)]
        val_df = df[df["user_id"].isin(val_users)]
        test_df = df[df["user_id"].isin(test_users)]
    else:
        # Leave-last-out per user: last interaction -> test, second-to-last -> val
        df = df.sort_values(["user_id", "timestamp"])
        test_rows, val_rows, train_rows = [], [], []

        for _, group in df.groupby("user_id"):
            group = group.sort_values("timestamp")
            if len(group) < 3:
                train_rows.append(group)
            else:
                test_rows.append(group.iloc[-1:])
                val_rows.append(group.iloc[-2:-1])
                train_rows.append(group.iloc[:-2])

        train_df = pd.concat(train_rows) if train_rows else pd.DataFrame()
        val_df = pd.concat(val_rows) if val_rows else pd.DataFrame()
        test_df = pd.concat(test_rows) if test_rows else pd.DataFrame()

    return {"train": train_df, "val": val_df, "test": test_df}
