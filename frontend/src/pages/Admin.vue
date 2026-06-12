<template>
  <div class="container">
    <div v-if="!loggedIn" class="auth-card">
      <h1>管理员登录</h1>
      <p class="desc">请输入管理员密码以访问后台控制台</p>
      <form @submit.prevent="doLogin">
        <input v-model="password" type="password" placeholder="管理员密码" required />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary" :disabled="loading">{{ loading ? '验证中...' : '登录' }}</button>
      </form>
      <p class="hint">默认密码：admin123，可通过 MUSIC_ADMIN_PASSWORD 环境变量修改</p>
      <p class="switch"><a href="/#/">返回用户端</a></p>
    </div>

    <div v-else>
      <div class="topbar">
        <div>
          <h1>管理控制台</h1>
          <p class="topbar-sub">音乐推荐系统演示后台</p>
        </div>
        <div class="topbar-right">
          <a href="/#/" class="user-link">返回用户端</a>
          <button class="btn btn-ghost btn-sm" @click="logout">退出登录</button>
        </div>
      </div>

      <div class="tabs">
        <button v-for="t in tabs" :key="t.id" :class="{ active: tab === t.id }" @click="switchTab(t.id)">
          {{ t.label }}
        </button>
      </div>

      <section v-if="tab === 'overview'">
        <div v-if="statsLoading" class="spinner"></div>
        <template v-else>
          <div class="stat-grid">
            <div class="stat-card"><span class="sv">{{ stats.users || 0 }}</span><span class="sl">用户数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.tracks || 0 }}</span><span class="sl">歌曲数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.artists || 0 }}</span><span class="sl">艺人数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.listens || 0 }}</span><span class="sl">播放记录</span></div>
            <div class="stat-card"><span class="sv">{{ stats.feedback || 0 }}</span><span class="sl">反馈数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.playlists || 0 }}</span><span class="sl">系统歌单</span></div>
            <div class="stat-card"><span class="sv">{{ stats.playable_tracks || 0 }}</span><span class="sl">可播放歌曲</span></div>
            <div class="stat-card"><span class="sv">{{ stats.full_audio_tracks || 0 }}</span><span class="sl">完整音频</span></div>
          </div>
          <div class="two-col">
            <div class="section">
              <h2>热门歌曲 Top 10</h2>
              <div class="simple-list">
                <div v-for="(t, i) in stats.top_tracks || []" :key="i" class="simple-row">
                  <span class="rank">{{ i + 1 }}</span>
                  <span class="name">{{ t.title }}</span>
                  <span class="artist">{{ t.artist }}</span>
                  <span class="cnt">{{ t.cnt }} 次</span>
                </div>
              </div>
            </div>
            <div class="section">
              <h2>流派分布</h2>
              <div class="genre-bars">
                <div v-for="g in limitedGenreDistribution" :key="g.genre" class="genre-row">
                  <span class="genre-label">{{ g.genre }}</span>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: barWidth(g.cnt) + '%' }"></div></div>
                  <span class="genre-cnt">{{ g.cnt }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </section>

      <section v-if="tab === 'users'">
        <div v-if="usersLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>ID</th><th>用户名</th><th>显示名称</th><th>偏好流派</th><th>注册时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in userList" :key="u.id">
              <td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.display_name }}</td>
              <td>{{ u.preferred_genres || '-' }}</td><td>{{ u.join_date?.slice(0, 10) }}</td>
              <td><button class="btn btn-dislike btn-xs" @click="deleteUser(u.id)">删除</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="tab === 'tracks'">
        <div class="toolbar">
          <input v-model="trackSearch" placeholder="搜索歌曲或艺人..." class="search-input" @keyup.enter="resetTrackPage" />
          <select v-model="trackSortBy" @change="resetTrackPage">
            <option value="id">ID</option>
            <option value="popularity">热度</option>
            <option value="year">年份</option>
            <option value="title">歌名</option>
            <option value="artist">艺人</option>
            <option value="genre">流派</option>
            <option value="created">新增时间</option>
          </select>
          <select v-model="trackSortOrder" @change="resetTrackPage">
            <option value="asc">升序</option>
            <option value="desc">降序</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="resetTrackPage">搜索</button>
        </div>
        <div v-if="tracksLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>ID</th><th>歌曲名</th><th>艺人</th><th>专辑</th><th>流派</th><th>年份</th><th>来源</th><th>音频</th><th>封面</th><th>试听</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="t in trackList" :key="t.id">
              <td>{{ t.id }}</td><td class="td-title">{{ t.title }}</td><td>{{ t.artist_name }}</td>
              <td class="td-album">{{ t.album || '-' }}</td><td>{{ t.genre || '-' }}</td><td>{{ t.year || '-' }}</td>
              <td>{{ t.source || 'itunes' }}</td><td>{{ t.audio_type || 'preview' }}</td>
              <td><span :class="t.image_url ? 'badge-ok' : 'badge-no'">{{ t.image_url ? '有' : '无' }}</span></td>
              <td><span :class="t.preview_url ? 'badge-ok' : 'badge-no'">{{ t.preview_url ? '有' : '无' }}</span></td>
              <td class="row-actions">
                <button class="btn btn-ghost btn-xs" @click="openEdit(t)">编辑</button>
                <button class="btn btn-dislike btn-xs" @click="deleteTrack(t.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="pagination-row">
          <p class="pagination-info">共 {{ trackTotal }} 条记录，第 {{ trackPage }} / {{ trackMaxPage }} 页</p>
          <div class="pager-actions">
            <button class="btn btn-ghost btn-xs" :disabled="trackPage <= 1" @click="loadTracks(trackPage - 1)">上一页</button>
            <button class="btn btn-ghost btn-xs" :disabled="trackPage >= trackMaxPage" @click="loadTracks(trackPage + 1)">下一页</button>
          </div>
        </div>
      </section>

      <section v-if="tab === 'feedback'">
        <div v-if="feedbackLoading" class="spinner"></div>
        <template v-else>
          <div class="stat-grid stat-grid-sm">
            <div class="stat-card"><span class="sv like">{{ fbData.total_likes }}</span><span class="sl">总喜欢</span></div>
            <div class="stat-card"><span class="sv dislike">{{ fbData.total_dislikes }}</span><span class="sl">总跳过</span></div>
          </div>
          <div class="two-col">
            <div class="section">
              <h2>最受欢迎</h2>
              <div class="simple-list">
                <div v-for="(t, i) in fbData.top_liked" :key="i" class="simple-row">
                  <span class="rank">{{ i + 1 }}</span><span class="name">{{ t.title }}</span>
                  <span class="artist">{{ t.artist_name }}</span><span class="cnt like">{{ t.cnt }}</span>
                </div>
              </div>
            </div>
            <div class="section">
              <h2>最多跳过</h2>
              <div class="simple-list">
                <div v-for="(t, i) in fbData.top_disliked" :key="i" class="simple-row">
                  <span class="rank">{{ i + 1 }}</span><span class="name">{{ t.title }}</span>
                  <span class="artist">{{ t.artist_name }}</span><span class="cnt dislike">{{ t.cnt }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </section>

      <section v-if="tab === 'comments'">
        <div v-if="commentsLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>ID</th><th>用户</th><th>歌曲</th><th>内容</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="c in commentList" :key="c.id">
              <td>{{ c.id }}</td>
              <td>{{ c.display_name || c.username }}</td>
              <td class="td-title">{{ c.track_title }}</td>
              <td class="td-comment">{{ c.content }}</td>
              <td>{{ c.created_at?.slice(0, 16) }}</td>
              <td><button class="btn btn-dislike btn-xs" @click="deleteComment(c.id)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <p class="pagination-info">共 {{ commentsTotal }} 条评论</p>
      </section>

      <section v-if="tab === 'data'">
        <div v-if="dataLoading" class="spinner"></div>
        <template v-else>
          <div class="section">
            <h2>iTunes 数据概览</h2>
            <p class="note">当前用户端仅使用 iTunes 30 秒试听数据，其他旧数据源不再作为前台入口展示。</p>
            <table class="data-table">
              <thead><tr><th>数据源</th><th>歌曲数</th><th>可播放</th><th>完整音频</th></tr></thead>
              <tbody>
                <tr v-for="s in itunesSources" :key="s.source">
                  <td>{{ s.source || 'itunes' }}</td>
                  <td>{{ s.tracks }}</td>
                  <td>{{ s.playable }}</td>
                  <td>{{ s.full_audio }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="section">
            <h2>最近导入记录</h2>
            <table class="data-table">
              <thead><tr><th>时间</th><th>来源</th><th>状态</th><th>数量</th><th>说明</th></tr></thead>
              <tbody>
                <tr v-for="r in itunesImportRuns" :key="r.id">
                  <td>{{ r.created_at?.slice(0, 16) }}</td>
                  <td>{{ r.source }}</td>
                  <td>{{ r.status }}</td>
                  <td>{{ r.imported_tracks }}</td>
                  <td class="td-comment">{{ r.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </section>

      <section v-if="tab === 'logs'">
        <div class="toolbar">
          <input v-model="logSearch" placeholder="搜索用户、歌曲、艺人、理由..." class="search-input" @keyup.enter="loadLogs" />
          <input v-model="logModel" placeholder="模型名，如 hybrid" class="search-input compact-input" @keyup.enter="loadLogs" />
          <button class="btn btn-primary btn-sm" @click="loadLogs">筛选</button>
        </div>
        <div v-if="logsLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>时间</th><th>用户</th><th>歌曲</th><th>模型</th><th>分数</th><th>理由</th></tr></thead>
          <tbody>
            <tr v-for="r in logList" :key="r.id">
              <td>{{ r.created_at?.slice(0, 16) }}</td>
              <td>{{ r.display_name || r.username || '-' }}</td>
              <td class="td-title">{{ r.track_title }}</td>
              <td>{{ r.model_name }}</td>
              <td>{{ ((r.score || 0) * 100).toFixed(1) }}%</td>
              <td class="td-comment">{{ r.reason }}</td>
            </tr>
          </tbody>
        </table>
        <p class="pagination-info">共 {{ logsTotal }} 条推荐日志</p>
      </section>

      <section v-if="tab === 'actions'">
        <div class="toolbar">
          <select v-model="actionFilter" class="search-input" @change="loadActionLogs">
            <option value="">全部动作</option>
            <option value="audio_play_request">播放请求</option>
            <option value="audio_playing">开始播放</option>
            <option value="audio_paused">暂停播放</option>
            <option value="audio_ended">播放结束</option>
            <option value="audio_error">播放错误</option>
            <option value="audio_missing_source">缺少音频</option>
            <option value="audio_seek">拖动进度</option>
            <option value="feedback">用户反馈</option>
          </select>
          <select v-model="actionStatus" class="search-input compact-input" @change="loadActionLogs">
            <option value="">全部状态</option>
            <option value="requested">请求</option>
            <option value="success">成功</option>
            <option value="error">错误</option>
            <option value="blocked">阻止</option>
          </select>
          <input v-model="actionSearch" placeholder="搜索说明、页面或对象 ID" class="search-input" @keyup.enter="loadActionLogs" />
          <button class="btn btn-primary btn-sm" @click="loadActionLogs">刷新</button>
        </div>
        <div v-if="actionLogsLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>时间</th><th>用户</th><th>动作</th><th>对象</th><th>状态</th><th>说明</th><th>页面</th></tr></thead>
          <tbody>
            <tr v-for="r in actionLogList" :key="r.id">
              <td>{{ r.created_at?.slice(0, 16) }}</td>
              <td>{{ r.display_name || r.username || r.session_id || '-' }}</td>
              <td>{{ actionLabel(r.action_type) }}</td>
              <td>{{ r.entity_type || '-' }} #{{ r.entity_id || '-' }}</td>
              <td>{{ r.status || '-' }}</td>
              <td class="td-comment">{{ r.message }}</td>
              <td class="td-comment">{{ r.page_url }}</td>
            </tr>
          </tbody>
        </table>
        <p class="pagination-info">共 {{ actionLogsTotal }} 条操作日志</p>
      </section>

      <section v-if="tab === 'models'">
        <div v-if="metricsLoading" class="loading-panel">
          <div class="progress-card">
            <div class="progress-head">
              <div>
                <h2>{{ metricJob?.stage || '准备评估' }}</h2>
                <p>{{ metricJob?.message || '正在创建模型评估任务' }}</p>
              </div>
              <span class="progress-num">{{ metricProgress.toFixed(1) }}%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" :style="{ width: metricProgress + '%' }"></div></div>
            <div class="progress-meta">
              <span>进度 {{ metricJob?.current || 0 }} / {{ metricJob?.total || 0 }}</span>
              <span>模型 {{ metricJob?.current_model || '-' }}</span>
              <span>用户 {{ metricJob?.current_user_id || '-' }}</span>
              <span>耗时 {{ metricElapsed }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="metricsError" class="error-msg">{{ metricsError }}</div>
        <template v-else>
          <div class="stat-grid stat-grid-sm">
            <div class="stat-card"><span class="sv">{{ metrics.sample_users || 0 }}</span><span class="sl">样本用户</span></div>
            <div class="stat-card"><span class="sv">{{ metrics.coverage_percent || 0 }}%</span><span class="sl">覆盖率</span></div>
            <div class="stat-card"><span class="sv">{{ percent(metrics.precision_at_10) }}</span><span class="sl">Precision@10</span></div>
            <div class="stat-card"><span class="sv">{{ percent(metrics.recall_at_10) }}</span><span class="sl">Recall@10</span></div>
            <div class="stat-card"><span class="sv">{{ metrics.avg_recommendations || 0 }}</span><span class="sl">平均返回数</span></div>
          </div>
          <div class="section">
            <h2>已加载模型</h2>
            <div class="model-list"><span v-for="m in metrics.models_loaded || []" :key="m" class="model-tag">{{ m }}</span></div>
            <p class="note">{{ metrics.notes }}</p>
          </div>
          <div v-if="metrics.model_breakdown?.length" class="section">
            <h2>分模型评估</h2>
            <table class="data-table">
              <thead><tr><th>模型</th><th>样本</th><th>命中</th><th>Precision</th><th>Recall</th><th>平均返回</th></tr></thead>
              <tbody>
                <tr v-for="m in metrics.model_breakdown" :key="m.model">
                  <td>{{ m.model }}</td>
                  <td>{{ m.cases }}</td>
                  <td>{{ m.hits }}</td>
                  <td>{{ percent(m.precision_at_10) }}</td>
                  <td>{{ percent(m.recall_at_10) }}</td>
                  <td>{{ m.avg_recommendations }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="section">
            <h2>模型管理</h2>
            <div class="action-row">
              <label class="inline-control">样本用户
                <input v-model.number="metricSampleUsers" type="number" min="1" max="300" />
              </label>
              <button class="btn btn-ghost" @click="loadMetrics" :disabled="metricsLoading">重新评估指标</button>
              <button class="btn btn-primary" @click="retrainModel(false)" :disabled="retraining">{{ retraining ? '训练中...' : '重新训练模型' }}</button>
              <button class="btn btn-ghost" @click="retrainModel(true)" :disabled="retraining">强制重建数据</button>
            </div>
            <p v-if="retrainMsg" class="retrain-msg" :class="retrainOk ? 'success' : 'error'">{{ retrainMsg }}</p>
          </div>
        </template>
      </section>

      <section v-if="tab === 'system'">
        <div v-if="sysLoading" class="spinner"></div>
        <template v-else>
          <div class="stat-grid stat-grid-sm">
            <div class="stat-card"><span class="sv">{{ formatUptime(sysData.uptime_seconds) }}</span><span class="sl">运行时间</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.memory_mb }} MB</span><span class="sl">内存</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.cpu_percent }}%</span><span class="sl">CPU</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.models_loaded?.length || 0 }}</span><span class="sl">模型数</span></div>
          </div>
          <div class="section">
            <h2>系统信息</h2>
            <p class="system-text">{{ sysData.python_version }}</p>
          </div>
        </template>
      </section>
    </div>

    <div v-if="editTrack" class="modal-mask" @click.self="closeEdit">
      <form class="edit-modal" @submit.prevent="saveTrack">
        <div class="modal-head">
          <h2>编辑歌曲</h2>
          <button type="button" class="modal-close" @click="closeEdit">×</button>
        </div>
        <label>歌曲名<input v-model="editForm.title" required /></label>
        <label>专辑<input v-model="editForm.album" /></label>
        <div class="form-grid">
          <label>年份<input v-model.number="editForm.year" type="number" /></label>
          <label>流派<input v-model="editForm.genre" /></label>
          <label>热度<input v-model.number="editForm.popularity" type="number" step="0.1" /></label>
        </div>
        <label>封面地址<input v-model="editForm.image_url" /></label>
        <label>试听地址<input v-model="editForm.preview_url" /></label>
        <p v-if="editError" class="error">{{ editError }}</p>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="closeEdit">取消</button>
          <button type="submit" class="btn btn-primary" :disabled="savingTrack">{{ savingTrack ? '保存中...' : '保存' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue'

const password = ref('')
const error = ref('')
const loading = ref(false)
const loggedIn = ref(false)
const tab = ref('overview')
let adminToken = ''

const tabs = [
  { id: 'overview', label: '概览' },
  { id: 'users', label: '用户' },
  { id: 'tracks', label: '歌曲' },
  { id: 'feedback', label: '反馈' },
  { id: 'comments', label: '评论' },
  { id: 'data', label: 'iTunes数据' },
  { id: 'logs', label: '推荐日志' },
  { id: 'actions', label: '操作日志' },
  { id: 'models', label: '模型' },
  { id: 'system', label: '系统' },
]

const stats = ref({})
const statsLoading = ref(false)
const userList = ref([])
const usersLoading = ref(false)
const trackList = ref([])
const tracksLoading = ref(false)
const trackSearch = ref('')
const trackTotal = ref(0)
const trackPage = ref(1)
const trackSize = ref(50)
const trackSortBy = ref('id')
const trackSortOrder = ref('asc')
const fbData = reactive({ total_likes: 0, total_dislikes: 0, top_liked: [], top_disliked: [] })
const feedbackLoading = ref(false)
const commentList = ref([])
const commentsTotal = ref(0)
const commentsLoading = ref(false)
const dataSources = reactive({ sources: [], import_runs: [] })
const dataLoading = ref(false)
const logList = ref([])
const logsTotal = ref(0)
const logsLoading = ref(false)
const logSearch = ref('')
const logModel = ref('')
const actionLogList = ref([])
const actionLogsTotal = ref(0)
const actionLogsLoading = ref(false)
const actionFilter = ref('')
const actionStatus = ref('')
const actionSearch = ref('')
const metrics = ref({})
const metricsLoading = ref(false)
const metricsError = ref('')
const metricJob = ref(null)
const metricSampleUsers = ref(50)
let metricsPollTimer = null
const sysData = reactive({ uptime_seconds: 0, memory_mb: 0, cpu_percent: 0, models_loaded: [], python_version: '' })
const sysLoading = ref(false)
const retraining = ref(false)
const retrainMsg = ref('')
const retrainOk = ref(false)
const editTrack = ref(null)
const editForm = reactive({ title: '', album: '', year: 0, genre: '', popularity: 0, image_url: '', preview_url: '' })
const editError = ref('')
const savingTrack = ref(false)

const limitedGenreDistribution = computed(() => (stats.value.genre_distribution || []).slice(0, 12))
const trackMaxPage = computed(() => Math.max(1, Math.ceil((trackTotal.value || 0) / trackSize.value)))
const itunesSources = computed(() => (dataSources.sources || []).filter((s) => String(s.source || '').toLowerCase() === 'itunes'))
const itunesImportRuns = computed(() => (dataSources.import_runs || []).filter((r) => String(r.source || '').toLowerCase().includes('itunes')))
const metricProgress = computed(() => Math.max(0, Math.min(100, Number(metricJob.value?.progress || 0))))
const metricElapsed = computed(() => formatDurationSeconds(metricJob.value?.elapsed_seconds || 0))

async function doLogin() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || '登录失败')
    adminToken = data.token
    loggedIn.value = true
    await loadStats()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function logout() {
  adminToken = ''
  loggedIn.value = false
  password.value = ''
}

async function adminFetch(url, opts = {}) {
  const res = await fetch(url, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}), Authorization: 'Bearer ' + adminToken },
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || '请求失败')
  return data
}

