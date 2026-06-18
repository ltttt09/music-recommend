<template>
  <div class="dh">
    <section class="dh-hero">
      <div class="dh-greet">
        <h1>{{ greeting }}，<span class="dh-grad">{{ displayName }}</span></h1>
        <p>根据你的听歌偏好，为你精选今日推荐</p>
      </div>
      <div class="dh-stats">
        <div class="dh-stat"><span>{{ stats.totalListens }}</span><small>总播放</small></div>
        <div class="dh-stat"><span>{{ stats.topGenre }}</span><small>偏爱流派</small></div>
        <div class="dh-stat"><span>{{ stats.activeTime }}</span><small>活跃时段</small></div>
      </div>
    </section>

    <section class="dh-prefs">
      <span class="dh-prefs-label">{{ isLoggedIn ? '你的偏好' : '推荐探索' }}</span>
      <span v-for="(genre, index) in preferenceGenres" :key="genre" class="dh-tag" :class="{ on: index === 0 }">
        {{ genre }}
      </span>
      <router-link v-if="isLoggedIn" class="dh-add" to="/my?tab=profile">管理偏好</router-link>
      <router-link v-else class="dh-add" to="/login">登录后同步偏好</router-link>
    </section>

    <section class="dh-sec">
      <div class="dh-sec-hd">
        <h2>&#9654; 为你推荐</h2>
        <router-link to="/browse">探索曲库 &rarr;</router-link>
      </div>
      <div v-if="loading.recs" class="dh-grid-6">
        <div v-for="i in 6" :key="i" class="dh-skeleton"></div>
      </div>
      <div v-else-if="recommendations.length" class="dh-grid-6">
        <TrackCard v-for="track in recommendations" :key="track.id" :track="track" />
      </div>
      <div v-else class="dh-empty">暂无推荐歌曲，请先浏览或喜欢几首歌。</div>
    </section>

    <section class="dh-sec">
      <div class="dh-sec-hd"><h2>&#9654; 推荐歌单</h2></div>
      <div class="dh-grid-3">
        <router-link v-for="playlist in profilePlaylists" :key="playlist.id" class="dh-pl-card" :to="'/playlist/' + playlist.id">
          <div class="dh-pl-cover" :style="{ background: grad(playlist.seed) }">
            <div class="dh-pl-mosaic">
              <span v-for="cover in playlist.covers" :key="cover.key" :style="{ background: grad(cover.id) }">
                <img v-if="cover.image_url" :src="cover.image_url" alt="" referrerpolicy="no-referrer" />
              </span>
            </div>
          </div>
          <div class="dh-pl-info">
            <div class="dh-pl-name">{{ playlist.name }}</div>
            <div class="dh-pl-cnt">{{ playlist.count }} 首 · {{ playlist.subtitle }}</div>
          </div>
        </router-link>
      </div>
    </section>

    <section class="dh-sec">
      <div class="dh-sec-hd">
        <h2>&#9654; 你喜欢的</h2>
        <router-link v-if="isLoggedIn" to="/my?tab=likes">查看全部 &rarr;</router-link>
      </div>
      <div v-if="!isLoggedIn" class="dh-login-panel">
        <p>登录后查看你的喜欢歌曲。</p>
        <router-link to="/login">去登录</router-link>
      </div>
      <div v-else-if="favorites.length" class="dh-grid-4">
        <router-link v-for="track in favorites" :key="track.id" :to="'/track/' + track.id" class="dh-like-card">
          <div class="dh-lcover" :style="{ background: grad(track.id) }">
            <img v-if="track.image_url" :src="track.image_url" alt="" referrerpolicy="no-referrer" />
            <span v-else class="dh-lcch">{{ coverChar(track.title) }}</span>
            <span class="dh-heart">&#9829;</span>
          </div>
          <div class="dh-ltitle">{{ track.title }}</div>
          <div class="dh-lartist">{{ track.artist_name }}</div>
        </router-link>
      </div>
      <div v-else class="dh-empty">还没有喜欢的歌曲。</div>
    </section>

    <section class="dh-sec">
      <div class="dh-sec-hd">
        <h2>&#9654; 最近播放</h2>
        <router-link to="/my?tab=history">查看历史 &rarr;</router-link>
      </div>
      <div v-if="recent.length" class="dh-scroll">
        <router-link v-for="track in recent" :key="track.id" :to="'/track/' + track.id" class="dh-scroll-item">
          <div class="dh-scover" :style="{ background: grad(track.id) }">
            <img v-if="track.image_url" :src="track.image_url" alt="" referrerpolicy="no-referrer" />
            <span v-else class="dh-scch">{{ coverChar(track.title) }}</span>
          </div>
          <span>{{ track.title }}</span>
        </router-link>
      </div>
      <div v-else class="dh-empty">暂无播放记录。</div>
    </section>

    <section class="dh-sec">
      <div class="dh-sec-hd">
        <h2>&#9654; 黑名单管理</h2>
        <router-link v-if="isLoggedIn" to="/my?tab=blacklist">管理 &rarr;</router-link>
      </div>
      <div v-if="!isLoggedIn" class="dh-login-panel">
        <p>登录后查看和管理已移入黑名单的歌曲。</p>
        <router-link to="/login">登录后查看</router-link>
      </div>
      <div v-else class="dh-skip">
        <span class="dh-skip-icon">&#128161;</span>
        <div>
          <p>你已移入黑名单 <strong>{{ skipCount }}</strong> 首歌曲</p>
          <small>这些歌曲会暂时避开推荐，进入“我的”可以恢复。</small>
        </div>
      </div>
    </section>

    <footer class="dh-footer">
      <p>&#127925; SoundMind · 发现你的下一首最爱</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api from '../api.js'
