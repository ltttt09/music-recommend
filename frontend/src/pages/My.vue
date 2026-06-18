<template>
  <div class="container">
    <div class="page-header">
      <h1>我的音乐</h1>
      <p v-if="user">{{ user.display_name || user.username }}</p>
    </div>

    <div class="tabs">
      <button v-for="item in tabs" :key="item.id" :class="{ active: tab === item.id }" @click="setTab(item.id)">
        {{ item.icon }} {{ item.label }}
      </button>
    </div>

    <div v-if="tab === 'likes'">
      <div v-if="likesLoading" class="spinner"></div>
      <template v-else-if="likes.length">
        <TrackList :items="pagedLikes" show-unlike @unlike="unlikeTrack" />
        <div class="pager"><button class="btn btn-ghost btn-sm" :disabled="likesPage<=1" @click="likesPage--">上一页</button><span>{{ likesPage }} / {{ likesPages }}</span><button class="btn btn-ghost btn-sm" :disabled="likesPage>=likesPages" @click="likesPage++">下一页</button></div>
      </template>
      <div v-else class="empty-hint">还没有喜欢的歌曲</div>
    </div>

    <div v-if="tab === 'history'">
      <div v-if="histLoading" class="spinner"></div>
      <div v-else-if="history.length" class="history-list">
        <div v-for="h in pagedHistory" :key="h.id" class="history-row">
          <router-link :to="'/track/' + h.track_id" class="hlink">
            <span class="h-time">{{ fmtDate(h.listened_at) }}</span>
            <span class="h-title">{{ h.track_title }}</span>
            <span class="h-artist">{{ h.artist_name }}</span>
            <span class="h-genre">{{ h.genre }}</span>
          </router-link>
        </div>
        <div class="pager"><button class="btn btn-ghost btn-sm" :disabled="historyPage<=1" @click="historyPage--">上一页</button><span>{{ historyPage }} / {{ historyPages }}</span><button class="btn btn-ghost btn-sm" :disabled="historyPage>=historyPages" @click="historyPage++">下一页</button></div>
      </div>
      <div v-else class="empty-hint">暂无听歌记录</div>
    </div>

    <div v-if="tab === 'playlists'">
      <div class="pl-actions">
        <input v-model="newPlName" placeholder="新建歌单名称..." class="pl-input" @keyup.enter="createPlaylist" />
          <button class="btn btn-primary btn-sm" @click="createPlaylist" :disabled="!newPlName.trim() || plCreating">{{ plCreating ? '创建中...' : '创建' }}</button>
      </div>
      <p v-if="plMsg" class="save-msg" :class="plOk ? 'success' : 'error'">{{ plMsg }}</p>
      <div v-if="plLoading" class="spinner"></div>
      <div v-else-if="playlists.length" class="pl-grid">
        <div v-for="pl in playlists" :key="pl.id" class="pl-card">
          <router-link class="pl-link" :to="'/playlist/' + pl.id">
            <span class="pl-icon">♪</span>
            <div class="pl-info">
              <span class="pl-name">{{ pl.name }}</span>
              <span class="pl-meta">{{ pl.track_count || 0 }} 首 · {{ pl.created_at?.slice(0, 10) }}</span>
            </div>
          </router-link>
          <button class="pl-del" @click="deletePl(pl.id)" title="删除">删除</button>
        </div>
      </div>
      <div v-else class="empty-hint">还没有自建歌单</div>
      <div v-if="playlistsTotal > plSize" class="pager"><button class="btn btn-ghost btn-sm" :disabled="plPage<=1 || plLoading" @click="loadPlaylists(plPage-1)">上一页</button><span>{{ plPage }} / {{ plPages }}</span><button class="btn btn-ghost btn-sm" :disabled="plPage>=plPages || plLoading" @click="loadPlaylists(plPage+1)">下一页</button></div>
    </div>

    <div v-if="tab === 'blacklist'">
      <div v-if="blackLoading" class="spinner"></div>
      <div v-else-if="blacklist.length" class="black-list">
        <div v-for="track in blacklist" :key="track.id" class="pl-card">
          <div class="pl-link">
            <span class="pl-icon">⊘</span>
            <div class="pl-info">
              <span class="pl-name">{{ track.title }}</span>
              <span class="pl-meta">{{ track.artist_name }} · 屏蔽到 {{ track.muted_until || '-' }}</span>
            </div>
          </div>
          <button class="pl-del" @click="removeBlack(track.id)">移除</button>
        </div>
        <div class="pager"><button class="btn btn-ghost btn-sm" :disabled="blackPage<=1 || blackLoading" @click="loadBlacklist(blackPage-1)">上一页</button><span>{{ blackPage }} / {{ blackPages }}</span><button class="btn btn-ghost btn-sm" :disabled="blackPage>=blackPages || blackLoading" @click="loadBlacklist(blackPage+1)">下一页</button></div>
      </div>
      <div v-else class="empty-hint">黑名单为空。移入黑名单的歌曲会显示在这里。</div>
    </div>

    <div v-if="tab === 'profile'">
      <div v-if="profileLoading" class="spinner"></div>
      <div v-else-if="!getUid()" class="guest-card">
        <div class="guest-avatar">♪</div>
        <h2>登录后可查看个人资料</h2>
        <p>登录后可以管理头像、偏好流派、喜欢歌曲、歌单和推荐记录。</p>
        <div class="guest-actions">
          <router-link class="btn btn-primary btn-sm" to="/login">去登录</router-link>
          <router-link class="btn btn-ghost btn-sm" to="/browse">先随便看看</router-link>
          <router-link class="btn btn-ghost btn-sm" to="/">查看热门歌曲</router-link>
        </div>
      </div>
      <div v-else-if="profile" class="profile-card">
        <div class="profile-avatar" role="button" tabindex="0" @click="avatarMenuOpen = !avatarMenuOpen" @keydown.enter="avatarMenuOpen = !avatarMenuOpen">
          <img v-if="avatarPreview" :src="avatarPreview" alt="头像" />
          <span v-else>{{ (profile.display_name || profile.username || '?').charAt(0) }}</span>
        </div>
        <div v-if="avatarMenuOpen" class="avatar-actions">
          <label class="avatar-upload">上传头像<input type="file" accept="image/*" @change="onAvatarSelected" /></label>
          <button v-if="avatarPreview" class="btn btn-ghost btn-sm" @click="avatarPreview = ''">移除头像</button>
        </div>
        <h2>{{ profile.display_name || profile.username }}</h2>
        <p class="profile-username">@{{ profile.username }}</p>
        <div class="profile-stats">
          <div class="pstat"><span class="psv">{{ stats?.total_listens || 0 }}</span><span class="psl">播放</span></div>
          <div class="pstat"><span class="psv">{{ stats?.top_genre || '-' }}</span><span class="psl">最爱流派</span></div>
          <div class="pstat"><span class="psv">{{ stats?.top_artist || '-' }}</span><span class="psl">最爱艺人</span></div>
        </div>
        <div class="profile-form">
          <label>显示名称</label>
          <input v-model="editName" placeholder="输入显示名称" />
          <label>偏好流派</label>
          <div class="chip-list">
            <button v-for="genre in preferenceOptions" :key="genre" type="button" class="chip" :class="{ active: selectedGenres.has(genre) }" @click="toggleGenre(genre)">{{ genre }}</button>
          </div>
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
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'
import { auth } from '../auth.js'
import TrackList from '../components/TrackList.vue'
import { PREFERENCE_GENRES, parsePreferences, stringifyPreferences } from '../preferences.js'

