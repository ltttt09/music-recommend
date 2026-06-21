<template>
  <div class="container">
    <div class="page-header">
      <h1>全部歌曲</h1>
      <p>{{ total }} 首歌曲 · 第 {{ page }} / {{ totalPages }} 页</p>
    </div>

    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input v-model="searchQuery" placeholder="搜索歌曲、艺术家或专辑..." @input="onSearch" />
    </div>

    <div class="sort-bar">
      <label>排序
        <select v-model="sortBy" @change="applyFilters">
          <option value="popularity">热度</option>
          <option value="year">年份</option>
          <option value="title">歌名</option>
          <option value="artist">艺人</option>
          <option value="duration">时长</option>
          <option value="created">新增</option>
        </select>
      </label>
      <label>顺序
        <select v-model="sortOrder" @change="applyFilters">
          <option value="desc">从高到低</option>
          <option value="asc">从低到高</option>
        </select>
      </label>
      <label>每页
        <select v-model.number="pageSize" @change="applyFilters">
          <option :value="20">20</option>
          <option :value="40">40</option>
          <option :value="60">60</option>
        </select>
      </label>
    </div>

    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">流派</span>
        <div class="filter-tags">
          <button class="ftag" :class="{ active: !activeGenre }" @click="setGenre('')">全部</button>
          <button v-for="g in topGenres" :key="g.name" class="ftag" :class="{ active: activeGenre === g.name }" @click="setGenre(g.name)">
            {{ g.name }} <small>{{ g.count }}</small>
          </button>
          <select v-if="moreGenres.length" v-model="activeGenre" @change="applyFilters" class="ftag ftag-select">
            <option value="">更多...</option>
            <option v-for="g in moreGenres" :key="g.name" :value="g.name">{{ g.name }}（{{ g.count }}）</option>
          </select>
        </div>
      </div>
      <div class="filter-group">
        <span class="filter-label">年代</span>
        <div class="filter-tags">
          <button class="ftag" :class="{ active: !activeDecade }" @click="setDecade('')">不限</button>
          <button v-for="d in decades" :key="d.label" class="ftag" :class="{ active: activeDecade===d.label }" @click="setDecade(d.label)">{{ d.label }}</button>
        </div>
      </div>
      <div class="filter-group">
        <span class="filter-label">语言</span>
        <div class="filter-tags">
          <button class="ftag" :class="{ active: !activeLang }" @click="setLang('')">全部</button>
          <button v-for="l in languages" :key="l.code" class="ftag" :class="{ active: activeLang===l.code }" @click="setLang(l.code)">{{ l.name }}</button>
        </div>
      </div>
    </div>

    <section class="section">
      <h2>{{ sectionTitle }}</h2>
      <div v-if="loading" class="skeleton-grid">
        <div v-for="i in 8" :key="i" class="skeleton-card"><div class="skeleton skeleton-cover"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
      </div>
      <div v-else class="track-grid">
        <TrackCard v-for="t in tracks" :key="t.id" :track="t" />
      </div>
      <div v-if="tracks.length===0&&!loading" class="empty-hint">没有匹配的歌曲，换个筛选条件试试</div>
      <Pagination :current="page" :total="totalPages" :total-items="total" item-name="首歌曲" @page-change="goPage" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api.js'
import TrackCard from '../components/TrackCard.vue'
import Pagination from '../components/Pagination.vue'

const tracks = ref([])
const genres = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const activeGenre = ref('')
const activeLang = ref('')
const activeDecade = ref('')
const sortBy = ref('popularity')
const sortOrder = ref('desc')
const loading = ref(true)
let searchTimer = null

const decades = [{label:'1950s',from:1950,to:1959},{label:'1960s',from:1960,to:1969},{label:'1970s',from:1970,to:1979},{label:'1980s',from:1980,to:1989},{label:'1990s',from:1990,to:1999},{label:'2000s',from:2000,to:2009},{label:'2010s',from:2010,to:2019},{label:'2020s',from:2020,to:2029}]
const languages = [{code:'ZH',name:'中文'},{code:'EN',name:'英文'},{code:'JP',name:'日语'},{code:'KR',name:'韩语'},{code:'FR',name:'法语'},{code:'ES',name:'西语'},{code:'AR',name:'阿拉伯语'},{code:'RU',name:'俄语'},{code:'PT',name:'葡语'},{code:'DE',name:'德语'}]

