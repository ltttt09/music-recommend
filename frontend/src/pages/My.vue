<template>
  <div class="my-page">
    <!-- Hero Profile Card -->
    <div class="my-hero-card">
      <div class="my-hero-bg" aria-hidden="true"></div>
      <div class="my-hero-content">
        <div class="my-avatar-ring" @click="tab==='profile'?triggerAvatarUpload():setTab('profile')">
          <img v-if="avatarUrl" :src="avatarUrl" class="my-avatar-img" alt="头像" />
          <div v-else class="my-avatar" :style="{ background: avatarGradient }">
            {{ (user?.display_name || user?.username || '?')[0] }}
          </div>
          <div class="avatar-edit-badge" title="更换头像">📷</div>
        </div>
        <div class="my-hero-info">
          <h1>{{ user?.display_name || user?.username || '听众' }}</h1>
          <p class="my-hero-handle">@{{ user?.username || '...' }}</p>
          <div v-if="selectedGenres.size" class="my-hero-genres">
            <span v-for="g in [...selectedGenres].slice(0, 5)" :key="g" class="genre-chip">{{ g }}</span>
            <span v-if="selectedGenres.size > 5" class="genre-chip more">+{{ selectedGenres.size - 5 }}</span>
          </div>
        </div>
      </div>
      <div class="my-stats-row">
        <div class="my-stat-card">
          <span class="my-stat-icon">▶</span>
          <div>
            <b>{{ stats?.total_listens || 0 }}</b>
            <small>播放次数</small>
          </div>
        </div>
        <div class="my-stat-card">
          <span class="my-stat-icon">♫</span>
          <div>
            <b>{{ stats?.unique_tracks || 0 }}</b>
            <small>听过歌曲</small>
          </div>
        </div>
        <div class="my-stat-card">
          <span class="my-stat-icon">♥</span>
          <div>
            <b>{{ favCount }}</b>
            <small>收藏歌曲</small>
          </div>
        </div>
        <div class="my-stat-card">
          <span class="my-stat-icon">♪</span>
          <div>
            <b>{{ stats?.playlist_count || 0 }}</b>
            <small>自建歌单</small>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <nav class="my-nav">
      <button
        v-for="t in tabs"
        :key="t.id"
        :class="['my-nav-btn', { active: tab === t.id }]"
        @click="setTab(t.id)"
      >
        <span class="nav-icon">{{ t.icon }}</span>
        <span class="nav-label">{{ t.label }}</span>
      </button>
    </nav>

    <!-- Content Sections -->
    <transition name="tab-fade" mode="out-in">
      <div :key="tab" class="my-content">

        <!-- Likes -->
        <section v-if="tab === 'likes'" class="my-section">
          <div class="section-header">
            <h2>我喜欢的歌曲</h2>
            <span class="section-badge">{{ likes.length }} 首</span>
          </div>
          <TrackList v-if="likes.length" :items="pagedLikes" show-unlike @unlike="unlikeTrack" />
          <div v-else-if="!likesLoading" class="my-empty-card">
            <div class="empty-visual">♥</div>
            <p>还没有喜欢的歌曲</p>
            <router-link to="/" class="empty-link">去首页发现好音乐</router-link>
          </div>
          <div v-if="likesPages > 1" class="my-pager">
            <button class="btn btn-ghost btn-sm" :disabled="likesPage<=1" @click="likesPage--">上一页</button>
            <span>{{ likesPage }} / {{ likesPages }}</span>
            <button class="btn btn-ghost btn-sm" :disabled="likesPage>=likesPages" @click="likesPage++">下一页</button>
          </div>
        </section>

        <!-- History -->
        <section v-if="tab === 'history'" class="my-section">
          <div class="section-header">
            <h2>最近播放</h2>
            <span class="section-badge">{{ history.length }} 条记录</span>
          </div>
          <div v-if="history.length" class="hist-list">
            <router-link
              v-for="h in pagedHistory"
              :key="h.id"
              :to="'/track/' + h.track_id"
              class="hist-card"
            >
              <span class="hist-cover">
                <img v-if="h.image_url && !imgFailed[h.track_id]" :src="h.image_url" referrerpolicy="no-referrer" @error="imgFailed[h.track_id]=true" />
                <span v-else :style="{ background: grad(h.track_id) }">{{ ch(h.track_title) }}</span>
              </span>
              <div class="hist-main">
                <b>{{ h.track_title }}</b>
                <small>{{ h.artist_name }}</small>
              </div>
              <span class="hist-time">{{ fmtDate(h.listened_at) }}</span>
            </router-link>
          </div>
          <div v-else-if="!histLoading" class="my-empty-card">
            <div class="empty-visual">🕐</div>
            <p>暂无听歌记录</p>
          </div>
          <div v-if="historyPages > 1" class="my-pager">
            <button class="btn btn-ghost btn-sm" :disabled="historyPage<=1" @click="historyPage--">上一页</button>
            <span>{{ historyPage }} / {{ historyPages }}</span>
            <button class="btn btn-ghost btn-sm" :disabled="historyPage>=historyPages" @click="historyPage++">下一页</button>
          </div>
        </section>

        <!-- Playlists -->
        <section v-if="tab === 'playlists'" class="my-section">
          <div class="section-header">
            <h2>我的歌单</h2>
          </div>
          <div class="pl-create-row">
            <input v-model="newPlName" placeholder="输入歌单名称..." class="pl-input" @keyup.enter="createPlaylist" />
            <button class="btn btn-primary btn-sm" @click="createPlaylist" :disabled="plCreating">
              {{ plCreating ? '创建中...' : '新建歌单' }}
            </button>
          </div>
          <p v-if="plMsg" :class="['pf-msg', plMsgOk ? 'ok' : 'err']">{{ plMsg }}</p>
          <div v-if="playlists.length" class="pl-grid">
            <div v-for="pl in playlists" :key="pl.id" class="pl-card" @click="$router.push('/playlist/'+pl.id)">
              <div class="pl-cover" :style="{ background: grad(pl.id) }">
                <div class="pl-mosaic"><span v-for="c in 4" :key="c" :style="{ background: grad(pl.id*c) }"></span></div>
              </div>
              <div class="pl-info">
                <span class="pl-name">{{ pl.name }}</span>
                <span class="pl-cnt">{{ pl.track_count || 0 }} 首歌</span>
              </div>
              <button class="pl-del" @click.stop="deletePl(pl.id)">✕</button>
            </div>
          </div>
          <div v-else-if="!plLoading" class="my-empty-card">
            <div class="empty-visual">♪</div>
            <p>还没有自建歌单</p>
            <p class="empty-hint">输入歌单名称，创建你的专属歌单</p>
          </div>
          <div v-if="plPages > 1" class="my-pager">
            <button class="btn btn-ghost btn-sm" :disabled="plPage<=1" @click="loadPlaylists(plPage-1)">上一页</button>
            <span>{{ plPage }} / {{ plPages }}</span>
            <button class="btn btn-ghost btn-sm" :disabled="plPage>=plPages" @click="loadPlaylists(plPage+1)">下一页</button>
          </div>
        </section>

        <!-- Blacklist -->
        <section v-if="tab === 'blacklist'" class="my-section">
          <div class="section-header">
            <h2>黑名单</h2>
            <span class="section-badge">{{ blacklist.length }} 首</span>
          </div>
          <div v-if="blacklist.length" class="bl-list">
            <div v-for="t in blacklist" :key="t.id" class="bl-card">
              <span class="bl-icon">⊘</span>
              <div class="bl-info">
                <b>{{ t.title }}</b>
                <small>{{ t.artist_name }}</small>
              </div>
              <button class="btn btn-ghost btn-sm" @click="removeBlack(t.id)">移除</button>
            </div>
          </div>
          <div v-else-if="!blackLoading" class="my-empty-card">
            <div class="empty-visual">⊘</div>
            <p>黑名单为空</p>
            <p class="empty-hint">标记不喜欢的歌曲后，它们会出现在这里</p>
          </div>
        </section>

        <!-- Profile Settings -->
        <section v-if="tab === 'profile'" class="my-section">
          <div class="section-header">
            <h2>个人设置</h2>
          </div>
          <!-- Avatar Upload -->
          <div class="pf-avatar-section">
            <div class="pf-avatar-preview" :style="avatarUrl ? {} : { background: avatarGradient }">
              <img v-if="avatarUrl" :src="avatarUrl" alt="头像" />
              <span v-else>{{ (user?.display_name || user?.username || '?')[0] }}</span>
            </div>
            <div class="pf-avatar-actions">
              <label class="btn btn-primary btn-sm pf-avatar-btn">
                上传头像
                <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="pf-avatar-file" @change="onAvatarSelected" />
              </label>
              <button v-if="avatarUrl" class="btn btn-ghost btn-sm" @click="removeAvatar">移除头像</button>
              <p class="pf-avatar-tip">支持 JPG/PNG/WebP/GIF，最大 10MB</p>
            </div>
          </div>
          <div class="pf-card">
            <div class="pf-field">
              <label>显示名称</label>
              <input v-model="editName" placeholder="你的名字" />
            </div>
            <div class="pf-field">
              <label>偏好流派</label>
              <div class="pf-tags">
                <button
                  v-for="g in preferenceOptions"
                  :key="g"
                  :class="['pf-tag', { sel: selectedGenres.has(g) }]"
                  @click="toggleGenre(g)"
                >{{ g }}</button>
              </div>
            </div>
            <button class="btn btn-primary" @click="saveProfile" :disabled="saving" style="width:100%;justify-content:center;margin-top:8px">
              {{ saving ? '保存中...' : '保存设置' }}
            </button>
            <p v-if="saveMsg" :class="['pf-msg', saveOk ? 'ok' : 'err']">{{ saveMsg }}</p>
          </div>

        </section>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import api from '../api.js'