const tab = ref('likes')
const route = useRoute()
const router = useRouter()
const user = ref(null)
const tabs = [
  { id: 'likes', label: '喜欢', icon: '✓' },
  { id: 'history', label: '历史', icon: '⌚' },
  { id: 'playlists', label: '歌单', icon: '♪' },
  { id: 'profile', label: '资料', icon: '◎' },
  { id: 'blacklist', label: '黑名单', icon: '⊘' },
]
const tabAliases = { favs: 'likes', favorites: 'likes', liked: 'likes', playlist: 'playlists', skipped: 'blacklist', preference: 'profile' }
tab.value = normalizeTab(route.query.tab)

function normalizeTab(value) {
  const raw = String(value || 'likes')
  const normalized = tabAliases[raw] || raw
  return tabs.some((item) => item.id === normalized) ? normalized : 'likes'
}

function setTab(next) {
  tab.value = normalizeTab(next)
  router.replace({ path: '/my', query: { ...route.query, tab: tab.value } })
}

function getUid() { return auth.userId || Number(localStorage.getItem('user_id')) || 0 }
function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const pageSize = 10
const likes = ref([])
const likesLoading = ref(false)
const likesPage = ref(1)
const pagedLikes = computed(() => likes.value.slice((likesPage.value - 1) * pageSize, likesPage.value * pageSize))
const likesPages = computed(() => Math.max(1, Math.ceil(likes.value.length / pageSize)))
async function loadLikes() {
  if (!getUid()) return
  likesLoading.value = true
  try {
    const d = await api.getLikedTracks(getUid())
    likes.value = d.items || []
  } finally {
    likesLoading.value = false
  }
}
async function unlikeTrack(track) {
  if (!getUid()) return
  if (!confirm('确定取消喜欢这首歌？')) return
  const id = track.id || track.track_id
  const prev = likes.value
  likes.value = likes.value.filter((item) => (item.id || item.track_id) !== id)
  try {
    await api.submitFeedback(getUid(), id, 1)
    window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'likes' } }))
  } catch (e) {
    likes.value = prev
    alert(e.message || '取消喜欢失败')
  }
}

