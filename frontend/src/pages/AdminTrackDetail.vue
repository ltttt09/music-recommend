<template>
  <div class="container admin-track-page">
    <button class="back-btn" @click="goBack">&larr; 返回管理页</button>
    <div v-if="loading" class="spinner"></div>
    <div v-else-if="error" class="error-state">
      <h2>歌曲加载失败</h2>
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="goBack">返回</button>
    </div>
    <template v-else>
      <section class="admin-track-hero">
        <div class="admin-track-cover" :style="coverBg">
          <img v-if="track.image_url && !imgFailed" :src="track.image_url" :alt="track.title" referrerpolicy="no-referrer" @error="imgFailed = true" />
          <span v-else>{{ coverChar }}</span>
        </div>
        <div class="admin-track-info">
          <p class="eyebrow">管理端只读详情</p>
          <h1>{{ track.title || '未知歌曲' }}</h1>
          <p class="artist">{{ track.artist_name || '未知艺人' }}</p>
          <div class="meta-grid">
            <div><span>专辑</span><strong>{{ track.album || '-' }}</strong></div>
            <div><span>流派</span><strong>{{ track.genre || '-' }}</strong></div>
            <div><span>年份</span><strong>{{ track.year || '-' }}</strong></div>
            <div><span>语言</span><strong>{{ track.language_group || track.language || '-' }}</strong></div>
            <div><span>数据源</span><strong>{{ track.source || 'itunes' }}</strong></div>
            <div><span>音频类型</span><strong>{{ track.audio_type === 'full' ? '完整音频' : '30 秒试听' }}</strong></div>
            <div><span>热度</span><strong>{{ Math.round(track.popularity || 0) }}</strong></div>
            <div><span>时长</span><strong>{{ formatDuration(track.duration_ms) }}</strong></div>
          </div>
        </div>
      </section>

      <section class="admin-track-section">
        <h2>资源状态</h2>
        <div class="resource-grid">
          <div :class="track.image_url ? 'ok' : 'muted'"><span>封面</span><strong>{{ track.image_url ? '已配置' : '缺失' }}</strong></div>
          <div :class="track.preview_url ? 'ok' : 'muted'"><span>试听地址</span><strong>{{ track.preview_url ? '可用' : '缺失' }}</strong></div>
          <div><span>歌曲 ID</span><strong>{{ track.id }}</strong></div>
          <div><span>艺人 ID</span><strong>{{ track.artist_id || '-' }}</strong></div>
        </div>
      </section>

      <section class="admin-track-section">
        <h2>歌词</h2>
        <div v-if="lyricsLoading" class="lyrics-box muted">歌词加载中...</div>
        <pre v-else-if="lyrics" class="lyrics-box">{{ lyrics }}</pre>
        <div v-else class="lyrics-box muted">{{ lyricsMessage }}</div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'
import { coverStyle, coverText } from '../cover.js'

const route = useRoute()
const router = useRouter()
const track = ref({})
const loading = ref(true)
const error = ref('')
const imgFailed = ref(false)
const lyrics = ref('')
const lyricsMessage = ref('暂未找到这首歌的歌词')
const lyricsLoading = ref(true)
const ADMIN_TOKEN_KEY = 'soundmind_admin_token'

const coverChar = computed(() => coverText(track.value.title || '?'))
const coverBg = computed(() => coverStyle(track.value.id, track.value.genre))

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/admin')
}

function formatDuration(ms) {
  if (!ms) return '-'
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${m}:${String(s).padStart(2, '0')}`
}

onMounted(async () => {
  const adminToken = sessionStorage.getItem(ADMIN_TOKEN_KEY)
  if (!adminToken) {
    router.replace('/admin')
    return
  }
  try {
    const authRes = await fetch('/api/admin/stats', { headers: { Authorization: 'Bearer ' + adminToken } })
    if (!authRes.ok) throw new Error('unauthorized')
  } catch {
    sessionStorage.removeItem(ADMIN_TOKEN_KEY)
    router.replace('/admin')
    return
  }
  const id = Number(route.params.id)
  window.scrollTo({ top: 0, left: 0 })
  try {
    track.value = await api.getTrack(id)
  } catch (e) {
    error.value = e.message || '歌曲不存在'
  } finally {
    loading.value = false
  }
  try {
    const data = await api.getTrackLyrics(id)
    lyrics.value = data.lyrics || ''
    lyricsMessage.value = data.message || lyricsMessage.value
  } catch (e) {
    lyricsMessage.value = e.message || '歌词加载失败'
  } finally {
    lyricsLoading.value = false
  }
})
</script>

<style scoped>
.admin-track-page { max-width: 1100px; }
.back-btn { background: none; border: none; color: var(--color-text-muted); font-size: 14px; cursor: pointer; padding: 8px 0; margin: 24px 0 16px; display: block; }
.back-btn:hover { color: var(--color-primary-light); }
.admin-track-hero { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 28px; align-items: start; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 18px; padding: 22px; }
.admin-track-cover { width: 260px; aspect-ratio: 1; border-radius: 18px; display: flex; align-items: center; justify-content: center; overflow: hidden; box-shadow: 0 18px 60px rgba(0,0,0,.28); }
.admin-track-cover img { width: 100%; height: 100%; object-fit: cover; }
.admin-track-cover span { font-size: 82px; font-weight: 900; color: rgba(255,255,255,.45); }
.eyebrow { font-size: 12px; color: var(--color-accent); font-weight: 800; margin-bottom: 8px; }
.admin-track-info h1 { font-size: 28px; line-height: 1.2; margin: 0; }
.artist { color: var(--color-text-muted); font-size: 17px; margin-top: 8px; }
.meta-grid, .resource-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 18px; }
.meta-grid div, .resource-grid div { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: 12px; padding: 12px; min-width: 0; }
.meta-grid span, .resource-grid span { display: block; font-size: 11px; color: var(--color-text-muted); margin-bottom: 5px; }
.meta-grid strong, .resource-grid strong { display: block; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.resource-grid .ok strong { color: var(--color-like); }
.resource-grid .muted strong { color: var(--color-text-muted); }
.admin-track-section { margin-top: 24px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 18px; padding: 18px; }
.admin-track-section h2 { font-size: 17px; margin-bottom: 12px; }
.lyrics-box { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: 12px; padding: 16px; max-height: 420px; overflow: auto; white-space: pre-wrap; line-height: 1.8; font-size: 14px; color: var(--color-text); }
.lyrics-box.muted { color: var(--color-text-muted); }
@media (max-width: 760px) {
  .admin-track-hero { grid-template-columns: 1fr; }
  .admin-track-cover { width: 100%; max-width: 260px; }
}
</style>