async function switchTab(next) {
  tab.value = next
  if (next === 'overview') await loadStats()
  if (next === 'users') await loadUsers()
  if (next === 'tracks') await loadTracks()
  if (next === 'feedback') await loadFeedback()
  if (next === 'comments') await loadComments()
  if (next === 'data') await loadDataSources()
  if (next === 'logs') await loadLogs()
  if (next === 'actions') await loadActionLogs()
  if (next === 'models') await loadMetrics()
  if (next === 'system') await loadSystem()
}

async function loadStats() {
  statsLoading.value = true
  try { stats.value = await adminFetch('/api/admin/stats') } finally { statsLoading.value = false }
}

async function loadUsers() {
  usersLoading.value = true
  try { userList.value = (await adminFetch('/api/admin/users?size=100')).items || [] } finally { usersLoading.value = false }
}

async function loadTracks(nextPage = trackPage.value) {
  tracksLoading.value = true
  trackPage.value = Math.max(1, nextPage)
  try {
    const q = trackSearch.value ? '&search=' + encodeURIComponent(trackSearch.value) : ''
    const sort = '&sort_by=' + encodeURIComponent(trackSortBy.value) + '&sort_order=' + encodeURIComponent(trackSortOrder.value)
    const data = await adminFetch('/api/admin/tracks?page=' + trackPage.value + '&size=' + trackSize.value + q + sort)
    trackList.value = data.items || []
    trackTotal.value = data.total || 0
  } finally {
    tracksLoading.value = false
  }
}

