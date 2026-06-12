<template>
  <div class="container">
    <div class="hero-search">
      <h1>🎵 乐荐</h1>
      <p>{{ total }} 首歌曲 · {{ genres.length }} 个流派 · 为你发现好音乐</p>
      <router-link to="/browse" class="hero-btn">探索曲库 →</router-link>
    </div>

    <div v-if="recs.length" class="section">
      <h2>为你推荐</h2>
      <div class="track-grid">
        <TrackCard v-for="t in recs" :key="t.id" :track="t" />
      </div>
    </div>
    <div v-else-if="recsLoading" class="section">
      <h2>为你推荐</h2>
      <div class="skeleton-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card"><div class="skeleton skeleton-cover"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
      </div>
    </div>

    <div class="section">
      <h2>排名</h2>
      <div v-if="trendingLoading" class="skeleton-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card"><div class="skeleton skeleton-cover"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
      </div>
      <div v-else class="track-grid">
        <TrackCard v-for="t in trending" :key="t.id" :track="t" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import TrackCard from '../components/TrackCard.vue'

const recs = ref([]); const trending = ref([]); const genres = ref([]); const total = ref(0)
const recsLoading = ref(true); const trendingLoading = ref(true)

function getUserId() { return Number(localStorage.getItem('user_id')) || 1 }

onMounted(async () => {
  try { const d = await api.getRecommendations(getUserId(), 'hybrid', 12); recs.value = d.items || [] } catch {} finally { recsLoading.value = false }
  try { const d = await api.getTrending(12); trending.value = d.items || [] } catch {} finally { trendingLoading.value = false }
  try { const d = await api.getGenres(); genres.value = d.genres || [] } catch {}
  try { const d = await api.getTracks(1, 1); total.value = d.total } catch {}
})
</script>

<style scoped>
.hero-search { text-align: center; padding: 48px 0 32px; }
.hero-search h1 { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-search p { color: var(--color-text-muted); font-size: 15px; margin-top: 8px; }
.hero-btn { display: inline-block; margin-top: 16px; padding: 10px 28px; background: var(--color-primary); color: #fff; border-radius: 24px; font-size: 14px; font-weight: 600; text-decoration: none; transition: all .2s; }
.hero-btn:hover { background: #5a4bd1; transform: translateY(-1px); }
.section { margin-bottom: 40px; }
.section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.track-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 16px; }
.skeleton-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 16px; }
@media (max-width: 768px) { .hero-search { padding: 32px 0 24px; } .hero-search h1 { font-size: 28px; } .track-grid, .skeleton-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); } }
</style>