import { auth, getUserId } from '../auth.js'
import TrackList from '../components/TrackList.vue'
import { PREFERENCE_GENRES, parsePreferences, stringifyPreferences } from '../preferences.js'

const GRADS = [
  'linear-gradient(145deg,#6c5ce7,#a78bfa)',
  'linear-gradient(145deg,#0984e3,#74b9ff)',
  'linear-gradient(145deg,#00b894,#55efc4)',
  'linear-gradient(145deg,#e17055,#fab1a0)',
  'linear-gradient(145deg,#fdcb6e,#ffeaa7)',
]
const grad = id => GRADS[Math.abs(id) % GRADS.length]
const ch = s => /[^\x00-\x7F]/.test((s || '?')[0]) ? '♪' : (s || '?')[0].toUpperCase()
const avatarGradient = 'linear-gradient(135deg, var(--color-primary), var(--color-accent))'
const imgFailed = reactive({})

const tab = ref('likes')
const tabs = [
  { id: 'likes', label: '喜欢', icon: '♥' },
  { id: 'history', label: '最近', icon: '▶' },
  { id: 'playlists', label: '歌单', icon: '♪' },
  { id: 'blacklist', label: '黑名单', icon: '⊘' },
  { id: 'profile', label: '设置', icon: '⚙' },
]

