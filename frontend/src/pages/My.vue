<template>
  <div class="container">
    <div class="page-header">
      <h1>我的音乐</h1>
      <p v-if="user">{{ user.display_name || user.username }}</p>
    </div>

    <div class="tabs">
      <button v-for="item in tabs" :key="item.id" :class="{ active: tab === item.id }" @click="tab = item.id">
        {{ item.icon }} {{ item.label }}
      </button>
    </div>

    <div v-if="tab === 'favs'">
      <div v-if="favsLoading" class="spinner"></div>
      <TrackList v-else-if="favs.length" :items="favs" />
      <div v-else class="empty-hint">还没有收藏歌曲</div>
    </div>

    <div v-if="tab === 'likes'">
      <div v-if="likesLoading" class="spinner"></div>
      <TrackList v-else-if="likes.length" :items="likes" />
      <div v-else class="empty-hint">还没有足够的喜欢记录</div>
    </div>

    <div v-if="tab === 'history'">
      <div v-if="histLoading" class="spinner"></div>
      <div v-else-if="history.length" class="history-list">
        <div v-for="h in history" :key="h.id" class="history-row">
          <router-link :to="'/track/' + h.track_id" class="hlink">
            <span class="h-time">{{ fmtDate(h.listened_at) }}</span>
            <span class="h-title">{{ h.track_title }}</span>
            <span class="h-artist">{{ h.artist_name }}</span>
            <span class="h-genre">{{ h.genre }}</span>
          </router-link>
        </div>
      </div>
      <div v-else class="empty-hint">暂无听歌记录</div>
    </div>

    <div v-if="tab === 'playlists'">
      <div class="pl-actions">
        <input v-model="newPlName" placeholder="新建歌单名称..." class="pl-input" @keyup.enter="createPlaylist" />
        <button class="btn btn-primary btn-sm" @click="createPlaylist" :disabled="!newPlName.trim() || plLoading">创建</button>
      </div>
      <p v-if="plMsg" class="save-msg" :class="plOk ? 'success' : 'error'">{{ plMsg }}</p>
      <div v-if="plLoading" class="spinner"></div>
      <div v-else-if="playlists.length" class="pl-grid">
        <div v-for="pl in playlists" :key="pl.id" class="pl-card">
          <div class="pl-link">
            <span class="pl-icon">♪</span>
            <div class="pl-info">
              <span class="pl-name">{{ pl.name }}</span>
              <span class="pl-meta">{{ pl.description || '暂无描述' }} · {{ pl.created_at?.slice(0, 10) }}</span>
            </div>
          </div>
          <button class="pl-del" @click="deletePl(pl.id)" title="删除">删除</button>
        </div>
      </div>
      <div v-else class="empty-hint">还没有自建歌单</div>
    </div>

    <div v-if="tab === 'profile'">
      <div v-if="profileLoading" class="spinner"></div>
      <div v-else-if="profile" class="profile-card">
        <div class="profile-avatar">
          <img v-if="avatarPreview" :src="avatarPreview" alt="头像" />
          <span v-else>{{ (profile.display_name || profile.username || '?').charAt(0) }}</span>
        </div>
        <h2>{{ profile.display_name || profile.username }}</h2>
        <p class="profile-username">@{{ profile.username }}</p>
        <div class="profile-stats">
          <div class="pstat"><span class="psv">{{ stats?.total_listens || 0 }}</span><span class="psl">播放</span></div>
          <div class="pstat"><span class="psv">{{ stats?.top_genre || '-' }}</span><span class="psl">最爱流派</span></div>
          <div class="pstat"><span class="psv">{{ stats?.top_artist || '-' }}</span><span class="psl">最爱艺人</span></div>
        </div>
        <div class="profile-form">
          <label>头像</label>
          <input type="file" accept="image/*" @change="onAvatarSelected" />
          <label>显示名称</label>
          <input v-model="editName" placeholder="输入显示名称" />
          <label>偏好流派</label>
          <input v-model="editGenres" placeholder="流行, 摇滚, 电子" />
          <button class="btn btn-primary" @click="saveProfile" :disabled="saving">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
          <p v-if="saveMsg" class="save-msg" :class="saveOk ? 'success' : 'error'">{{ saveMsg }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../api.js'
import { auth } from '../auth.js'
import TrackList from '../components/TrackList.vue'

const tab = ref('favs')
const user = ref(null)
const tabs = [
  { id: 'favs', label: '收藏', icon: '★' },
  { id: 'likes', label: '喜欢', icon: '✓' },
  { id: 'history', label: '历史', icon: '⌚' },
  { id: 'playlists', label: '歌单', icon: '♪' },
  { id: 'profile', label: '资料', icon: '◎' },
]

function getUid() { return auth.userId || Number(localStorage.getItem('user_id')) || 1 }
function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const favs = ref([])
const favsLoading = ref(false)
async function loadFavs() {
  favsLoading.value = true
  try {
    const d = await api.getFavorites(getUid())
    favs.value = d.items || []
  } finally {
    favsLoading.value = false
  }
}

const likes = ref([])
const likesLoading = ref(false)
async function loadLikes() {
  likesLoading.value = true
  try {
    const d = await api.getLikedTracks(getUid())
    likes.value = d.items || []
  } finally {
    likesLoading.value = false
  }
}

const history = ref([])
const histLoading = ref(false)
async function loadHistory() {
  histLoading.value = true
  try {
    const d = await api.getUserHistory(getUid(), 100)
    history.value = d.items || []
  } finally {
    histLoading.value = false
  }
}

const playlists = ref([])
const plLoading = ref(false)
const newPlName = ref('')
const plMsg = ref('')
const plOk = ref(false)
async function loadPlaylists() {
  plLoading.value = true
  try {
    const d = await api.getUserCreatedPlaylists(getUid())
    playlists.value = d.items || []
  } finally {
    plLoading.value = false
  }
}
async function createPlaylist() {
  if (!newPlName.value.trim()) return
  plLoading.value = true
  plMsg.value = ''
  try {
    await api.createUserPlaylist(getUid(), newPlName.value.trim())
    newPlName.value = ''
    plMsg.value = '歌单创建成功'
    plOk.value = true
    await loadPlaylists()
  } catch (e) {
    plMsg.value = e.message || '歌单创建失败'
    plOk.value = false
  } finally {
    plLoading.value = false
  }
}
async function deletePl(id) {
  if (!confirm('确定删除这个歌单？')) return
  await api.deleteUserPlaylist(id)
  loadPlaylists()
}

const profile = ref(null)
const stats = ref(null)
const profileLoading = ref(false)
const editName = ref('')
const editGenres = ref('')
const avatarPreview = ref('')
const saving = ref(false)
const saveMsg = ref('')
const saveOk = ref(false)
async function loadProfile() {
  profileLoading.value = true
  try {
    const d = await api.getUser(getUid())
    profile.value = d.user
    user.value = d.user
    stats.value = d.stats
    editName.value = d.user?.display_name || ''
    editGenres.value = d.user?.preferred_genres || ''
    avatarPreview.value = d.user?.avatar_url || ''
  } finally {
    profileLoading.value = false
  }
}
function onAvatarSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    saveMsg.value = '请选择图片文件'
    saveOk.value = false
    return
  }
  if (file.size > 800 * 1024) {
    saveMsg.value = '头像图片不能超过 800KB'
    saveOk.value = false
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    avatarPreview.value = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}
async function saveProfile() {
  saving.value = true
  saveMsg.value = ''
  try {
    await api.updateProfile(getUid(), { display_name: editName.value, preferred_genres: editGenres.value, avatar_url: avatarPreview.value })
    auth.username = editName.value || profile.value?.username
    localStorage.setItem('username', auth.username)
    saveMsg.value = '保存成功'
    saveOk.value = true
    loadProfile()
  } catch (e) {
    saveMsg.value = e.message
    saveOk.value = false
  } finally {
    saving.value = false
  }
}

