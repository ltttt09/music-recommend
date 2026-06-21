"""
Enhanced recommendation engine with feedback, playlists, artist recs, trending & cold start.
v2: incorporates favorites, comments, and time-decay signals.
"""

import numpy as np
from collections import defaultdict, Counter

from src.db.repository import (
    TrackRepo, ArtistRepo, UserRepo, ListeningRepo, FeedbackRepo, PlaylistRepo,
)
from src.db.schema import get_connection


class EnhancedRecommender:
    """Extended recommendation features on top of the ML models."""

    def __init__(self, ml_models: dict):
        self.ml = ml_models

    # ---- User Profile ----

    def _get_user_profile(self, user_id):
        """Build user affinity profile from favorites, likes, comments."""
        profile = {"genres": Counter(), "artists": Counter(), "tracks": set()}
        # Favorites (strong signal, weight 3)
        try:
            conn = get_connection()
            favs = conn.execute("SELECT track_id FROM favorites WHERE user_id=?", (user_id,)).fetchall()
            for row in favs:
                t = TrackRepo.get_by_id(row["track_id"])
                if t:
                    profile["genres"][t.get("genre","")] += 3
                    profile["artists"][t.get("artist_id",0)] += 3
                    profile["tracks"].add(row["track_id"])
            conn.close()
        except: pass
        # Liked feedback (weight 2)
        liked = FeedbackRepo.get_liked_tracks(user_id)
        for ltid in list(liked)[:30]:
            t = TrackRepo.get_by_id(ltid)
            if t and ltid not in profile["tracks"]:
                profile["genres"][t.get("genre","")] += 2
                profile["artists"][t.get("artist_id",0)] += 2
                profile["tracks"].add(ltid)
        # Commented tracks (weak signal, weight 1)
        try:
            conn = get_connection()
            cts = conn.execute("SELECT DISTINCT track_id FROM comments WHERE user_id=?", (user_id,)).fetchall()
            for row in cts:
                t = TrackRepo.get_by_id(row["track_id"])
                if t and row["track_id"] not in profile["tracks"]:
                    profile["genres"][t.get("genre","")] += 1
                    profile["artists"][t.get("artist_id",0)] += 1
                    profile["tracks"].add(row["track_id"])
            conn.close()
        except: pass
        return profile

    # ---- Feedback-aware Recommendations ----

    def recommend_with_feedback(self, user_id: int, n: int = 10, model_name: str = "hybrid"):
        """Recommend with full feedback: excludes dislikes, boosts favorites/likes/comments affinity."""
        model = self.ml.get(model_name)
        if model is None:
            return {"items": [], "error": f"Unknown model: {model_name}"}

        disliked = FeedbackRepo.get_disliked_tracks(user_id)
        profile = self._get_user_profile(user_id)

        try:
            recs = model.recommend(user_id, n=n * 4)
        except Exception as e:
            return {"items": [], "error": str(e)}

        items = []
        for tid, score in recs:
            if tid in disliked or tid in profile["tracks"]:
                continue
            track = TrackRepo.get_by_id(tid)
            boost = 1.0
            if track:
                g = track.get("genre", "")
                a = track.get("artist_id", 0)
                if g in profile["genres"]: boost += 0.1 * profile["genres"][g]
                if a in profile["artists"]: boost += 0.15 * profile["artists"][a]
                year = track.get("year", 2000)
                if year >= 2020: boost *= 1.1
                elif year >= 2010: boost *= 1.05
            items.append((tid, score * min(boost, 3.0)))

        items.sort(key=lambda x: x[1], reverse=True)
        return {"items": [self._format_track(tid, s) for tid, s in items[:n]]}

    # ---- Playlist Generation ----

    def generate_playlist(self, seed_track_id: int, user_id: int = 1, length: int = 20):
        """Generate a playlist from a seed track using Song2Vec similarity."""
        s2v = self.ml.get("song2vec")
        item_cf = self.ml.get("itemcf")

        candidates = []
        if s2v:
            try:
                sims = s2v.similar_tracks(seed_track_id, n=length * 3)
                candidates.extend(tid for tid, _ in sims)
            except Exception: pass

        if not candidates and item_cf:
            try:
                recs = item_cf.recommend(user_id, n=length * 3)
                candidates.extend(tid for tid, _ in recs)
            except Exception: pass

        if not candidates:
            trending = self.get_trending(limit=length * 3)
            candidates = [t["id"] for t in trending]

        selected = []
        for tid in candidates:
            if tid != seed_track_id and tid not in selected:
                selected.append(tid)
            if len(selected) >= length: break

        seed_track = TrackRepo.get_by_id(seed_track_id)
        name = f"电台: {seed_track['title']}" if seed_track else "推荐电台"
        playlist_id = PlaylistRepo.create(user_id=user_id, name=name, is_system=True, seed_track_id=seed_track_id)
        PlaylistRepo.add_tracks(playlist_id, selected)

        tracks = [TrackRepo.get_by_id(tid) for tid in selected]
        return {"playlist_id": playlist_id, "name": name, "seed_track": seed_track,
                "tracks": [t for t in tracks if t is not None]}

    # ---- Artist Recommendations ----

    def recommend_artists(self, user_id: int, n: int = 10):
        listened = ListeningRepo.get_listened_track_ids(user_id)
        if not listened: return {"items": []}
        artist_counter = Counter()
        artist_genres = {}
        for tid in listened:
            track = TrackRepo.get_by_id(tid)
            if track:
                artist_counter[track["artist_id"]] += 1
                if track["artist_id"] not in artist_genres:
                    artist_genres[track["artist_id"]] = track.get("genre", "")
        known_artists = set(artist_counter.keys())
        user_genres = set(artist_genres.values())
        candidates = Counter()
        for aid in artist_counter:
            artist = ArtistRepo.get_by_id(aid)
            if not artist or not artist.get("genres"): continue
            for genre in artist["genres"].split(","):
                candidates[aid] += 1
        conn = get_connection()
        for genre in user_genres:
            if not genre: continue
            placeholders = ",".join("?" * len(known_artists))
            rows = conn.execute(
                f"SELECT DISTINCT a.id, a.name, a.genres, COUNT(lh.id) AS play_count FROM artists a JOIN tracks t ON t.artist_id=a.id LEFT JOIN listening_history lh ON lh.track_id=t.id WHERE a.genres LIKE ? AND a.id NOT IN ({placeholders}) GROUP BY a.id ORDER BY play_count DESC LIMIT ?",
                [f"%{genre}%"] + list(int(a) for a in known_artists) + [n],
            ).fetchall()
            for row in rows:
                if row["id"] not in known_artists: candidates[row["id"]] += 1
        conn.close()
        ranked = candidates.most_common(n)
        return {"items": [{**ArtistRepo.get_by_id(aid), "match_score": s} for aid, s in ranked]}

    # ---- Trending Charts ----

    def get_trending(self, limit: int = 20):
        return TrackRepo.get_trending(limit)

    # ---- Helpers ----

    def _format_track(self, track_id: int, score: float):
        track = TrackRepo.get_by_id(track_id)
        if track: return {**track, "score": round(float(score), 4)}
        return {"id": track_id, "title": f"Track {track_id}", "artist_name": "Unknown", "score": round(float(score), 4)}

    def _format_list(self, items):
        return {"items": items}