function resetTrackPage() {
  trackPage.value = 1
  return loadTracks(1)
}

async function loadFeedback() {
  feedbackLoading.value = true
  try { Object.assign(fbData, await adminFetch('/api/admin/feedback')) } finally { feedbackLoading.value = false }
}

async function loadComments() {
  commentsLoading.value = true
  try {
    const data = await adminFetch('/api/admin/comments?page=1&size=100')
    commentList.value = data.items || []
    commentsTotal.value = data.total || 0
  } finally {
    commentsLoading.value = false
  }
}

async function loadDataSources() {
  dataLoading.value = true
  try { Object.assign(dataSources, await adminFetch('/api/admin/data-sources')) } finally { dataLoading.value = false }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const p = new URLSearchParams({ page: 1, size: 100 })
    if (logSearch.value.trim()) p.set('search', logSearch.value.trim())
    if (logModel.value.trim()) p.set('model_name', logModel.value.trim())
    const data = await adminFetch('/api/admin/recommendation-logs?' + p)
    logList.value = data.items || []
    logsTotal.value = data.total || 0
  } finally {
    logsLoading.value = false
  }
}

async function loadActionLogs() {
  actionLogsLoading.value = true
  try {
    const p = new URLSearchParams({ page: 1, size: 100 })
    if (actionFilter.value) p.set('action_type', actionFilter.value)
    if (actionStatus.value) p.set('status', actionStatus.value)
    if (actionSearch.value.trim()) p.set('search', actionSearch.value.trim())
    const data = await adminFetch('/api/admin/action-logs?' + p)
    actionLogList.value = data.items || []
    actionLogsTotal.value = data.total || 0
  } finally {
    actionLogsLoading.value = false
  }
}

