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
            <button class="btn btn-like btn-sm" :class="{ active: liked }" :disabled="feedbackLoading" @click="feedback(1)">
              {{ feedbackLoading ? '处理中...' : (liked ? '已喜欢' : '喜欢') }}
            </button>
            <button class="btn btn-dislike btn-sm" :class="{ active: skipped }" :disabled="feedbackLoading" @click="feedback(-1)">
              {{ skipped ? '已在黑名单' : '移入黑名单' }}
            </button>
            <button class="btn btn-ghost btn-sm" @click="playlistOpen = true">加入歌单</button>
            <button class="btn btn-ghost btn-sm" @click="shareLink">分享</button>
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
        <h2>歌词</h2>
        <div v-if="lyricsLoading" class="lyrics-box muted">歌词加载中...</div>
        <pre v-else-if="lyrics" class="lyrics-box">{{ lyrics }}</pre>
        <div v-else class="lyrics-box muted">{{ lyricsMessage }}</div>
      </div>

      <div class="section">
        <h2>评论 ({{ commentsTotal }})</h2>
        <div class="comment-form">
          <input v-model="commentText" placeholder="写下你的评论..." maxlength="500" @keyup.enter="submitComment" />
          <button class="btn btn-primary btn-sm" @click="submitComment" :disabled="!commentText.trim() || commentLoading">
            {{ commentLoading ? '发表中...' : '发表' }}
          </button>
        </div>
        <div v-if="commentsLoading" class="spinner"></div>
        <div v-else-if="comments.length" class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-head">
              <span class="comment-avatar">
                <img v-if="c.avatar_url" :src="c.avatar_url" alt="" />
                <b v-else>{{ (c.display_name || c.username || '?').charAt(0) }}</b>
              </span>
              <div>
                <span class="comment-user">{{ c.display_name || c.username }}</span>
                <span class="comment-time">{{ fmtDate(c.created_at) }}</span>
              </div>
            </div>
            <p class="comment-body">{{ c.content }}</p>
            <div class="comment-actions">
              <button :class="{ active: c.liked_by_me }" @click="toggleCommentLike(c)">赞 {{ c.like_count || 0 }}</button>
              <button @click="openReply(c, c)">{{ replyTarget === c.id ? '收起' : '回复' }}</button>
              <button v-if="c.can_delete" @click="deleteComment(c)">删除</button>
            </div>
            <div v-if="replyTarget === c.id" class="reply-form">
              <input v-model="replyText" placeholder="回复评论..." maxlength="500" @keyup.enter="submitReply(c)" />
              <button class="btn btn-primary btn-sm" :disabled="!replyText.trim() || commentLoading" @click="submitReply(c)">回复</button>
            </div>
            <div v-if="c.replies?.length" class="reply-list">
              <div v-for="r in visibleReplies(c)" :key="r.id" class="reply-item">
                <div class="comment-head">
                  <span class="comment-avatar small">
                    <img v-if="r.avatar_url" :src="r.avatar_url" alt="" />
                    <b v-else>{{ (r.display_name || r.username || '?').charAt(0) }}</b>
                  </span>
                  <div>
                    <span class="comment-user">{{ r.display_name || r.username }}</span>
                    <span class="comment-time">{{ fmtDate(r.created_at) }}</span>
                  </div>
                </div>
                <p class="comment-body">{{ r.content }}</p>
                <div class="comment-actions">
                  <button :class="{ active: r.liked_by_me }" @click="toggleCommentLike(r)">赞 {{ r.like_count || 0 }}</button>
                  <button @click="openReply(c, r)">回复</button>
                  <button v-if="r.can_delete" @click="deleteComment(r)">删除</button>
                </div>
              </div>
              <button v-if="c.replies.length > 2" class="reply-toggle" @click="toggleReplies(c.id)">
                {{ expandedReplies.has(c.id) ? '收起回复' : `展开全部 ${c.replies.length} 条回复` }}
              </button>
            </div>
          </div>
          <div class="pager">
            <button class="btn btn-ghost btn-sm" :disabled="commentsPage <= 1" @click="loadComments(commentsPage - 1)">上一页</button>
            <span>{{ commentsPage }} / {{ commentsPages }}</span>
            <button class="btn btn-ghost btn-sm" :disabled="commentsPage >= commentsPages" @click="loadComments(commentsPage + 1)">下一页</button>
          </div>
        </div>
        <div v-else class="empty-hint">暂无评论</div>
      </div>
    </template>
    <AddToPlaylistModal v-if="playlistOpen" :track-ids="[Number(route.params.id)]" @close="playlistOpen = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'
