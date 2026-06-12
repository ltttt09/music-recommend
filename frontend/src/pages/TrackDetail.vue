<template>
  <div class="container">
    <div v-if="loading" class="spinner"></div>
    <div v-else-if="error" class="error-state">
      <h2>加载失败</h2>
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="goBack">返回首页</button>
    </div>
    <template v-else>
      <button class="back-btn" @click="goBack">&larr; 返回</button>
      <div class="track-hero">
        <div class="hero-cover">
          <img
            v-if="track.image_url && !imgFailed"
            :src="track.image_url"
            :alt="track.title"
            class="hero-img"
            referrerpolicy="no-referrer"
            @error="imgFailed = true"
          />
          <div v-if="!track.image_url || imgFailed" class="hero-fallback" :style="coverStyle(track.id, track.genre)">
            <span class="hero-letter">{{ heroCoverChar }}</span>
          </div>
          <button class="hero-play-btn" @click="play(track)">
            <span v-if="isCurrentPlaying">&#10074;&#10074;</span>
            <span v-else>&#9654;</span>
          </button>
        </div>

        <div class="hero-info">
          <h1>{{ track.title }}</h1>
          <p class="hero-artist">{{ track.artist_name }}</p>
          <div class="hero-meta">
            <span v-if="track.album" class="tag">{{ track.album }}</span>
            <span v-if="track.year" class="tag">{{ track.year }}</span>
            <span v-if="track.genre" class="tag">{{ track.genre }}</span>
            <span v-if="track.duration_ms">{{ formatDuration(track.duration_ms) }}</span>
          </div>
          <div class="hero-actions">
            <button class="btn btn-like btn-sm" :class="{ active: liked }" @click="feedback(1)">
              {{ liked ? '已喜欢' : '喜欢' }}
            </button>
            <button class="btn btn-dislike btn-sm" :class="{ active: skipped }" @click="feedback(-1)">
              {{ skipped ? '已跳过' : '跳过' }}
            </button>
            <button class="btn btn-sm" :class="favorited ? 'btn-fav-active' : 'btn-ghost'" @click="toggleFav">
              {{ favorited ? '已收藏' : '收藏' }}
            </button>
            <button class="btn btn-ghost btn-sm" @click="shareLink">分享</button>
            <button class="btn btn-primary btn-sm" @click="generatePlaylist" :disabled="playlistLoading">
              {{ playlistLoading ? '生成中...' : '生成歌单' }}
            </button>
          </div>
          <p v-if="toast" class="toast" :class="toastType">{{ toast }}</p>
        </div>
      </div>

      <div class="section">
        <h2>相似歌曲</h2>
        <div v-if="similarLoading" class="spinner"></div>
        <TrackList v-else :items="similarTracks" />
      </div>

      <div class="section">
        <h2>评论 ({{ comments.length }})</h2>
        <div class="comment-form">
          <input v-model="commentText" placeholder="写下你的评论..." maxlength="500" @keyup.enter="submitComment" />
          <button class="btn btn-primary btn-sm" @click="submitComment" :disabled="!commentText.trim()">发表</button>
        </div>
        <div v-if="comments.length" class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <span class="comment-user">{{ c.display_name || c.username }}</span>
            <span class="comment-time">{{ fmtDate(c.created_at) }}</span>
            <p class="comment-body">{{ c.content }}</p>
          </div>
        </div>
        <div v-else class="empty-hint">暂无评论</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'
import { pauseTrack, playerState, playTrack } from '../audio.js'
import TrackList from '../components/TrackList.vue'
import { coverStyle, coverText } from '../cover.js'

const route = useRoute()
const router = useRouter()
const track = ref({})
const similarTracks = ref([])
const loading = ref(true)
const similarLoading = ref(true)
const error = ref('')
const imgFailed = ref(false)
const playlistLoading = ref(false)
const toast = ref('')
const toastType = ref('success')
const favorited = ref(false)
const liked = ref(false)
const skipped = ref(false)
const mutedUntil = ref('')
const comments = ref([])
const commentText = ref('')

function getUserId() { return Number(localStorage.getItem('user_id')) || 1 }
function showToast(message, type = 'success') {
  toast.value = message
  toastType.value = type
  setTimeout(() => { toast.value = '' }, 2000)
}
function shareLink() {
  navigator.clipboard?.writeText(window.location.href)
  showToast('链接已复制')
}
function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function toggleFav() {
  try {
    const d = await api.toggleFavorite(Number(route.params.id))
    favorited.value = d.favorited
    showToast(d.favorited ? '已收藏' : '已取消收藏')
  } catch (e) {
    showToast(e.message || '操作失败', 'error')
  }
}

async function loadComments() {
  try {
    const d = await api.getComments(Number(route.params.id))
    comments.value = d.items || []
  } catch {}
}

async function submitComment() {
  if (!commentText.value.trim()) return
  try {
    await api.addComment(Number(route.params.id), getUserId(), commentText.value.trim())
    commentText.value = ''
    loadComments()
  } catch (e) {
    showToast(e.message || '评论失败', 'error')
  }
}