function actionLabel(type) {
  const labels = {
    audio_play_request: '播放请求',
    audio_loadedmetadata: '音频加载',
    audio_playing: '开始播放',
    audio_paused: '暂停播放',
    audio_ended: '播放结束',
    audio_error: '播放错误',
    audio_play_error: '播放异常',
    audio_missing_source: '缺少音频',
    audio_pause_request: '暂停请求',
    audio_seek: '拖动进度',
    feedback: '用户反馈',
  }
  return labels[type] || type
}

async function loadMetrics() {
  clearMetricsPoll()
  metricsLoading.value = true
  metricsError.value = ''
  metricJob.value = null
  try {
    const job = await adminFetch('/api/admin/model-metrics/jobs', {
      method: 'POST',
      body: JSON.stringify({ sample_users: metricSampleUsers.value, n: 10 }),
    })
    metricJob.value = job
    pollMetricsJob(job.job_id)
  } catch (e) {
    metricsError.value = e.message || '模型指标加载失败'
    metricsLoading.value = false
  }
}

function clearMetricsPoll() {
  if (metricsPollTimer) {
    clearTimeout(metricsPollTimer)
    metricsPollTimer = null
  }
}

async function pollMetricsJob(jobId) {
  try {
    const job = await adminFetch('/api/admin/model-metrics/jobs/' + jobId)
    metricJob.value = job
    if (job.status === 'completed') {
      metrics.value = job.result || {}
      metricsLoading.value = false
      clearMetricsPoll()
      return
    }
    if (job.status === 'error') {
      metricsError.value = job.error || job.message || '模型评估失败'
      metricsLoading.value = false
      clearMetricsPoll()
      return
    }
    metricsPollTimer = setTimeout(() => pollMetricsJob(jobId), 800)
  } catch (e) {
    metricsError.value = e.message || '模型评估进度查询失败'
    metricsLoading.value = false
    clearMetricsPoll()
  }
}