import { auth } from '../auth.js'
import TrackCard from '../components/TrackCard.vue'
import { parsePreferences } from '../preferences.js'

const GRADS = [
  'linear-gradient(145deg,#6c5ce7,#a29bfe)',
  'linear-gradient(145deg,#00cec9,#81ecec)',
  'linear-gradient(145deg,#e17055,#fdcb6e)',
  'linear-gradient(145deg,#0984e3,#6c5ce7)',
  'linear-gradient(145deg,#00b894,#55efc4)',
  'linear-gradient(145deg,#d63031,#e17055)',
  'linear-gradient(145deg,#e84393,#fd79a8)',
  'linear-gradient(145deg,#6c5ce7,#00cec9)',
  'linear-gradient(145deg,#2d3436,#636e72)',
  'linear-gradient(145deg,#fdcb6e,#e17055)',
]

const user = ref(null)
const userStats = ref(null)
const recommendations = ref([])
const recent = ref([])
const favorites = ref([])
const generatedPlaylists = ref([])
const profilePlaylists = ref([])
const skipCount = ref(0)
const loading = ref({ recs: true })
const CACHE_TTL = 6 * 60 * 60 * 1000
const CACHE_VERSION = 4

const userId = computed(() => auth.userId || Number(localStorage.getItem('user_id')) || 0)
const isLoggedIn = computed(() => Boolean(userId.value))
const displayName = computed(() => user.value?.display_name || user.value?.username || auth.username || '访客')
const preferenceGenres = computed(() => {
  const parsed = Array.from(parsePreferences(user.value?.preferred_genres || ''))
  const genres = parsed.length ? parsed : [userStats.value?.top_genre || '流行', '中文', '电子']
  return genres.filter(Boolean).slice(0, 8)
})
const stats = computed(() => ({
  totalListens: userStats.value?.total_listens || 0,
  topGenre: userStats.value?.top_genre || preferenceGenres.value[0] || '-',
  activeTime: activeTimeLabel(recent.value),
}))
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

function grad(id) {
  return GRADS[Math.abs(Number(id) || 0) % GRADS.length]
}

function coverChar(title = '') {
  const first = String(title || '?').trim().charAt(0) || '?'
  return /[^\x00-\x7F]/.test(first) ? '🎵' : first.toUpperCase()
}

function normalizeTrack(item = {}) {
  return {
    ...item,
    id: item.id || item.track_id,
    title: item.title || item.track_title || item.track_name || '未知歌曲',
    artist_name: item.artist_name || item.artist || '未知艺人',
    image_url: item.image_url || '',
    genre: item.genre || item.track_genre || '',
    year: item.year || '',
  }
}

function uniqueTracks(items, limit = 12) {
  const seen = new Set()
  const result = []
  for (const item of items.map(normalizeTrack)) {
    if (!item.id || seen.has(item.id)) continue
    seen.add(item.id)
    result.push(item)
    if (result.length >= limit) break
  }
  return result
}