const heroCoverChar = computed(() => coverText(track.value.title || '?'))
const isCurrentPlaying = computed(() =>
  playerState.currentTrack?.id === Number(route.params.id) && playerState.isPlaying
)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}
function play(t) {
  if (!t.preview_url) {
    showToast('这首歌缺少可播放试听地址', 'error')
    return
  }
  playTrack({
    id: t.id || t.track_id,
    title: t.title,
    artist_name: t.artist_name,
    image_url: t.image_url,
    preview_url: t.preview_url,
  })
}
function formatDuration(ms) {
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${m}:${String(s).padStart(2, '0')}`
}
async function feedback(rating) {
  if (rating < 0) {
    const ok = confirm('确定跳过这首歌？系统会在一段时间内减少推荐它，反复跳过会延长屏蔽时间。')
    if (!ok) return
  }
  try {
    const id = Number(route.params.id)
    await api.submitFeedback(getUserId(), id, rating)
    if (rating > 0) {
      liked.value = true
      showToast('已标记为喜欢')
      return
    }
    skipped.value = true
    if (playerState.currentTrack?.id === id) pauseTrack()
    showToast('已跳过，短期内不会再推荐')
    setTimeout(goBack, 500)
  } catch (e) {
    showToast(e.message || '操作失败', 'error')
  }
}
async function generatePlaylist() {
  playlistLoading.value = true
  try {
    const d = await api.generatePlaylist(Number(route.params.id))
    if (d.error) throw new Error(d.error)
    showToast('歌单已生成')
    setTimeout(() => { router.push('/playlist/' + d.playlist_id) }, 600)
  } catch (e) {
    showToast(e.message || '生成歌单失败', 'error')
  } finally {
    playlistLoading.value = false
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    track.value = await api.getTrack(id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
  try {
    const d = await api.getSimilarTracks(id)
    similarTracks.value = d.items || []
  } finally {
    similarLoading.value = false
  }
  try {
    const d = await api.checkFavorite(id, getUserId())
    favorited.value = d.favorited
  } catch {}
  try {
    const d = await api.getTrackState(id, getUserId())
    favorited.value = d.favorited
    liked.value = d.liked
    skipped.value = d.skipped
    mutedUntil.value = d.muted_until || ''
  } catch {}
  loadComments()
})
</script>

<style scoped>
.back-btn { background: none; border: none; color: var(--color-text-muted); font-size: 14px; cursor: pointer; padding: 8px 0; margin: 24px 0 16px; display: block; }
.back-btn:hover { color: var(--color-text); }
.track-hero { display: flex; align-items: flex-start; gap: 32px; margin-bottom: 40px; }
.hero-cover { width: 240px; height: 240px; border-radius: 18px; flex-shrink: 0; position: relative; overflow: hidden; box-shadow: 0 12px 48px rgba(0,0,0,0.5); }
.hero-img { width: 100%; height: 100%; object-fit: cover; }
.hero-fallback { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.hero-letter { font-size: 80px; font-weight: 900; font-family: Arial, "Microsoft YaHei", sans-serif; color: rgba(255,255,255,0.35); line-height: 1; }
.hero-play-btn { position: absolute; bottom: 16px; right: 16px; width: 52px; height: 52px; border-radius: 50%; border: none; background: var(--color-primary); color: white; font-size: 20px; cursor: pointer; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.hero-play-btn:hover { background: var(--color-primary-light); transform: scale(1.08); }
.hero-info h1 { font-size: 30px; font-weight: 700; line-height: 1.2; }
.hero-artist { color: var(--color-text-muted); font-size: 18px; margin-top: 8px; }
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; font-size: 13px; color: var(--color-text-muted); }
.tag { padding: 4px 10px; border-radius: 6px; background: var(--color-bg); font-size: 12px; }
.hero-actions { display: flex; gap: 8px; margin-top: 18px; flex-wrap: wrap; }
.toast { margin-top: 10px; font-size: 13px; }
.toast.success { color: var(--color-like); }
.toast.error { color: var(--color-dislike); }
.section { margin-top: 32px; }
.section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.btn-fav-active { background: #fdcb6e; color: #2d3436; }
.btn-like.active { box-shadow: 0 0 0 2px rgba(0,184,148,.25); filter: brightness(1.08); }
.btn-dislike.active { box-shadow: 0 0 0 2px rgba(225,112,85,.25); filter: brightness(1.08); }
.comment-form { display: flex; gap: 8px; margin-bottom: 16px; }
.comment-form input { flex: 1; }
.comment-list { display: flex; flex-direction: column; gap: 2px; }
.comment-item { background: var(--color-surface); border-radius: var(--radius); padding: 12px 16px; }
.comment-user { font-size: 13px; font-weight: 600; color: var(--color-primary-light); }
.comment-time { font-size: 11px; color: var(--color-text-muted); margin-left: 8px; }
.comment-body { margin-top: 6px; font-size: 14px; line-height: 1.5; color: var(--color-text); }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 24px 0; font-size: 13px; }
@media (max-width: 768px) {
  .track-hero { flex-direction: column; align-items: center; text-align: center; }
  .hero-cover { width: 200px; height: 200px; }
  .hero-actions { justify-content: center; }
}
</style>
