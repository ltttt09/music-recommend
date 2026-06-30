import { apiFetch } from "./api/client.js";

function fetchJSON(path, options = {}) {
  return apiFetch(path, options);
}

export default {
  register(username, password, displayName) {
    return fetchJSON(`/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, display_name: displayName }),
    });
  },
  login(username, password) {
    return fetchJSON(`/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  },

  me() { return fetchJSON(`/auth/me`); },

  adminStats() { return fetchJSON(`/admin/stats`); },
  adminUsers(page = 1, size = 20, search = "", genre = "", sortBy = "id", sortOrder = "asc") {
    const p = new URLSearchParams({ page, size, search, genre, sort_by: sortBy, sort_order: sortOrder });
    return fetchJSON(`/admin/users?${p}`);
  },
  adminTracks(page = 1, size = 20, search = "", sortBy = "id", sortOrder = "asc") {
    const p = new URLSearchParams({ page, size, search, sort_by: sortBy, sort_order: sortOrder });
    return fetchJSON(`/admin/tracks?${p}`);
  },
  adminUpdateTrack(trackId, data) {
    return fetchJSON(`/admin/tracks/${trackId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  adminComments(page = 1, size = 20, search = "") {
    const p = new URLSearchParams({ page, size });
    if (search) p.set("search", search);
    return fetchJSON(`/admin/comments?${p}`);
  },
  adminFeedback() { return fetchJSON(`/admin/feedback`); },
  adminSystem() { return fetchJSON(`/admin/system`); },
  adminModelMetrics() { return fetchJSON(`/admin/model-metrics`); },
  adminHybridWeights() { return fetchJSON(`/admin/hybrid-weights`); },
  updateAdminHybridWeights(weights) {
    return fetchJSON(`/admin/hybrid-weights`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weights }),
    });
  },
  adminRecommendationLogs(page = 1, size = 50) {
    return fetchJSON(`/admin/recommendation-logs?page=${page}&size=${size}`);
  },
  adminActionLogs(page = 1, size = 100, actionType = '', status = '', search = '') {
    const p = new URLSearchParams({ page, size });
    if (actionType) p.set("action_type", actionType);
    if (status) p.set("status", status);
    if (search) p.set("search", search);
    return fetchJSON(`/admin/action-logs?${p}`);
  },
  adminUserProfile(userId) {
    return fetchJSON(`/admin/users/${userId}/profile`);
  },
  adminDataSources() {
    return fetchJSON(`/admin/data-sources`);
  },
  adminReindexIds() {
    return fetchJSON(`/admin/reindex-ids`, { method: "POST" });
  },
  adminImportItunes(target = 10000, limitPerQuery = 200) {
    return fetchJSON(`/admin/import-itunes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, limit_per_query: limitPerQuery }),
    });
  },
  adminImportProgress() { return fetchJSON(`/admin/import-progress`); },
  adminImportCancel() {
    return fetchJSON(`/admin/import-cancel`, { method: "POST" });
  },

  getTracks(page = 1, size = 20, search = "", genre = "", yearFrom = 0, yearTo = 0, language = "", sortBy = "popularity", sortOrder = "desc") {
    const p = new URLSearchParams({ page, size, search, genre });
    if (yearFrom) p.set("year_from", yearFrom);
    if (yearTo) p.set("year_to", yearTo);
    if (language) p.set("language", language);
    if (sortBy) p.set("sort_by", sortBy);
    if (sortOrder) p.set("sort_order", sortOrder);
    return fetchJSON(`/tracks?${p}`);
  },
  getTrack(id) { return fetchJSON(`/tracks/${id}`); },
  getSimilarTracks(id, n = 10) { return fetchJSON(`/tracks/${id}/similar?n=${n}`); },
  getTrackLyrics(id) { return fetchJSON(`/tracks/${id}/lyrics`); },
  getTrending(limit = 20) { return fetchJSON(`/tracks/trending?limit=${limit}`); },
  getGenres(limit = 0) { return fetchJSON(`/tracks/genres?limit=${limit}`); },
  getHomeSummary(limit = 8) { return fetchJSON(`/tracks/rankings?limit=${limit}`); },
  getPlaylist(id) { return fetchJSON(`/tracks/playlist/${id}`); },

  getUsers() { return fetchJSON(`/users`); },
  getUser(id) { return fetchJSON(`/users/${id}`); },
  getUserHistory(id, limit = 50) { return fetchJSON(`/users/${id}/history?limit=${limit}`); },
  getLikedTracks(id) { return fetchJSON(`/users/${id}/liked`); },
  unlikeTrack(userId, trackId) { return fetchJSON(`/users/${userId}/liked/${trackId}`, { method: "DELETE" }); },
  getRecommendations(userId, model = "hybrid", n = 10, excludeIds = [], refresh = false) {
    const p = new URLSearchParams({ model, n });
    if (excludeIds.length) p.set("exclude_ids", excludeIds.join(","));
    if (refresh) p.set("refresh", "1");
    return fetchJSON(`/users/${userId}/recommend?${p}`);
  },
  getArtistRecommendations(userId, n = 10) {
    return fetchJSON(`/users/${userId}/artists?n=${n}`);
  },
  getGeneratedPlaylists(userId) { return fetchJSON(`/users/${userId}/playlists`); },
  submitFeedback(userId, trackId, rating, modelName = "") {
    return fetchJSON(`/users/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: trackId, rating, model_name: modelName }),
    });
  },
  getColdStartSeeds(n = 20) { return fetchJSON(`/users/cold-start/seeds?n=${n}`); },
  coldStartRecommend(trackIds, n = 10) {
    return fetchJSON(`/users/cold-start/recommend?n=${n}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_ids: trackIds }),
    });
  },
  getModels() { return fetchJSON(`/models`); },

  toggleFavorite(trackId) {
    return fetchJSON(`/tracks/${trackId}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  },
  checkFavorite(trackId) {
    return fetchJSON(`/tracks/${trackId}/favorite`);
  },
  getTrackState(trackId) {
    return fetchJSON(`/tracks/${trackId}/state`);
  },
  getFavorites(userId) { return fetchJSON(`/users/${userId}/favorites`); },
  getBlacklist(userId, page = 1, size = 20) { return fetchJSON(`/users/${userId}/blacklist?page=${page}&size=${size}`); },
  removeFromBlacklist(userId, trackId) {
    return fetchJSON(`/users/${userId}/blacklist/${trackId}`, { method: "DELETE" });
  },
  updateProfile(userId, data) {
    return fetchJSON(`/users/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  getComments(trackId, page = 1, size = 10) { return fetchJSON(`/tracks/${trackId}/comments?page=${page}&size=${size}`); },
  addComment(trackId, content, parentId = null) {
    return fetchJSON(`/tracks/${trackId}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, parent_id: parentId }),
    });
  },
  toggleCommentLike(commentId) {
    return fetchJSON(`/tracks/comments/${commentId}/like`, { method: "POST" });
  },
  deleteOwnComment(commentId) {
    return fetchJSON(`/tracks/comments/${commentId}`, { method: "DELETE" });
  },
  deleteComment(commentId) {
    return fetchJSON(`/admin/comments/${commentId}`, { method: "DELETE" });
  },

  createUserPlaylist(userId, name, desc = "") {
    return fetchJSON(`/tracks/user-playlists`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: desc }),
    });
  },
  getUserCreatedPlaylists(userId, page = 1, size = 20) {
    return fetchJSON(`/tracks/user-playlists/${userId}?page=${page}&size=${size}`);
  },
  getUserPlaylist(id) { return fetchJSON(`/tracks/user-playlist/${id}`); },
  addToPlaylist(playlistId, trackId) {
    return fetchJSON(`/tracks/user-playlist/${playlistId}/tracks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: trackId }),
    });
  },
  removeFromPlaylist(playlistId, trackId) {
    return fetchJSON(`/tracks/user-playlist/${playlistId}/tracks/${trackId}`, { method: "DELETE" });
  },
  deleteUserPlaylist(playlistId) {
    return fetchJSON(`/tracks/user-playlist/${playlistId}`, { method: "DELETE" });
  },
  updatePlaylistCover(playlistId, coverUrl) {
    return fetchJSON(`/tracks/user-playlist/${playlistId}/cover`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cover_url: coverUrl }),
    });
  },
};