const history = ref([])
const histLoading = ref(false)
const historyPage = ref(1)
const pagedHistory = computed(() => history.value.slice((historyPage.value - 1) * pageSize, historyPage.value * pageSize))
const historyPages = computed(() => Math.max(1, Math.ceil(history.value.length / pageSize)))
async function loadHistory() {
  if (!getUid()) return
  histLoading.value = true
  try {
    const d = await api.getUserHistory(getUid(), 200)
    history.value = d.items || []
  } finally {
    histLoading.value = false
  }
}

const playlists = ref([])
const plLoading = ref(false)
const plCreating = ref(false)
const newPlName = ref('')
const plMsg = ref('')
const plOk = ref(false)
const plPage = ref(1)
const plSize = 10
const playlistsTotal = ref(0)
const plPages = computed(() => Math.max(1, Math.ceil((playlistsTotal.value || 0) / plSize)))
async function loadPlaylists(nextPage = plPage.value) {
  if (!getUid()) return
  plLoading.value = true
  plPage.value = Math.max(1, nextPage)
  try {
    const d = await api.getUserCreatedPlaylists(getUid(), plPage.value, plSize)
    playlists.value = d.items || []
    playlistsTotal.value = d.total || 0
  } finally {
    plLoading.value = false
  }
}
async function createPlaylist() {
  const name = newPlName.value.trim()
  if (!name) {
    plMsg.value = '歌单名称不能为空'
    plOk.value = false
    return
  }
  if (name.length > 30) {
    plMsg.value = '歌单名称不能超过 30 个字符'
    plOk.value = false
    return
  }
  if (!getUid()) {
    plMsg.value = '请先登录后创建歌单'
    plOk.value = false
    return
  }
  plCreating.value = true
  plMsg.value = ''
  try {
    await api.createUserPlaylist(getUid(), name)
    newPlName.value = ''
    plMsg.value = '歌单创建成功'
    plOk.value = true
    await loadPlaylists(1)
  } catch (e) {
    plMsg.value = e.message || '歌单创建失败'
    plOk.value = false
  } finally {
    plCreating.value = false
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
const avatarPreview = ref('')
const avatarMenuOpen = ref(false)
const preferenceOptions = PREFERENCE_GENRES
const selectedGenres = ref(new Set())
const saving = ref(false)
const saveMsg = ref('')
const saveOk = ref(false)
async function loadProfile() {
  if (!getUid()) return
  profileLoading.value = true
  try {
    const d = await api.getUser(getUid())
    profile.value = d.user
    user.value = d.user
    stats.value = d.stats
    editName.value = d.user?.display_name || ''
    selectedGenres.value = parsePreferences(d.user?.preferred_genres || '')
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
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    saveMsg.value = '头像仅支持 JPG、PNG、WebP'
    saveOk.value = false
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    saveMsg.value = '头像图片不能超过 5MB'
    saveOk.value = false
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    avatarPreview.value = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}
function toggleGenre(genre) {
  const next = new Set(selectedGenres.value)
  next.has(genre) ? next.delete(genre) : next.add(genre)
  selectedGenres.value = next
}
async function saveProfile() {
  if (!getUid()) {
    saveMsg.value = '请先登录'
    saveOk.value = false
    return
  }
  saving.value = true
  saveMsg.value = ''
  try {
    await api.updateProfile(getUid(), { display_name: editName.value, preferred_genres: stringifyPreferences(selectedGenres.value), avatar_url: avatarPreview.value })
    auth.username = editName.value || profile.value?.username
    localStorage.setItem('username', auth.username)
    saveMsg.value = '保存成功'
    saveOk.value = true
    window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'preferences' } }))
    loadProfile()
  } catch (e) {
    saveMsg.value = e.message
    saveOk.value = false
  } finally {
    saving.value = false
  }
}