async function loadSystem() {
  sysLoading.value = true
  try { Object.assign(sysData, await adminFetch('/api/admin/system')) } finally { sysLoading.value = false }
}

async function deleteUser(id) {
  if (!confirm('确定删除用户 ' + id + ' 及其所有数据？')) return
  await adminFetch('/api/admin/users/delete', { method: 'POST', body: JSON.stringify({ user_id: id }) })
  await Promise.all([loadUsers(), loadStats()])
}

async function deleteTrack(id) {
  if (!confirm('确定删除歌曲 ' + id + '？')) return
  await adminFetch('/api/admin/tracks/delete', { method: 'POST', body: JSON.stringify({ track_id: id }) })
  await Promise.all([loadTracks(), loadStats()])
}

async function deleteComment(id) {
  if (!confirm('确定删除评论 ' + id + '？')) return
  await adminFetch('/api/admin/comments/' + id, { method: 'DELETE' })
  await loadComments()
}

function openEdit(track) {
  editTrack.value = track
  Object.assign(editForm, {
    title: track.title || '',
    album: track.album || '',
    year: track.year || 0,
    genre: track.genre || '',
    popularity: track.popularity || 0,
    image_url: track.image_url || '',
    preview_url: track.preview_url || '',
  })
  editError.value = ''
}

