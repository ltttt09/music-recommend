<template>
  <div class="container">
    <div class="page-header"><h1>听歌洞察</h1><p v-if="user">用户：{{ user.display_name || user.username }}</p></div>

    <div v-if="!getUserId()" class="empty-hint">请先登录后查看听歌洞察</div>
    <div v-else-if="loading" class="spinner"></div>
    <div v-else-if="!stats" class="empty-hint">暂无听歌数据</div>
    <template v-else>
      <!-- 统计概览 -->
      <div class="stats">
        <div class="stat-card"><span class="stat-value">{{ stats.total_listens }}</span><span class="stat-label">总播放</span></div>
        <div class="stat-card" v-if="stats.top_genre"><span class="stat-value">{{ stats.top_genre }}</span><span class="stat-label">最爱流派</span></div>
        <div class="stat-card" v-if="stats.top_artist"><span class="stat-value">{{ stats.top_artist }}</span><span class="stat-label">最爱艺人</span></div>
        <div class="stat-card" v-if="stats.unique_tracks"><span class="stat-value">{{ stats.unique_tracks }}</span><span class="stat-label">不同歌曲</span></div>
      </div>

      <!-- 流派分布 -->
      <div class="section" v-if="genreDist.length">
        <h2>流派分布</h2>
        <div class="genre-bars">
          <div v-for="g in genreDist.slice(0, 15)" :key="g.name" class="genre-row">
            <span class="genre-label">{{ g.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{width: barWidth(g.count)+'%'}"></div></div>
            <span class="genre-cnt">{{ g.count }} 首</span>
          </div>
        </div>
      </div>

      <!-- 听歌时间趋势 -->
      <div class="section" v-if="timeTrend.length">
        <h2>听歌趋势</h2>
        <div class="trend-chart">
          <div v-for="(d, i) in timeTrend" :key="i" class="trend-bar-wrapper">
            <div class="trend-bar" :style="{height: barHeight(d.count)+'px'}"></div>
            <span class="trend-label">{{ d.label }}</span>
          </div>
        </div>
      </div>

      <!-- 时段偏好 -->
      <div class="section" v-if="hourDist.length">
        <h2>听歌时段</h2>
        <div class="hour-grid">
          <div v-for="h in hourDist" :key="h.hour" class="hour-cell" :style="{opacity: h.opacity}">
            <span class="hour-num">{{ h.hour }}时</span>
            <span class="hour-cnt">{{ h.count }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import { auth, getUserId } from '../auth.js'

// getUserId() imported from auth.js

const user = ref(null)
const stats = ref(null)
const genreDist = ref([])
const timeTrend = ref([])
const hourDist = ref([])
const loading = ref(false)

function barWidth(cnt) {
  const max = Math.max(...genreDist.value.map(g => g.count), 1)
  return (cnt / max) * 100
}

function barHeight(cnt) {
  const max = Math.max(...timeTrend.value.map(t => t.count), 1)
  return Math.max(8, (cnt / max) * 180)
}

onMounted(() => { loadInsights() })

async function loadInsights() {
  const uid = getUserId()
  if (!uid) return
  loading.value = true
  try {
    const [uData, hData] = await Promise.all([
      api.getUser(uid),
      api.getUserHistory(uid, 200)
    ])
    user.value = uData.user
    stats.value = uData.stats

    const history = hData.items || []

    // Genre distribution from history
    const genreMap = {}
    history.forEach(h => {
      const g = h.genre || h.track_genre || '其他'
      genreMap[g] = (genreMap[g] || 0) + 1
    })
    genreDist.value = Object.entries(genreMap)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)

    // Time trend by month
    const monthMap = {}
    history.forEach(h => {
      if (h.listened_at) {
        const d = new Date(h.listened_at)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        monthMap[key] = (monthMap[key] || 0) + 1
      }
    })
    timeTrend.value = Object.entries(monthMap)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-12)
      .map(([label, count]) => ({ label: label.slice(5), count }))

    // Hour distribution
    const hourMap = {}
    for (let h = 0; h < 24; h++) hourMap[h] = 0
    history.forEach(h => {
      if (h.listened_at) {
        const hour = new Date(h.listened_at).getHours()
        hourMap[hour] = (hourMap[hour] || 0) + 1
      }
    })
    const maxHour = Math.max(...Object.values(hourMap), 1)
    hourDist.value = Object.entries(hourMap).map(([hour, count]) => ({
      hour: Number(hour),
      count,
      opacity: 0.15 + (count / maxHour) * 0.85
    }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.controls { margin-bottom: 24px; }
.control-group { display: flex; flex-direction: column; gap: 6px; max-width: 220px; }
.control-group label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; }
.stats { display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }
.stat-card { background: var(--color-surface); border-radius: var(--radius); padding: 20px 24px; display: flex; flex-direction: column; min-width: 140px; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--color-primary-light); }
.stat-label { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; }
.section { margin-bottom: 32px; }
.section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.genre-bars { display: flex; flex-direction: column; gap: 6px; max-width: 500px; }
.genre-row { display: flex; align-items: center; gap: 10px; }
.genre-label { width: 80px; font-size: 13px; font-weight: 500; text-align: right; }
.bar-track { flex: 1; height: 20px; background: var(--color-bg); border-radius: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light)); border-radius: 10px; transition: width 0.5s; }
.genre-cnt { font-size: 12px; color: var(--color-text-muted); width: 40px; }
.trend-chart { display: flex; align-items: flex-end; gap: 8px; height: 200px; padding: 10px 0; }
.trend-bar-wrapper { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end; }
.trend-bar { width: 100%; max-width: 40px; background: linear-gradient(180deg, var(--color-primary-light), var(--color-primary)); border-radius: 6px 6px 0 0; transition: height 0.5s; min-height: 4px; }
.trend-label { font-size: 10px; color: var(--color-text-muted); white-space: nowrap; }
.hour-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; max-width: 500px; }
.hour-cell { background: var(--color-primary); border-radius: var(--radius); padding: 8px 4px; text-align: center; color: #fff; transition: opacity 0.3s; }
.hour-num { font-size: 12px; font-weight: 600; }
.hour-cnt { font-size: 10px; opacity: 0.8; display: block; }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 60px 0; font-size: 15px; }
@media (max-width: 768px) { .hour-grid { grid-template-columns: repeat(6, 1fr); } .trend-chart { gap: 4px; } .trend-label { font-size: 9px; } }
</style>