const blacklist = ref([])
const blackLoading = ref(false)
const blackPage = ref(1)
const blackSize = 10
const blackTotal = ref(0)
const blackPages = computed(() => Math.max(1, Math.ceil((blackTotal.value || 0) / blackSize)))
async function loadBlacklist(nextPage = blackPage.value) {
  if (!getUid()) return
  blackLoading.value = true
  blackPage.value = Math.max(1, nextPage)
  try {
    const d = await api.getBlacklist(getUid(), blackPage.value, blackSize)
    blacklist.value = d.items || []
    blackTotal.value = d.total || 0
  } finally {
    blackLoading.value = false
  }
}
async function removeBlack(trackId) {
  await api.removeFromBlacklist(getUid(), trackId)
  window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'blacklist' } }))
  await loadBlacklist(blackPage.value)
}

watch(tab, (current) => {
  if (current === 'likes' && !likes.value.length) loadLikes()
  else if (current === 'history' && !history.value.length) loadHistory()
  else if (current === 'playlists' && !playlists.value.length) loadPlaylists()
  else if (current === 'profile' && !profile.value) loadProfile()
  else if (current === 'blacklist' && !blacklist.value.length) loadBlacklist()
}, { immediate: true })

watch(() => route.query.tab, (next) => {
  const normalized = normalizeTab(next)
  if (normalized !== tab.value) tab.value = normalized
})
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
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin: 18px 0; color: var(--color-text-muted); font-size: 13px; }
.history-list { display: flex; flex-direction: column; gap: 2px; }
.history-row { background: var(--color-surface); border-radius: var(--radius); padding: 10px 14px; }
.hlink { display: flex; align-items: center; gap: 16px; text-decoration: none; color: inherit; }
.h-time { font-size: 12px; color: var(--color-text-muted); min-width: 90px; }
.h-title { font-size: 14px; font-weight: 500; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.h-artist, .h-genre { font-size: 13px; color: var(--color-text-muted); }
.profile-card { max-width: 420px; }
.profile-avatar { width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 800; color: white; margin-bottom: 12px; overflow: hidden; cursor: pointer; border: 2px solid transparent; }
.profile-avatar:hover { border-color: var(--color-primary-light); }
.profile-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
.avatar-actions { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.avatar-upload { display: inline-flex; align-items: center; justify-content: center; padding: 6px 12px; border-radius: var(--radius); border: 1px solid var(--color-border); color: var(--color-text-muted); cursor: pointer; font-size: 12px; }
.avatar-upload input { display: none; }
.profile-card h2 { font-size: 20px; }
.profile-username { font-size: 13px; color: var(--color-text-muted); margin-top: 2px; }
.profile-stats { display: flex; gap: 20px; margin: 16px 0; }
.pstat { display: flex; flex-direction: column; align-items: center; }
.psv { font-size: 20px; font-weight: 700; color: var(--color-primary-light); }
.psl { font-size: 11px; color: var(--color-text-muted); }
.profile-form { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.profile-form label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); }
.profile-form input { width: 100%; }
.chip-list { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { border: 1px solid var(--color-border); background: var(--color-bg); color: var(--color-text-muted); border-radius: 999px; padding: 6px 12px; cursor: pointer; font-size: 12px; }
.chip.active { background: var(--color-primary); border-color: var(--color-primary); color: #fff; font-weight: 700; }
.save-msg { font-size: 13px; margin-top: 4px; }
.save-msg.success { color: var(--color-like); }
.save-msg.error { color: var(--color-dislike); }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 40px 0; font-size: 14px; }
.guest-card { max-width: 520px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 28px; text-align: center; }
.guest-avatar { width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 14px; font-size: 30px; font-weight: 800; }
.guest-card h2 { font-size: 20px; margin-bottom: 8px; }
.guest-card p { color: var(--color-text-muted); font-size: 14px; line-height: 1.7; }
.guest-actions { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
</style>