function setTab(t) {
  if (tab.value !== t) {
    tab.value = t
    loadTab(t)
  }
}
function loadTab(t) {
  if (t === 'likes' && !likes.value.length) loadLikes()
  else if (t === 'history' && !history.value.length) loadHistory()
  else if (t === 'playlists') loadPlaylists()
  else if (t === 'blacklist' && !blacklist.value.length) loadBlacklist()
  else if (t === 'profile' && !profile.value) loadProfile()
}

const user = ref(null)
const stats = ref(null)
const favCount = ref(0)
const fmtDate = d => d ? new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''

// Likes
const likes = ref([])
const likesLoading = ref(false)
const likesPage = ref(1)
const likesSize = 12
const likesPages = computed(() => Math.max(1, Math.ceil(likes.value.length / likesSize)))
const pagedLikes = computed(() => likes.value.slice((likesPage.value - 1) * likesSize, likesPage.value * likesSize))
async function loadLikes() {
  likesLoading.value = true
  try { const d = await api.getLikedTracks(getUserId()); likes.value = d.items || [] } finally { likesLoading.value = false }
}
async function unlikeTrack(track) { await api.unlikeTrack(getUserId(), track.id); loadLikes() }

// History
const history = ref([])
const histLoading = ref(false)
const historyPage = ref(1)
const histSize = 15
const historyPages = computed(() => Math.max(1, Math.ceil(history.value.length / histSize)))
const pagedHistory = computed(() => history.value.slice((historyPage.value - 1) * histSize, historyPage.value * histSize))
async function loadHistory() {
  histLoading.value = true
  try { const d = await api.getUserHistory(getUserId(), 200); history.value = d.items || [] } finally { histLoading.value = false }
}

