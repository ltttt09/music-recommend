<template>
  <div class="container">
    <div class="page-header">
      <h1>全部歌曲</h1>
      <p>{{ total }} 首歌曲 · 筛选你想找的音乐</p>
    </div>

    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input v-model="searchQuery" placeholder="搜索歌曲、艺术家或专辑..." @input="onSearch" />
    </div>

    <div class="sort-bar">
      <label>
        排序
        <select v-model="sortBy" @change="applyFilters">
          <option value="popularity">热度</option>
          <option value="year">年份</option>
          <option value="title">歌名</option>
          <option value="artist">艺人</option>
          <option value="duration">时长</option>
          <option value="created">新增</option>
        </select>
      </label>
      <label>
        顺序
        <select v-model="sortOrder" @change="applyFilters">
          <option value="desc">从高到低</option>
          <option value="asc">从低到高</option>
        </select>
      </label>
    </div>

    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">流派</span>
        <div class="filter-tags">
          <button class="ftag" :class="{ active: !activeGenre }" @click="setGenre('')">全部</button>
          <button v-for="g in genres.slice(0, 10)" :key="g" class="ftag" :class="{ active: activeGenre === g }" @click="setGenre(g)">{{ g }}</button>
          <select v-if="genres.length>10" v-model="activeGenre" @change="applyFilters" class="ftag ftag-select"><option value="">更多...</option><option v-for="g in genres.slice(10)" :key="g" :value="g">{{ g }}</option></select>
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
          <button v-for="l in languages" :key="l.code" class="ftag" :class="{ active: activeLang===l.code }" @click="setLang(l.code)">{{ l.flag }} {{ l.name }}</button>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>{{ sectionTitle }}</h2>
      <div v-if="loading" class="skeleton-grid">
        <div v-for="i in 8" :key="i" class="skeleton-card"><div class="skeleton skeleton-cover"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
      </div>
      <div v-else class="track-grid">
        <TrackCard v-for="t in tracks" :key="t.id" :track="t" />
      </div>
      <div v-if="tracks.length===0&&!loading" class="empty-hint">没有匹配的歌曲，换个筛选条件试试</div>
      <div v-if="hasMore&&!loading" ref="sentinel" class="load-more"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '../api.js'
import TrackCard from '../components/TrackCard.vue'

const tracks=ref([]);const genres=ref([]);const total=ref(0);const page=ref(1);const hasMore=ref(true)
const searchQuery=ref('');const activeGenre=ref('');const activeLang=ref('');const activeDecade=ref('')
const sortBy=ref('popularity');const sortOrder=ref('desc')
const loading=ref(true)
const sentinel=ref(null);let observer=null;let searchTimer=null

const decades=[{label:'1950s',from:1950,to:1959},{label:'1960s',from:1960,to:1969},{label:'1970s',from:1970,to:1979},{label:'1980s',from:1980,to:1989},{label:'1990s',from:1990,to:1999},{label:'2000s',from:2000,to:2009},{label:'2010s',from:2010,to:2019},{label:'2020s',from:2020,to:2029}]
const languages=[{code:'CN',name:'中文',flag:'🇨🇳'},{code:'JP',name:'日语',flag:'🇯🇵'},{code:'KR',name:'韩语',flag:'🇰🇷'},{code:'FR',name:'法语',flag:'🇫🇷'},{code:'ES',name:'西语',flag:'🇪🇸'},{code:'IN',name:'印度',flag:'🇮🇳'},{code:'AR',name:'阿拉伯',flag:'🇸🇦'},{code:'RU',name:'俄语',flag:'🇷🇺'},{code:'BR',name:'巴西',flag:'🇧🇷'},{code:'DE',name:'德语',flag:'🇩🇪'}]

const sectionTitle=computed(()=>{const p=[];if(searchQuery.value)p.push('搜索结果');else if(activeGenre.value)p.push(activeGenre.value);else if(activeLang.value)p.push(languages.find(l=>l.code===activeLang.value)?.name||'');else if(activeDecade.value)p.push(activeDecade.value);else p.push('全部歌曲');return p.join(' · ')})

function getYearRange(){if(!activeDecade.value)return{from:0,to:0};const d=decades.find(d=>d.label===activeDecade.value);return d?{from:d.from,to:d.to}:{from:0,to:0}}

async function loadTracks(reset=false){
  if(reset){page.value=1;tracks.value=[];hasMore.value=true}
  loading.value=true
  try{const yr=getYearRange();const data=await api.getTracks(page.value,20,searchQuery.value,activeGenre.value,yr.from,yr.to,activeLang.value,sortBy.value,sortOrder.value);if(reset)tracks.value=data.items;else tracks.value.push(...data.items);total.value=data.total;hasMore.value=page.value*20<data.total}catch{}finally{loading.value=false}
}
async function loadGenres(){try{const d=await api.getGenres();genres.value=d.genres||[]}catch{}}
function onSearch(){clearTimeout(searchTimer);searchTimer=setTimeout(()=>applyFilters(),300)}
function setGenre(g){activeGenre.value=g;applyFilters()}
function setLang(l){activeLang.value=l;applyFilters()}
function setDecade(d){activeDecade.value=d;applyFilters()}
function applyFilters(){loadTracks(true)}

function setupObserver(){if(observer)observer.disconnect();observer=new IntersectionObserver(e=>{if(e[0].isIntersecting&&hasMore.value&&!loading.value){page.value++;loadTracks()}},{threshold:0.1})}
watch(sentinel,el=>{if(el)observer?.observe(el)})
onMounted(()=>{setupObserver();loadTracks(true);loadGenres()})
onUnmounted(()=>observer?.disconnect())
</script>

<style scoped>
.search-box{display:flex;align-items:center;max-width:520px;background:var(--color-surface);border:1px solid var(--color-border);border-radius:14px;padding:0 16px;margin-bottom:16px;transition:border-color .2s}
.search-box:focus-within{border-color:var(--color-primary);box-shadow:0 0 0 3px rgba(108,92,231,.15)}
.search-icon{font-size:18px;opacity:.5}
.search-box input{flex:1;border:none;background:transparent;padding:14px 10px;font-size:16px;outline:none}
.sort-bar{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.sort-bar label{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--color-text-muted)}
.sort-bar select{min-width:120px;padding:8px 12px;font-size:13px}
.filter-bar{background:var(--color-surface);border-radius:14px;padding:16px;margin-bottom:24px;display:flex;flex-direction:column;gap:12px;border:1px solid var(--color-border)}
.filter-group{display:flex;align-items:flex-start;gap:10px}
.filter-label{font-size:12px;font-weight:700;color:var(--color-text-muted);min-width:48px;padding-top:6px;flex-shrink:0}
.filter-tags{display:flex;flex-wrap:wrap;gap:6px;flex:1}
.ftag{padding:5px 12px;border-radius:20px;border:1px solid var(--color-border);background:var(--color-bg);font-size:12px;color:var(--color-text-muted);cursor:pointer;transition:all .15s;white-space:nowrap}
.ftag:hover{border-color:var(--color-primary);color:var(--color-text)}
.ftag.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff;font-weight:600}
.ftag-select{appearance:auto}
.section{margin-bottom:40px}.section h2{font-size:18px;font-weight:600;margin-bottom:16px}
.track-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:16px}
.skeleton-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:16px}
.load-more{height:1px}
.empty-hint{text-align:center;color:var(--color-text-muted);padding:40px 0;font-size:14px}
@media(max-width:768px){.filter-bar{padding:12px}.filter-group{flex-direction:column;gap:6px}.track-grid,.skeleton-grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}}
</style>