const topGenres = computed(() => genres.value.slice(0, 10))
const moreGenres = computed(() => genres.value.slice(10))
const totalPages = computed(() => Math.max(1, Math.ceil((total.value || 0) / pageSize.value)))
const sectionTitle = computed(() => {
  if (searchQuery.value) return '搜索结果'
  if (activeGenre.value) return activeGenre.value
  if (activeLang.value) return languages.find((item) => item.code === activeLang.value)?.name || '语言筛选'
  if (activeDecade.value) return activeDecade.value
  return '全部歌曲'
})

function getYearRange() {
  const decade = decades.find((item) => item.label === activeDecade.value)
  return decade ? { from: decade.from, to: decade.to } : { from: 0, to: 0 }
}

async function loadTracks(nextPage = page.value) {
  page.value = Math.max(1, Math.min(nextPage, totalPages.value))
  loading.value = true
  try {
    const yr = getYearRange()
    const data = await api.getTracks(page.value, pageSize.value, searchQuery.value, activeGenre.value, yr.from, yr.to, activeLang.value, sortBy.value, sortOrder.value)
    tracks.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadGenres() {
  const data = await api.getGenres(80)
  genres.value = data.genres || []
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => applyFilters(), 300)
}
function setGenre(value) { activeGenre.value = value; applyFilters() }
function setLang(value) { activeLang.value = value; applyFilters() }
function setDecade(value) { activeDecade.value = value; applyFilters() }
function applyFilters() { page.value = 1; loadTracks(1) }
function goPage(value) { loadTracks(value) }

onMounted(async () => {
  await Promise.all([loadTracks(1), loadGenres()])
})
</script>

<style scoped>
.search-box{display:flex;align-items:center;max-width:560px;background:var(--color-surface);border:1px solid var(--color-border);border-radius:14px;padding:0 16px;margin-bottom:16px;animation:fadeUp .3s ease both}
.search-box:focus-within{border-color:var(--color-primary);box-shadow:0 0 0 3px rgba(108,92,231,.15)}
.search-icon{font-size:18px;opacity:.5}.search-box input{flex:1;border:none;background:transparent;padding:14px 10px;font-size:16px;outline:none}
.sort-bar{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap}.sort-bar label{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--color-text-muted)}.sort-bar select{min-width:110px;padding:8px 12px;font-size:13px}
.filter-bar{background:var(--color-surface);border-radius:14px;padding:16px;margin-bottom:24px;display:flex;flex-direction:column;gap:12px;border:1px solid var(--color-border);animation:fadeUp .3s ease .06s both}
.filter-group{display:flex;align-items:flex-start;gap:10px}.filter-label{font-size:12px;font-weight:700;color:var(--color-text-muted);min-width:48px;padding-top:6px;flex-shrink:0}.filter-tags{display:flex;flex-wrap:wrap;gap:6px;flex:1}
.ftag{padding:5px 12px;border-radius:20px;border:1px solid var(--color-border);background:var(--color-bg);font-size:12px;color:var(--color-text-muted);cursor:pointer;transition:all .15s;white-space:nowrap}.ftag small{opacity:.7;margin-left:3px}.ftag:hover{border-color:var(--color-primary);color:var(--color-text)}.ftag.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff;font-weight:600}.ftag-select{appearance:auto}
.section{margin-bottom:40px}.section h2{font-size:18px;font-weight:600;margin-bottom:16px}.track-grid,.skeleton-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:16px}
.empty-hint{text-align:center;color:var(--color-text-muted);padding:40px 0;font-size:14px}.pager{display:flex;align-items:center;justify-content:center;gap:12px;margin:24px 0;color:var(--color-text-muted);font-size:13px}
@media(max-width:768px){.filter-bar{padding:12px}.filter-group{flex-direction:column;gap:6px}.track-grid,.skeleton-grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
</style>