function pickLikedTracks(items, limit = 4) {
  const unique = uniqueTracks(items, 80)
  const hasPlayCount = unique.some((item) => Number(item.play_count || item.listen_count || 0) > 0)
  if (hasPlayCount) {
    return unique
      .sort((a, b) => Number(b.play_count || b.listen_count || 0) - Number(a.play_count || a.listen_count || 0))
      .slice(0, limit)
  }
  return unique
    .map((item) => ({ item, key: Math.sin(Number(item.id || 0) * 9301 + Date.now() / 600000) }))
    .sort((a, b) => b.key - a.key)
    .map((entry) => entry.item)
    .slice(0, limit)
}

function activeTimeLabel(history) {
  const hours = history
    .map((item) => new Date(item.listened_at || item.created_at || '').getHours())
    .filter((hour) => Number.isFinite(hour))
  if (!hours.length) return new Date().getHours() >= 18 ? '晚间' : '日间'
  const avg = hours.reduce((sum, hour) => sum + hour, 0) / hours.length
  if (avg < 6) return '深夜'
  if (avg < 12) return '上午'
  if (avg < 18) return '下午'
  return '晚间'
}

function playlistName(kind, genre) {
  const base = genre || '今日'
  const names = {
    focus: `${base}高能补给站`,
    memory: `刚听完还想循环`,
    liked: `把喜欢放大十倍`,
  }
  return names[kind]
}

function buildProfilePlaylists() {
  const pref = preferenceGenres.value[0] || stats.value.topGenre || '今日'
  const mixed = uniqueTracks([...recommendations.value, ...recent.value, ...favorites.value], 16)
  const recSlice = uniqueTracks(recommendations.value, 10)
  const recentSlice = uniqueTracks(recent.value, 10)
  const favoriteSlice = uniqueTracks(favorites.value, 10)
  const apiCounts = generatedPlaylists.value.map((playlist) => playlist.track_count || playlist.count || 0)
  const source = mixed.length ? mixed : recSlice
  const groups = [
    { id: 'focus', seed: 201, name: playlistName('focus', pref), subtitle: '按当前画像生成', tracks: recSlice.length ? recSlice : source },
    { id: 'memory', seed: 202, name: playlistName('memory', pref), subtitle: '延续最近播放', tracks: recentSlice.length ? recentSlice : source },
    { id: 'liked', seed: 203, name: playlistName('liked', pref), subtitle: '围绕喜欢扩展', tracks: favoriteSlice.length ? favoriteSlice : source },
  ]
  profilePlaylists.value = groups.map((group, index) => {
    const tracks = group.tracks.slice(0, 12)
    const covers = (tracks.length ? tracks : source).slice(0, 4).map((track, index) => ({
      key: `${group.id}-${track.id || index}`,
      id: track.id || group.seed + index,
      image_url: track.image_url || '',
    }))
    while (covers.length < 4) covers.push({ key: `${group.id}-fill-${covers.length}`, id: group.seed + covers.length, image_url: '' })
    return { ...group, id: `home-${group.id}`, count: tracks.length || apiCounts[index] || 0, covers, tracks }
  })
  sessionStorage.setItem('home_recommend_playlists', JSON.stringify(profilePlaylists.value))
}

async function loadFallbackSummary() {
  const data = await api.getHomeSummary(8)
  recommendations.value = uniqueTracks(data.recommended || data.popular || [], 6)
  recent.value = userId.value ? uniqueTracks(data.active || data.latest || [], 8) : []
  favorites.value = []
  skipCount.value = 0
}

function cacheKey() {
  return `home-cache:${userId.value || 'guest'}`
}

function readCache() {
  const raw = localStorage.getItem(cacheKey())
  if (!raw) return false
  try {
    const cached = JSON.parse(raw)
    if (cached.version !== CACHE_VERSION) return false
    if (Date.now() - Number(cached.created_at || 0) > CACHE_TTL) return false
    user.value = cached.user || null
    userStats.value = cached.userStats || null
    recommendations.value = cached.recommendations || []
    recent.value = cached.recent || []
    favorites.value = cached.favorites || []
    generatedPlaylists.value = cached.generatedPlaylists || []
    skipCount.value = cached.skipCount || 0
    buildProfilePlaylists()
    return true
  } catch {
    return false
  }
}

function writeCache() {
  localStorage.setItem(cacheKey(), JSON.stringify({
    version: CACHE_VERSION,
    created_at: Date.now(),
    user: user.value,
    userStats: userStats.value,
    recommendations: recommendations.value,
    recent: recent.value,
    favorites: favorites.value,
    generatedPlaylists: generatedPlaylists.value,
    skipCount: skipCount.value,
  }))
}