function closeEdit() {
  editTrack.value = null
  editError.value = ''
}

async function saveTrack() {
  savingTrack.value = true
  editError.value = ''
  try {
    await adminFetch('/api/admin/tracks/' + editTrack.value.id, { method: 'PUT', body: JSON.stringify(editForm) })
    closeEdit()
    await loadTracks()
  } catch (e) {
    editError.value = e.message
  } finally {
    savingTrack.value = false
  }
}

async function retrainModel(force) {
  retraining.value = true
  retrainMsg.value = ''
  try {
    const data = await adminFetch('/api/admin/retrain', { method: 'POST', body: JSON.stringify({ force }) })
    retrainMsg.value = data.message || '模型重新训练完成'
    retrainOk.value = true
    await loadMetrics()
  } catch (e) {
    retrainMsg.value = e.message
    retrainOk.value = false
  } finally {
    retraining.value = false
  }
}

function barWidth(count) {
  const rows = stats.value.genre_distribution || [{ cnt: 1 }]
  const max = Math.max(...rows.map(g => g.cnt), 1)
  return (count / max) * 100
}

function percent(value) {
  return ((Number(value) || 0) * 100).toFixed(1) + '%'
}

function formatUptime(seconds) {
  const s = Number(seconds) || 0
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h > 0 ? h + '小时 ' + m + '分钟' : m + '分钟'
}

