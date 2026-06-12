"""
Enhanced synthetic data generator with rich metadata.

Generates: artists with genres/countries, tracks with albums/years/audio features.
"""

import numpy as np
import pandas as pd

GENRES = [
    "Rock", "Pop", "Hip-Hop", "Jazz", "Electronic", "Classical",
    "R&B", "Country", "Metal", "Folk", "Blues", "Reggae",
    "Latin", "Soul", "Funk", "Punk", "Indie", "Alternative",
    "Dance", "Ambient",
]

ALBUM_ADJECTIVES = [
    "Midnight", "Electric", "Golden", "Silent", "Crimson", "Neon",
    "Velvet", "Cosmic", "Urban", "Wild", "Fading", "Broken",
    "Endless", "Crystal", "Shadow", "Burning", "Frozen", "Silver",
]

ALBUM_NOUNS = [
    "Dreams", "Highway", "Memories", "Horizon", "Waves", "Echoes",
    "Stories", "Nights", "Garden", "Empire", "Letters", "Seasons",
    "Planets", "Towers", "Rivers", "Frequencies", "Stars", "Thunder",
]

COUNTRIES = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "KR", "BR", "SE", "NL", "MX"]

ALBUMS_PER_ARTIST = (1, 5)
TRACKS_PER_ALBUM = (4, 14)


def generate_enhanced_artists(n_artists: int = 200, seed: int = 42) -> list[dict]:
    """Generate artists with genres and countries."""
    rng = np.random.default_rng(seed)
    artists = []
    for i in range(n_artists):
        n_genres = rng.integers(1, 4)
        artist_genres = sorted(rng.choice(GENRES, size=n_genres, replace=False))
        artists.append({
            "id": i + 1,
            "name": f"Artist {i}",
            "genres": ",".join(artist_genres),
            "country": rng.choice(COUNTRIES),
        })
    return artists


def generate_enhanced_tracks(
    n_tracks: int = 2000, n_artists: int = 200, seed: int = 42
) -> list[dict]:
    """Generate tracks with albums, years, genres, audio features."""
    rng = np.random.default_rng(seed)

    # Pre-generate albums per artist
    artist_albums = {}
    for aid in range(1, n_artists + 1):
        n_albums = rng.integers(*ALBUMS_PER_ARTIST)
        albums = []
        for _ in range(n_albums):
            adj = rng.choice(ALBUM_ADJECTIVES)
            noun = rng.choice(ALBUM_NOUNS)
            albums.append({
                "name": f"{adj} {noun}",
                "year": int(rng.integers(1990, 2025)),
            })
        artist_albums[aid] = albums

    # Artists have primary genres
    artist_genre_sets = {}
    for aid in range(1, n_artists + 1):
        n_g = rng.integers(1, 4)
        artist_genre_sets[aid] = rng.choice(GENRES, size=n_g, replace=False)

    tracks = []
    for i in range(n_tracks):
        artist_id = (i % n_artists) + 1
        albums = artist_albums[artist_id]
        album = albums[i % len(albums)]
        genres = artist_genre_sets[artist_id]
        genre = rng.choice(genres)

        tracks.append({
            "id": i + 1,
            "title": f"Song {i:04d}",
            "artist_id": artist_id,
            "album": album["name"],
            "year": album["year"],
            "duration_ms": int(rng.integers(120000, 360000)),
            "genre": genre,
            "popularity": round(float(rng.random() * 100), 2),
            "energy": round(float(rng.random()), 3),
            "danceability": round(float(rng.random()), 3),
            "valence": round(float(rng.random()), 3),
            "tempo": round(float(rng.uniform(60, 180)), 1),
        })
    return tracks


def generate_enhanced_users(n_users: int = 500, seed: int = 42) -> list[dict]:
    """Generate users with preferred genres."""
    rng = np.random.default_rng(seed)
    users = []
    for i in range(n_users):
        n_g = rng.integers(1, 4)
        prefs = ",".join(sorted(rng.choice(GENRES, size=n_g, replace=False)))
        users.append({
            "id": i + 1,
            "username": f"user_{i:04d}",
            "display_name": f"Listener {i}",
            "preferred_genres": prefs,
        })
    return users


def generate_enhanced_listening(
    n_users: int = 500, n_tracks: int = 2000, avg_interactions: int = 60, seed: int = 42
) -> pd.DataFrame:
    """Generate listening history with timestamps."""
    rng = np.random.default_rng(seed)

    track_popularity = 1.0 / (np.arange(1, n_tracks + 1) ** 0.8)
    track_popularity /= track_popularity.sum()

    timestamps = pd.date_range("2023-01-01", "2024-06-01", freq="h")

    records = []
    for user_id in range(1, n_users + 1):
        n_listens = int(np.clip(rng.poisson(avg_interactions), 5, 500))
        sampled_tracks = rng.choice(n_tracks, size=n_listens, p=track_popularity)
        sampled_times = sorted(rng.choice(timestamps, size=n_listens, replace=False))
        for track_idx, ts in zip(sampled_tracks, sampled_times):
            records.append({
                "user_id": user_id,
                "track_id": int(track_idx) + 1,
                "listened_at": str(ts),
                "source": "organic",
            })
    return pd.DataFrame(records)