import { auth } from '../auth.js'
import { pauseTrack, playerState, playTrack } from '../audio.js'
import TrackList from '../components/TrackList.vue'
import AddToPlaylistModal from '../components/AddToPlaylistModal.vue'
import { coverStyle, coverText } from '../cover.js'

const route = useRoute()
const router = useRouter()
const track = ref({})
const similarTracks = ref([])
const loading = ref(true)
const similarLoading = ref(true)
const error = ref('')
const imgFailed = ref(false)
const toast = ref('')
const toastType = ref('success')
const liked = ref(false)
const skipped = ref(false)
const feedbackLoading = ref(false)
const mutedUntil = ref('')
const comments = ref([])
const commentsTotal = ref(0)
const commentsPage = ref(1)
const commentsSize = 10
const commentsLoading = ref(false)
const commentText = ref('')
const commentLoading = ref(false)
const replyTarget = ref(0)
const replyParentId = ref(0)
const replyText = ref('')
const expandedReplies = ref(new Set())
const lyrics = ref('')
const lyricsMessage = ref('暂未找到这首歌的歌词')
const lyricsLoading = ref(true)
const playlistOpen = ref(false)

function getUserId() { return auth.userId || Number(localStorage.getItem('user_id')) || 0 }
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

async function loadComments(nextPage = commentsPage.value) {
  commentsPage.value = Math.max(1, nextPage)
  commentsLoading.value = true
  try {
    const d = await api.getComments(Number(route.params.id), commentsPage.value, commentsSize)
    comments.value = d.items || []
    commentsTotal.value = d.total || 0
  } catch (e) {
    showToast(e.message || '评论加载失败', 'error')
  } finally {
    commentsLoading.value = false
  }
}
const commentsPages = computed(() => Math.max(1, Math.ceil((commentsTotal.value || 0) / commentsSize)))

async function submitComment() {
  if (!commentText.value.trim()) return
  if (!getUserId()) {
    showToast('请先登录后评论', 'error')
    return
  }
  commentLoading.value = true
  try {
    const created = await api.addComment(Number(route.params.id), commentText.value.trim())
    comments.value = created?.id ? [created, ...comments.value] : comments.value
    commentText.value = ''
    if (!created?.id) await loadComments()
  } catch (e) {
    showToast(e.message || '评论失败', 'error')
  } finally {
    commentLoading.value = false
  }
}

function openReply(root, target) {
  if (!getUserId()) {
    showToast('请先登录后回复', 'error')
    return
  }
  if (replyTarget.value === root.id && replyParentId.value === target.id) {
    replyTarget.value = 0
    replyParentId.value = 0
    return
  }
  replyTarget.value = root.id
  replyParentId.value = target.id
  replyText.value = target.id === root.id ? '' : `回复 @${target.display_name || target.username || '用户'}：`
}

function visibleReplies(comment) {
  return expandedReplies.value.has(comment.id) ? comment.replies : comment.replies.slice(0, 2)
}

function toggleReplies(commentId) {
  const next = new Set(expandedReplies.value)
  next.has(commentId) ? next.delete(commentId) : next.add(commentId)
  expandedReplies.value = next
}

async function submitReply(comment) {
  if (!replyText.value.trim()) return
  commentLoading.value = true
  try {
    const created = await api.addComment(Number(route.params.id), replyText.value.trim(), replyParentId.value || comment.id)
    comment.replies = [...(comment.replies || []), created]
    expandedReplies.value = new Set([...expandedReplies.value, comment.id])
    replyText.value = ''
    replyTarget.value = 0
    replyParentId.value = 0
  } catch (e) {
    showToast(e.message || '回复失败', 'error')
  } finally {
    commentLoading.value = false
  }
}

async function toggleCommentLike(comment) {
  if (!getUserId()) {
    showToast('请先登录后点赞', 'error')
    return
  }
  try {
    const data = await api.toggleCommentLike(comment.id)
    comment.liked_by_me = data.liked
    comment.like_count = data.like_count
  } catch (e) {
    showToast(e.message || '点赞失败', 'error')
  }
}