function clearHomeCache() {
  localStorage.removeItem(cacheKey())
  sessionStorage.removeItem('home_recommend_playlists')
}

async function refreshHomeFromEvent(event) {
  const playedTrack = event?.detail?.track
  if (playedTrack?.id) {
    recent.value = uniqueTracks([playedTrack, ...recent.value], 8)
  }
  clearHomeCache()
  await loadHome()
  if (playedTrack?.id) {
    recent.value = uniqueTracks([playedTrack, ...recent.value], 8)
    writeCache()
  }
}

async function loadHome() {
  loading.value.recs = true
  const uid = userId.value
  try {
    if (!uid && readCache()) return
    if (!uid) {
      await loadFallbackSummary()
      return
    }
    const [profile, recData, historyData, favData, playlistData, blacklistData] = await Promise.allSettled([
      api.getUser(uid),
      api.getRecommendations(uid, 'hybrid', 6),
      api.getUserHistory(uid, 8),
      api.getFavorites(uid),
      api.getGeneratedPlaylists(uid),
      api.getBlacklist(uid, 1, 1),
    ])
    if (profile.status === 'fulfilled') {
      user.value = profile.value.user || null
      userStats.value = profile.value.stats || null
    }
    if (recData.status === 'fulfilled') recommendations.value = uniqueTracks(recData.value.items || [], 6)
    if (historyData.status === 'fulfilled') recent.value = uniqueTracks(historyData.value.items || [], 8)
    if (favData.status === 'fulfilled') favorites.value = pickLikedTracks(favData.value.items || [], 4)
    if (playlistData.status === 'fulfilled') generatedPlaylists.value = playlistData.value.items || []
    if (blacklistData.status === 'fulfilled') skipCount.value = blacklistData.value.total || 0
    if (!recommendations.value.length) {
      const data = await api.getHomeSummary(8)
      recommendations.value = uniqueTracks(data.recommended || data.popular || [], 6)
    }
  } catch {
    await loadFallbackSummary()
  } finally {
    buildProfilePlaylists()
    writeCache()
    loading.value.recs = false
  }
}

onMounted(() => {
  loadHome()
  window.addEventListener('home-data-invalidated', refreshHomeFromEvent)
  window.addEventListener('track-played', refreshHomeFromEvent)
})

onUnmounted(() => {
  window.removeEventListener('home-data-invalidated', refreshHomeFromEvent)
  window.removeEventListener('track-played', refreshHomeFromEvent)
})
</script>