watch(tab, (current) => {
  if (current === 'favs' && !favs.value.length) loadFavs()
  else if (current === 'likes' && !likes.value.length) loadLikes()
  else if (current === 'history' && !history.value.length) loadHistory()
  else if (current === 'playlists' && !playlists.value.length) loadPlaylists()
  else if (current === 'profile' && !profile.value) loadProfile()
}, { immediate: true })
</script>

<style scoped>
.tabs { display: flex; gap: 4px; margin-bottom: 24px; flex-wrap: wrap; }
.tabs button { padding: 8px 18px; border: none; border-radius: var(--radius); font-size: 13px; font-weight: 600; background: var(--color-surface); color: var(--color-text-muted); cursor: pointer; transition: all .2s; }
.tabs button.active { background: var(--color-primary); color: white; }
.pl-actions { display: flex; gap: 8px; margin-bottom: 16px; }
.pl-input { flex: 1; max-width: 300px; }
.pl-grid { display: flex; flex-direction: column; gap: 4px; }
.pl-card { background: var(--color-surface); border-radius: var(--radius); padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; }
.pl-link { display: flex; align-items: center; gap: 12px; color: inherit; flex: 1; }
.pl-icon { font-size: 24px; color: var(--color-primary-light); }
.pl-info { display: flex; flex-direction: column; }
.pl-name { font-size: 15px; font-weight: 600; }
.pl-meta { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; }
.pl-del { background: none; border: none; color: var(--color-text-muted); font-size: 12px; cursor: pointer; padding: 4px 8px; border-radius: 4px; }
.pl-del:hover { color: var(--color-dislike); background: rgba(225,112,85,0.1); }
.history-list { display: flex; flex-direction: column; gap: 2px; }
.history-row { background: var(--color-surface); border-radius: var(--radius); padding: 10px 14px; }
.hlink { display: flex; align-items: center; gap: 16px; text-decoration: none; color: inherit; }
.h-time { font-size: 12px; color: var(--color-text-muted); min-width: 90px; }
.h-title { font-size: 14px; font-weight: 500; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.h-artist, .h-genre { font-size: 13px; color: var(--color-text-muted); }
.profile-card { max-width: 420px; }
.profile-avatar { width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 800; color: white; margin-bottom: 12px; overflow: hidden; }
.profile-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
.profile-card h2 { font-size: 20px; }
.profile-username { font-size: 13px; color: var(--color-text-muted); margin-top: 2px; }
.profile-stats { display: flex; gap: 20px; margin: 16px 0; }
.pstat { display: flex; flex-direction: column; align-items: center; }
.psv { font-size: 20px; font-weight: 700; color: var(--color-primary-light); }
.psl { font-size: 11px; color: var(--color-text-muted); }
.profile-form { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.profile-form label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); }
.profile-form input { width: 100%; }
.save-msg { font-size: 13px; margin-top: 4px; }
.save-msg.success { color: var(--color-like); }
.save-msg.error { color: var(--color-dislike); }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 40px 0; font-size: 14px; }
</style>