// Playlists
const playlists = ref([])
const plLoading = ref(false)
const newPlName = ref('')
const plCreating = ref(false)
const plMsg = ref('')
const plMsgOk = ref(false)
let plMsgTimer = null
function setPlMsg(text, ok = false) {
  plMsg.value = text
  plMsgOk.value = ok
  if (plMsgTimer) clearTimeout(plMsgTimer)
  if (text) plMsgTimer = setTimeout(() => { plMsg.value = ''; plMsgOk.value = false; plMsgTimer = null }, ok ? 2000 : 3000)
}
const plPage = ref(1)
const plSize = 10
const playlistsTotal = ref(0)
const plPages = computed(() => Math.max(1, Math.ceil((playlistsTotal.value || 0) / plSize)))
async function loadPlaylists(p = plPage.value) {
  if (!getUserId()) return
  plLoading.value = true
  plPage.value = Math.max(1, p)
  try {
    const d = await api.getUserCreatedPlaylists(getUserId(), plPage.value, plSize)
    playlists.value = d.items || []
    playlistsTotal.value = d.total || 0
  } finally { plLoading.value = false }
}
async function createPlaylist() {
  const n = newPlName.value.trim()
  if (!n) { setPlMsg('请输入歌单名称', false); return }
  if (n.length > 30) { setPlMsg('歌单名称不能超过30个字符', false); return }
  setPlMsg('', false)
  plCreating.value = true
  try {
    await api.createUserPlaylist(getUserId(), n)
    newPlName.value = ''
    setPlMsg('歌单创建成功', true)
    await loadPlaylists(1)
  } catch (e) {
    const status = e.response?.status
    if (status === 400) setPlMsg(e.response?.data?.detail || '歌单名称无效', false)
    else if (status === 409) setPlMsg('同名歌单已存在', false)
    else setPlMsg(e.message || '创建失败', false)
  } finally { plCreating.value = false }
}
async function deletePl(id) { if (!confirm('确定删除此歌单？')) return; await api.deleteUserPlaylist(id); loadPlaylists() }

// Blacklist
const blacklist = ref([])
const blackLoading = ref(false)
async function loadBlacklist() {
  blackLoading.value = true
  try { const d = await api.getBlacklist(getUserId(), 1); blacklist.value = d.items || [] } finally { blackLoading.value = false }
}
async function removeBlack(id) { await api.removeFromBlacklist(getUserId(), id); loadBlacklist() }

// Profile
const profile = ref(null)
const editName = ref('')
const preferenceOptions = PREFERENCE_GENRES
const selectedGenres = ref(new Set())
const saving = ref(false)
const saveMsg = ref('')
const saveOk = ref(false)
const avatarUrl = ref('')
const avatarUploading = ref(false)

function triggerAvatarUpload() {
  const input = document.querySelector('.pf-avatar-file')
  if (input) input.click()
}

function onAvatarSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) { saveMsg.value = '头像文件不能超过 10MB'; saveOk.value = false; return }
  const reader = new FileReader()
  reader.onload = () => { avatarUrl.value = reader.result; saveAvatar() }
  reader.readAsDataURL(file)
}

function removeAvatar() {
  avatarUrl.value = ''
  saveAvatar()
}

async function saveAvatar() {
  avatarUploading.value = true
  try {
    await api.updateProfile(getUserId(), {
      display_name: editName.value || user.value?.display_name || '',
      preferred_genres: stringifyPreferences(selectedGenres.value),
      avatar_url: avatarUrl.value || ''
    })
    saveMsg.value = avatarUrl.value ? '头像已更新' : '头像已移除'
    saveOk.value = true
  } catch (e) { saveMsg.value = e.message || '头像保存失败'; saveOk.value = false }
  finally { avatarUploading.value = false }
}
async function loadProfile() {
  if (!getUserId()) return
  try {
    const d = await api.getUser(getUserId())
    user.value = d.user
    profile.value = d.user
    stats.value = d.stats
    editName.value = d.user?.display_name || ''
    avatarUrl.value = d.user?.avatar_url || ''
    selectedGenres.value = parsePreferences(d.user?.preferred_genres || '')
    favCount.value = d.stats?.liked_count || 0
  } catch {}
}
function toggleGenre(g) {
  const s = new Set(selectedGenres.value)
  s.has(g) ? s.delete(g) : s.add(g)
  selectedGenres.value = s
}
async function saveProfile() {
  saving.value = true
  try {
    await api.updateProfile(getUserId(), { display_name: editName.value, preferred_genres: [...selectedGenres.value].join(',') })
    auth.username = editName.value || user.value?.username
    localStorage.setItem('username', auth.username)
    saveMsg.value = '设置已保存'
    saveOk.value = true
  } catch (e) { saveMsg.value = e.message || '保存失败'; saveOk.value = false } finally { saving.value = false }
}