async function deleteComment(comment) {
  if (!confirm('确定删除这条评论？')) return
  try {
    await api.deleteOwnComment(comment.id)
    await loadComments()
  } catch (e) {
    showToast(e.message || '删除失败', 'error')
  }
}

async function loadLyrics(id) {
  lyricsLoading.value = true
  try {
    const data = await api.getTrackLyrics(id)
    lyrics.value = data.lyrics || ''
    lyricsMessage.value = data.message || '暂未找到这首歌的歌词'
  } catch (e) {
    lyricsMessage.value = e.message || '歌词加载失败'
  } finally {
    lyricsLoading.value = false
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
  if (feedbackLoading.value) return
  const uid = getUserId()
  if (!uid) {
    showToast('请先登录', 'error')
    return
  }
  if (rating < 0) {
    const ok = confirm('确定将这首歌移入黑名单？移入后会从喜欢列表移除，并在一段时间内不再推荐。')
    if (!ok) return
  }
  try {
    feedbackLoading.value = true
    const id = Number(route.params.id)
    const state = await api.submitFeedback(uid, id, rating)
    if (rating > 0) {
      liked.value = Boolean(state.liked)
      skipped.value = Boolean(state.skipped)
      showToast(liked.value ? '已标记为喜欢' : '已取消喜欢')
      window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'likes' } }))
      return
    }
    liked.value = Boolean(state.liked)
    skipped.value = Boolean(state.skipped)
    mutedUntil.value = state.muted_until || ''
    if (playerState.currentTrack?.id === id) pauseTrack()
    showToast('已移入黑名单，并已从喜欢列表移除')
    window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'blacklist' } }))
    setTimeout(goBack, 500)
  } catch (e) {
    showToast(e.message || '操作失败', 'error')
  } finally {
    feedbackLoading.value = false
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
  loadLyrics(id)
  try {
    const d = await api.getTrackState(id, getUserId())
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
.btn-like.active { box-shadow: 0 0 0 2px rgba(0,184,148,.25); filter: brightness(1.08); }
.btn-dislike.active { box-shadow: 0 0 0 2px rgba(225,112,85,.25); filter: brightness(1.08); }
.comment-form { display: flex; gap: 8px; margin-bottom: 16px; }
.comment-form input { flex: 1; }
.comment-list { display: flex; flex-direction: column; gap: 2px; }
.comment-item { background: var(--color-surface); border-radius: var(--radius); padding: 12px 16px; }
.comment-head { display: flex; align-items: center; gap: 10px; }
.comment-avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--color-bg); color: var(--color-primary-light); display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0; }
.comment-avatar.small { width: 28px; height: 28px; font-size: 12px; }
.comment-avatar img { width: 100%; height: 100%; object-fit: cover; }
.comment-user { font-size: 13px; font-weight: 600; color: var(--color-primary-light); }
.comment-time { font-size: 11px; color: var(--color-text-muted); margin-left: 8px; }
.comment-body { margin-top: 6px; font-size: 14px; line-height: 1.5; color: var(--color-text); }
.comment-actions { display: flex; gap: 8px; margin-top: 8px; }
.comment-actions button { background: none; border: none; color: var(--color-text-muted); cursor: pointer; font-size: 12px; padding: 3px 6px; border-radius: 4px; }
.comment-actions button:hover, .comment-actions button.active { color: var(--color-primary-light); background: var(--color-bg); }
.reply-form { display: flex; gap: 8px; margin-top: 10px; }
.reply-form input { flex: 1; }
.reply-list { margin-top: 10px; padding-left: 42px; display: flex; flex-direction: column; gap: 8px; }
.reply-item { background: var(--color-bg); border-radius: var(--radius); padding: 10px 12px; }
.reply-toggle { margin-top: 8px; background: none; border: none; color: var(--color-primary-light); cursor: pointer; font-size: 12px; padding: 4px 0; }
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin: 18px 0 4px; color: var(--color-text-muted); font-size: 13px; }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 24px 0; font-size: 13px; }
.lyrics-box { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 16px; max-height: 360px; overflow: auto; white-space: pre-wrap; line-height: 1.8; font-size: 14px; color: var(--color-text); }
.lyrics-box.muted { color: var(--color-text-muted); }
@media (max-width: 768px) {
  .track-hero { flex-direction: column; align-items: center; text-align: center; }
  .hero-cover { width: 200px; height: 200px; }
  .hero-actions { justify-content: center; }
}
</style>
