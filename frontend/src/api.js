const BASE = import.meta.env.VITE_API_BASE || "/api";

async function fetchJSON(url, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export default {
  register(username, password, displayName) {
    return fetchJSON(`${BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, display_name: displayName }),
    });
  },
  login(username, password) {
    return fetchJSON(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  },

  adminStats() { return fetchJSON(`${BASE}/admin/stats`); },
  adminUsers(page = 1) { return fetchJSON(`${BASE}/admin/users?page=${page}`); },
  adminTracks(page = 1, size = 20, search = "", sortBy = "id", sortOrder = "asc") {
    const p = new URLSearchParams({ page, size, search, sort_by: sortBy, sort_order: sortOrder });
    return fetchJSON(`${BASE}/admin/tracks?${p}`);
  },
  adminUpdateTrack(trackId, data) {
    return fetchJSON(`${BASE}/admin/tracks/${trackId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  adminComments(page = 1, size = 20) {
    return fetchJSON(`${BASE}/admin/comments?page=${page}&size=${size}`);
  },
  adminFeedback() { return fetchJSON(`${BASE}/admin/feedback`); },
  adminSystem() { return fetchJSON(`${BASE}/admin/system`); },
  adminModelMetrics() { return fetchJSON(`${BASE}/admin/model-metrics`); },
  adminRecommendationLogs(page = 1, size = 50) {
    return fetchJSON(`${BASE}/admin/recommendation-logs?page=${page}&size=${size}`);
  },
  adminActionLogs(page = 1, size = 100, actionType = "") {
    const p = new URLSearchParams({ page, size });
    if (actionType) p.set("action_type", actionType);
    return fetchJSON(`${BASE}/admin/action-logs?${p}`);
  },
  adminUserProfile(userId) {
    return fetchJSON(`${BASE}/admin/users/${userId}/profile`);
  },
  adminDataSources() {
    return fetchJSON(`${BASE}/admin/data-sources`);
  },

  getTracks(page = 1, size = 20, search = "", genre = "", yearFrom = 0, yearTo = 0, language = "", sortBy = "popularity", sortOrder = "desc") {
    const p = new URLSearchParams({ page, size, search, genre });
    if (yearFrom) p.set("year_from", yearFrom);
    if (yearTo) p.set("year_to", yearTo);
    if (language) p.set("language", language);
    if (sortBy) p.set("sort_by", sortBy);
    if (sortOrder) p.set("sort_order", sortOrder);
    return fetchJSON(`${BASE}/tracks?${p}`);
  },
  getTrack(id) { return fetchJSON(`${BASE}/tracks/${id}`); },
  getSimilarTracks(id, n = 10) { return fetchJSON(`${BASE}/tracks/${id}/similar?n=${n}`); },
  getTrending(limit = 20) { return fetchJSON(`${BASE}/tracks/trending?limit=${limit}`); },
  getGenres() { return fetchJSON(`${BASE}/tracks/genres`); },
  generatePlaylist(seedTrackId, length = 20) {
    return fetchJSON(`${BASE}/tracks/playlist/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed_track_id: seedTrackId, length }),
    });
  },
  getPlaylist(id) { return fetchJSON(`${BASE}/tracks/playlist/${id}`); },

  getUsers() { return fetchJSON(`${BASE}/users`); },
  getUser(id) { return fetchJSON(`${BASE}/users/${id}`); },
  getUserHistory(id, limit = 50) { return fetchJSON(`${BASE}/users/${id}/history?limit=${limit}`); },
  getLikedTracks(id) { return fetchJSON(`${BASE}/users/${id}/liked`); },
  getRecommendations(userId, model = "hybrid", n = 10) {
    return fetchJSON(`${BASE}/users/${userId}/recommend?model=${model}&n=${n}`);
  },
  getArtistRecommendations(userId, n = 10) {
    return fetchJSON(`${BASE}/users/${userId}/artists?n=${n}`);
  },
  getGeneratedPlaylists(userId) { return fetchJSON(`${BASE}/users/${userId}/playlists`); },
  submitFeedback(userId, trackId, rating, modelName = "") {
    return fetchJSON(`${BASE}/users/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, track_id: trackId, rating, model_name: modelName }),
    });
  },
  getColdStartSeeds(n = 20) { return fetchJSON(`${BASE}/users/cold-start/seeds?n=${n}`); },
  coldStartRecommend(trackIds, n = 10) {
    return fetchJSON(`${BASE}/users/cold-start/recommend?n=${n}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_ids: trackIds }),
    });
  },
  getModels() { return fetchJSON(`${BASE}/models`); },

  toggleFavorite(trackId) {
    return fetchJSON(`${BASE}/tracks/${trackId}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  },
  checkFavorite(trackId, userId = 1) {
    return fetchJSON(`${BASE}/tracks/${trackId}/favorite?user_id=${userId}`);
  },
  getTrackState(trackId, userId = 1) {
    return fetchJSON(`${BASE}/tracks/${trackId}/state?user_id=${userId}`);
  },
  getFavorites(userId) { return fetchJSON(`${BASE}/users/${userId}/favorites`); },
  updateProfile(userId, data) {
    return fetchJSON(`${BASE}/users/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  getComments(trackId) { return fetchJSON(`${BASE}/tracks/${trackId}/comments`); },
  addComment(trackId, userId, content) {
    return fetchJSON(`${BASE}/tracks/${trackId}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
  },
  deleteComment(commentId) {
    return fetchJSON(`${BASE}/admin/comments/${commentId}`, { method: "DELETE" });
  },

  createUserPlaylist(userId, name, desc = "") {
    return fetchJSON(`${BASE}/tracks/user-playlists`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: desc }),
    });
  },
  getUserCreatedPlaylists(userId) {
    return fetchJSON(`${BASE}/tracks/user-playlists/${userId}`);
  },
  getUserPlaylist(id) { return fetchJSON(`${BASE}/tracks/user-playlist/${id}`); },
  addToPlaylist(playlistId, trackId) {
    return fetchJSON(`${BASE}/tracks/user-playlist/${playlistId}/tracks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: trackId }),
    });
  },
  removeFromPlaylist(playlistId, trackId) {
    return fetchJSON(`${BASE}/tracks/user-playlist/${playlistId}/tracks/${trackId}`, { method: "DELETE" });
  },
  deleteUserPlaylist(playlistId) {
    return fetchJSON(`${BASE}/tracks/user-playlist/${playlistId}`, { method: "DELETE" });
  },
};