onMounted(() => { loadProfile(); loadLikes() })
</script>

<style scoped>
.my-page { max-width: 800px; margin: 0 auto; padding: 0 20px 40px; }

/* Hero Card */
.my-hero-card {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}
.my-hero-bg {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 120px;
  background: linear-gradient(135deg, rgba(108,92,231,.28), rgba(0,206,201,.12));
  pointer-events: none;
}
.my-hero-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 28px 24px 16px;
}
.my-avatar-ring {
  width: 68px; height: 68px;
  border-radius: 50%;
  padding: 3px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
}
.my-avatar {
  width: 100%; height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px; font-weight: 900;
  color: #fff;
  background: var(--color-surface);
}
.my-avatar-img {
  width: 100%; height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-edit-badge {
  position: absolute;
  bottom: -2px; right: -2px;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0;
  transition: opacity .2s;
  cursor: pointer;
}
.my-avatar-ring:hover .avatar-edit-badge { opacity: 1; }
.my-hero-info h1 {
  font-size: 24px; font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.my-hero-handle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 3px 0 0;
}
.my-hero-genres {
  display: flex; gap: 5px; margin-top: 8px; flex-wrap: wrap;
}
.genre-chip {
  font-size: 11px; font-weight: 600;
  padding: 3px 9px;
  border-radius: 20px;
  background: rgba(108,92,231,.12);
  color: var(--color-primary-light);
}
.genre-chip.more { background: var(--color-bg); color: var(--color-text-muted); }

/* Stats Row */
.my-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  padding: 0 24px 18px;
  position: relative;
}
.my-stat-card {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 10px;
  border-top: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
}
.my-stat-card:last-child { border-right: none; }
.my-stat-icon {
  font-size: 18px;
  color: var(--color-primary-light);
  width: 32px; height: 32px;
  border-radius: 10px;
  background: rgba(108,92,231,.1);
  display: flex;
  align-items: center;
  justify-content: center;
}
.my-stat-card b {
  font-size: 18px; font-weight: 900;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.my-stat-card small {
  font-size: 11px; color: var(--color-text-muted); margin-top: 1px;
}

/* Navigation */
.my-nav {
  display: flex;
  gap: 4px;
  margin-bottom: 22px;
  background: var(--color-surface);
  border-radius: 14px;
  padding: 4px;
  border: 1px solid var(--color-border);
}
.my-nav-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 18px;
  border: none; border-radius: 10px;
  font-size: 13px; font-weight: 700;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all .2s;
  font-family: inherit;
}
.my-nav-btn.active {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 4px 16px rgba(108,92,231,.22);
}
.my-nav-btn:hover:not(.active) {
  background: var(--color-bg);
  color: var(--color-text);
}
.nav-icon { font-size: 15px; }
.nav-label { white-space: nowrap; }

/* Sections */
.my-section { animation: fadeUp .35s ease both; }
.section-header {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 16px;
}
.section-header h2 { font-size: 18px; font-weight: 800; margin: 0; }
.section-badge {
  font-size: 12px; font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border-radius: 20px;
  padding: 4px 12px;
}

/* Empty States */
.my-empty-card {
  text-align: center;
  padding: 48px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
}
.empty-visual {
  font-size: 48px; font-weight: 900;
  color: var(--color-primary-light);
  opacity: .3;
  margin-bottom: 14px;
}
.my-empty-card p { font-size: 14px; color: var(--color-text-muted); margin: 0; }
.empty-hint { font-size: 12px; margin-top: 6px; color: var(--color-text-muted); opacity: .7; }
.empty-link {
  display: inline-block;
  margin-top: 12px;
  padding: 8px 20px;
  border-radius: 10px;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px; font-weight: 600;
  text-decoration: none;
  transition: transform .2s;
}
.empty-link:hover { transform: translateY(-2px); }

/* Pager */
.my-pager {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  margin-top: 18px; font-size: 13px; color: var(--color-text-muted);
}