function formatDurationSeconds(seconds) {
  const s = Math.floor(Number(seconds) || 0)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}小时 ${m}分钟 ${sec}秒`
  if (m > 0) return `${m}分钟 ${sec}秒`
  return `${sec}秒`
}

onUnmounted(clearMetricsPoll)
</script>

<style scoped>
.auth-card{max-width:380px;margin:60px auto;background:var(--color-surface);border-radius:var(--radius);padding:32px;text-align:center}
.auth-card h1{font-size:22px;margin-bottom:8px}.desc,.hint{color:var(--color-text-muted);font-size:13px}.hint{margin-top:12px}.switch{font-size:13px;margin-top:12px}.switch a,.user-link{color:var(--color-primary-light);text-decoration:none}
form{display:flex;flex-direction:column;gap:10px;margin-top:20px}.error{color:var(--color-dislike);font-size:13px}
.topbar{display:flex;justify-content:space-between;align-items:flex-start;margin:24px 0 16px}.topbar h1{font-size:22px}.topbar-sub{font-size:13px;color:var(--color-text-muted);margin-top:2px}.topbar-right{display:flex;align-items:center;gap:12px}
.tabs{display:flex;gap:4px;margin-bottom:24px;flex-wrap:wrap}.tabs button{padding:8px 16px;border:none;border-radius:var(--radius);font-size:13px;font-weight:600;background:var(--color-surface);color:var(--color-text-muted);cursor:pointer}.tabs button.active{background:var(--color-primary);color:#fff}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:24px}.stat-grid-sm{grid-template-columns:repeat(auto-fit,minmax(120px,1fr))}
.stat-card{background:var(--color-surface);border-radius:var(--radius);padding:18px;display:flex;flex-direction:column;align-items:center}.sv{font-size:26px;font-weight:800;color:var(--color-primary-light)}.sl{font-size:12px;color:var(--color-text-muted);margin-top:4px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}.section{margin-bottom:28px}.section h2{font-size:16px;font-weight:600;margin-bottom:12px}
.simple-list{display:flex;flex-direction:column;gap:2px}.simple-row{background:var(--color-surface);border-radius:var(--radius);padding:10px 14px;display:flex;align-items:center;gap:12px}.rank{font-weight:700;color:var(--color-primary-light);width:24px}.name{flex:1;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.artist{color:var(--color-text-muted);font-size:13px}.cnt{font-size:13px;font-weight:600}
.genre-bars{display:flex;flex-direction:column;gap:6px}.genre-row{display:flex;align-items:center;gap:10px}.genre-label{width:92px;font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{flex:1;height:20px;background:var(--color-bg);border-radius:10px;overflow:hidden}.bar-fill{height:100%;background:var(--color-primary);border-radius:10px}.genre-cnt{font-size:12px;color:var(--color-text-muted);width:36px;text-align:right}
.toolbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}.search-input{flex:1;max-width:320px}.compact-input{max-width:180px}
.data-table{width:100%;border-collapse:collapse;font-size:13px}.data-table th,.data-table td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--color-border)}.data-table th{color:var(--color-text-muted);font-weight:600;white-space:nowrap}.data-table tr:hover td{background:var(--color-surface-hover)}
.td-title{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.td-album{max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.td-comment{max-width:360px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.row-actions{display:flex;gap:6px}.btn-xs{padding:3px 10px;font-size:11px}.badge-ok,.like{color:var(--color-like)}.badge-no{color:var(--color-text-muted)}.dislike{color:var(--color-dislike)}
.pagination-info,.note,.system-text{font-size:12px;color:var(--color-text-muted);margin-top:10px}.pagination-row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.pager-actions{display:flex;gap:6px}.model-list{display:flex;flex-wrap:wrap;gap:6px}.model-tag{padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;background:var(--color-bg);color:var(--color-text-muted)}.action-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.inline-control{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;color:var(--color-text-muted)}.inline-control input{width:88px;padding:7px 10px}.retrain-msg{margin-top:10px;font-size:13px}.retrain-msg.success{color:var(--color-like)}.retrain-msg.error{color:var(--color-dislike)}.loading-panel{text-align:left}.error-msg{color:var(--color-dislike);background:var(--color-surface);border-radius:var(--radius);padding:14px;font-size:13px}
.progress-card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;max-width:820px}.progress-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.progress-head h2{font-size:17px;margin:0 0 4px}.progress-head p{font-size:13px;color:var(--color-text-muted);margin:0}.progress-num{font-size:24px;font-weight:800;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.progress-track{height:12px;border-radius:999px;background:var(--color-bg);overflow:hidden;margin:16px 0 12px}.progress-fill{height:100%;background:linear-gradient(90deg,var(--color-primary),var(--color-accent));border-radius:999px;transition:width .3s ease}.progress-meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;font-size:12px;color:var(--color-text-muted)}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.56);display:flex;align-items:center;justify-content:center;padding:20px;z-index:100}.edit-modal{width:min(560px,100%);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;box-shadow:0 24px 80px rgba(0,0,0,.45);display:flex;flex-direction:column;gap:10px}.modal-head{display:flex;justify-content:space-between;align-items:center}.modal-head h2{font-size:18px}.modal-close{background:none;border:none;color:var(--color-text-muted);font-size:24px;cursor:pointer;line-height:1}.edit-modal label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--color-text-muted);font-weight:600}.edit-modal input{width:100%}.form-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:4px}
@media(max-width:900px){.two-col{grid-template-columns:1fr}.topbar{flex-direction:column;gap:10px}.data-table{display:block;overflow-x:auto}.form-grid{grid-template-columns:1fr}}
</style>