<style scoped>
.dh { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
.dh-hero { display: flex; justify-content: space-between; align-items: flex-end; padding: 36px 0 24px; gap: 16px; flex-wrap: wrap; }
.dh-hero h1 { font-size: 26px; font-weight: 700; }
.dh-hero p { color: var(--color-text-muted); font-size: 14px; margin-top: 6px; }
.dh-grad { background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.dh-stats { display: flex; gap: 16px; }
.dh-stat { display: flex; flex-direction: column; align-items: center; background: var(--color-surface); border-radius: 14px; padding: 14px 22px; min-width: 90px; border: 1px solid var(--color-border); }
.dh-stat span { font-size: 20px; font-weight: 700; color: var(--color-primary-light); max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dh-stat small { font-size: 11px; color: var(--color-text-muted); margin-top: 4px; }
.dh-prefs { display: flex; align-items: center; gap: 8px; margin-bottom: 28px; flex-wrap: wrap; }
.dh-prefs-label { font-size: 12px; font-weight: 700; color: var(--color-text-muted); text-transform: uppercase; }
.dh-tag { padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; background: var(--color-surface); color: var(--color-text-muted); border: 1px solid var(--color-border); display: flex; align-items: center; gap: 6px; }
.dh-tag.on { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.dh-add { padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; background: transparent; color: var(--color-primary-light); border: 1px dashed var(--color-border); text-decoration: none; }
.dh-sec { margin-bottom: 36px; }
.dh-sec-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.dh-sec-hd h2 { font-size: 17px; font-weight: 600; }
.dh-sec-hd a { font-size: 13px; color: var(--color-primary-light); text-decoration: none; }
.dh-sec-hd a:hover { text-decoration: underline; }
.dh-grid-6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
.dh-grid-6 :deep(.track-card) { min-width: 0; }
.dh-grid-6 :deep(.card-body) { padding: 10px 12px; }
.dh-grid-6 :deep(.card-title) { font-size: 13px; }
.dh-grid-6 :deep(.card-artist) { font-size: 11px; }
.dh-skeleton { aspect-ratio: 1 / 1.35; border-radius: 14px; background: linear-gradient(90deg, var(--color-surface), var(--color-bg), var(--color-surface)); border: 1px solid var(--color-border); animation: pulse 1.2s infinite linear; }
.dh-scroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: thin; scrollbar-color: var(--color-border) transparent; }
.dh-scroll::-webkit-scrollbar { height: 4px; }
.dh-scroll::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 4px; }
.dh-scroll-item { display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; cursor: pointer; text-decoration: none; color: inherit; }
.dh-scroll-item > span { font-size: 11px; color: var(--color-text-muted); max-width: 88px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center; }
.dh-scover { width: 88px; height: 88px; border-radius: 14px; display: flex; align-items: center; justify-content: center; overflow: hidden; transition: transform .2s; }
.dh-scover img, .dh-lcover img, .dh-pl-mosaic img { width: 100%; height: 100%; object-fit: cover; display: block; }
.dh-scroll-item:hover .dh-scover { transform: scale(1.05); }
.dh-scch { font-size: 28px; font-weight: 800; color: rgba(255,255,255,.35); }
.dh-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.dh-pl-card { background: var(--color-surface); border-radius: 14px; overflow: hidden; border: 1px solid var(--color-border); cursor: pointer; transition: transform .2s, box-shadow .2s; color: inherit; text-decoration: none; }
.dh-pl-card:hover { transform: translateY(-3px); box-shadow: 0 12px 36px rgba(0,0,0,.28); }
.dh-pl-cover { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; }
.dh-pl-mosaic { display: grid; grid-template-columns: 1fr 1fr; width: 70%; height: 70%; border-radius: 10px; overflow: hidden; opacity: .9; gap: 2px; }
.dh-pl-mosaic span { border-radius: 2px; overflow: hidden; }
.dh-pl-info { padding: 12px 14px; }
.dh-pl-name { font-size: 14px; font-weight: 600; }
.dh-pl-cnt { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; }
.dh-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.dh-like-card { cursor: pointer; color: inherit; text-decoration: none; }
.dh-lcover { aspect-ratio: 1; border-radius: 14px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.dh-lcch { font-size: 32px; font-weight: 800; color: rgba(255,255,255,.35); }
.dh-heart { position: absolute; top: 8px; right: 8px; font-size: 16px; color: var(--color-like); filter: drop-shadow(0 1px 3px rgba(0,0,0,.4)); }
.dh-ltitle { font-size: 13px; font-weight: 600; margin-top: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dh-lartist { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dh-skip { background: var(--color-surface); border-radius: 14px; padding: 18px 20px; display: flex; align-items: center; gap: 14px; border: 1px solid var(--color-border); }
.dh-skip-icon { font-size: 28px; flex-shrink: 0; }
.dh-skip p { font-size: 14px; font-weight: 500; }
.dh-skip strong { color: var(--color-dislike); }
.dh-skip small { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; display: block; }
.dh-footer { text-align: center; padding: 32px 0; border-top: 1px solid var(--color-border); margin-top: 10px; }
.dh-footer p { font-size: 13px; color: var(--color-text-muted); }
.dh-empty { color: var(--color-text-muted); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 14px; padding: 18px; font-size: 13px; }
.dh-login-panel { display: flex; align-items: center; justify-content: space-between; gap: 12px; background: var(--color-surface); border: 1px dashed var(--color-border); border-radius: 14px; padding: 18px 20px; color: var(--color-text-muted); font-size: 13px; }
.dh-login-panel a { color: var(--color-primary-light); font-weight: 700; text-decoration: none; white-space: nowrap; }
.dh-login-panel a:hover { text-decoration: underline; }
@keyframes pulse { 0% { opacity: .7; } 50% { opacity: 1; } 100% { opacity: .7; } }
@media (max-width: 1024px) { .dh-grid-6 { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) {
  .dh-hero { flex-direction: column; align-items: flex-start; }
  .dh-stats { width: 100%; }
  .dh-stat { flex: 1; min-width: 0; padding: 12px 10px; }
  .dh-grid-6 { grid-template-columns: repeat(2, 1fr); }
  .dh-grid-3 { grid-template-columns: 1fr; }
  .dh-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .dh-login-panel { align-items: flex-start; flex-direction: column; }
  .dh-scover { width: 72px; height: 72px; }
  .dh-scch { font-size: 22px; }
}
</style>