/* History */
.hist-list { display: flex; flex-direction: column; gap: 6px; }
.hist-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  text-decoration: none; color: inherit;
  transition: transform .15s, border-color .15s;
  animation: fadeUp .3s ease both;
}
.hist-card:hover { transform: translateX(4px); border-color: var(--color-primary); }
.hist-cover {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800;
  color: rgba(255,255,255,.5);
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
}
.hist-cover img {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: 10px;
}
.hist-cover > span {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  border-radius: 10px;
}
.hist-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.hist-main b { font-size: 14px; font-weight: 600; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-main small { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-time { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; }

/* Playlists */
.pl-create-row {
  display: flex; gap: 8px; margin-bottom: 16px;
}
.pl-input {
  flex: 1;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 13px;
}
.pl-input:focus { border-color: var(--color-primary); }
.pl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.pl-card {
  background: var(--color-surface);
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: transform .2s, border-color .2s;
  border: 1px solid var(--color-border);
  position: relative;
}
.pl-card:hover { transform: translateY(-4px); border-color: var(--color-primary); }
.pl-cover {
  aspect-ratio: 1;
  display: flex; align-items: center; justify-content: center;
}
.pl-mosaic {
  display: grid; grid-template-columns: 1fr 1fr;
  width: 60%; height: 60%;
  gap: 3px; border-radius: 10px; overflow: hidden; opacity: .7;
}
.pl-mosaic span { border-radius: 3px; }
.pl-info { padding: 12px 14px; }
.pl-name { font-size: 14px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.pl-cnt { font-size: 11px; color: var(--color-text-muted); margin-top: 3px; }
.pl-del {
  position: absolute; top: 8px; right: 8px;
  background: rgba(0,0,0,.55); color: #fff;
  border: none; width: 26px; height: 26px;
  border-radius: 50%; font-size: 12px;
  cursor: pointer; opacity: 0; transition: opacity .2s;
}
.pl-card:hover .pl-del { opacity: 1; }

/* Blacklist */
.bl-list { display: flex; flex-direction: column; gap: 6px; }
.bl-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  animation: fadeUp .3s ease both;
}
.bl-icon { font-size: 20px; color: var(--color-dislike); }
.bl-info { flex: 1; }
.bl-info b { font-size: 14px; font-weight: 600; }
.bl-info small { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }

/* Avatar Upload */
.pf-avatar-section {
  display: flex;
  align-items: center;
  gap: 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 22px;
  margin-bottom: 18px;
}
.pf-avatar-preview {
  width: 72px; height: 72px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; font-weight: 900; color: #fff;
  flex-shrink: 0;
  overflow: hidden;
}
.pf-avatar-preview img {
  width: 100%; height: 100%; object-fit: cover; border-radius: 50%;
}
.pf-avatar-actions { flex: 1; }
.pf-avatar-btn {
  cursor: pointer;
  margin-bottom: 6px;
}
.pf-avatar-file { display: none; }
.pf-avatar-tip {
  font-size: 12px; color: var(--color-text-muted); margin: 6px 0 0;
}

/* Profile */
.pf-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 22px;
  margin-bottom: 18px;
}
.pf-field { margin-bottom: 16px; }
.pf-field label {
  display: block; font-size: 12px; font-weight: 700;
  color: var(--color-text-muted); margin-bottom: 6px;
}
.pf-field input {
  width: 100%; padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 14px;
}
.pf-field input:focus { border-color: var(--color-primary); }
.pf-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.pf-tag {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid var(--color-border);
  background: var(--color-bg); color: var(--color-text-muted);
  font-size: 13px; cursor: pointer;
  transition: all .2s; font-family: inherit;
}
.pf-tag.sel {
  background: var(--color-primary); color: #fff;
  border-color: var(--color-primary);
}
.pf-msg { margin-top: 10px; font-size: 14px; }
.pf-msg.ok { color: var(--color-like); }
.pf-msg.err { color: var(--color-dislike); font-weight: bold; }


/* Transitions */
.tab-fade-enter-active, .tab-fade-leave-active { transition: opacity .2s, transform .2s; }
.tab-fade-enter-from { opacity: 0; transform: translateY(8px); }
.tab-fade-leave-to { opacity: 0; transform: translateY(-8px); }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Responsive */
@media (max-width: 700px) {
  .my-stats-row { grid-template-columns: repeat(2, 1fr); }
  .my-stat-card { border-right: none; }
  .my-stat-card:nth-child(2) { border-right: 1px solid var(--color-border); }
}
@media (max-width: 500px) {
  .my-hero-content { flex-direction: column; text-align: center; padding: 24px 16px 14px; }
  .my-hero-genres { justify-content: center; }
  .my-nav-btn { padding: 8px 12px; }
  .nav-label { display: none; }
  .nav-icon { font-size: 18px; }
  .pl-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
