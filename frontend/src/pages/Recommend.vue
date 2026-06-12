<template>
  <div class="container">
    <div class="page-header"><h1>个性化推荐</h1><p>选择推荐模型，获取专属推荐</p></div>
    <div class="controls">
      <div class="control-group"><label>推荐模型</label><select v-model="selectedModel"><option v-for="m in models" :key="m" :value="m">{{ MODEL_NAMES[m] || m }}</option></select></div>
      <button class="btn btn-primary" @click="fetchRecs" :disabled="recsLoading">{{ recsLoading ? '加载中...' : '获取推荐' }}</button>
    </div>
    <div class="user-links">
      <router-link to="/history">查看听歌历史</router-link>
      <span class="sep">|</span>
      <a href="#" @click.prevent="fetchArtists">推荐艺人</a>
    </div>

    <div v-if="recsLoading" class="spinner"></div>
    <div v-else-if="recsError" class="error-msg">{{ recsError }}</div>
    <div v-else-if="recs.length" class="results">
      <div class="recs-header">
        <h2>推荐结果 <span class="model-tag">{{ MODEL_NAMES[selectedModel] || selectedModel }}</span></h2>
        <button class="btn btn-ghost btn-sm" @click="fetchRecs" :disabled="recsLoading">换一批</button>
      </div>
      <div class="recs-grid">
        <div v-for="item in recs" :key="item.id" class="rec-card">
          <router-link :to="'/track/' + item.id" class="rec-link">
            <span class="rec-cover" :style="coverStyle(item.id, item.genre)">{{ coverText(item.title) }}</span>
            <div class="rec-meta">
              <span class="rec-title">{{ item.title }}</span>
              <span class="rec-artist">{{ item.artist_name }}</span>
              <span class="rec-reason">{{ item.reason || '综合你的历史偏好排序' }}</span>
              <span class="rec-genre">{{ modelSources(item) }}</span>
            </div>
          </router-link>
          <div class="rec-actions">
            <span class="rec-score">{{ ((item.score || 0) * 100).toFixed(0) }}%</span>
            <button class="btn-info-icon" @click="openExplain(item)" title="推荐解释">i</button>
            <button class="btn-like-icon" :class="{ active: item.user_liked }" @click="quickFeedback(item, 1)" :title="item.user_liked ? '已喜欢' : '喜欢'">&#10003;</button>
            <button class="btn-dislike-icon" :class="{ active: item.user_skipped }" @click="quickFeedback(item, -1)" :title="item.user_skipped ? '已跳过' : '跳过'">&#10007;</button>
          </div>
        </div>
      </div>
      <p v-if="toast" class="toast">{{ toast }}</p>
    </div>

    <div v-if="artists.length" class="section">
      <h2>推荐艺人</h2>
      <div class="artist-grid">
        <div v-for="a in artists" :key="a.id" class="artist-card">
          <span class="artist-avatar">{{ (a.name || '?').charAt(0) }}</span>
          <span class="artist-name">{{ a.name }}</span>
          <span class="artist-genre">{{ a.genres }}</span>
          <span class="artist-score">匹配 {{ ((a.match_score || 0) * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <div v-if="!recs.length && !recsLoading" class="section">
      <h2>排名</h2>
      <TrackList :items="trending" />
    </div>

    <div v-if="explainItem" class="modal-mask" @click.self="explainItem = null">
      <div class="explain-modal">
        <div class="modal-head">
          <h2>推荐解释</h2>
          <button class="modal-close" @click="explainItem = null">×</button>
        </div>
        <div class="modal-track">
          <span class="rec-cover large" :style="coverStyle(explainItem.id, explainItem.genre)">{{ coverText(explainItem.title) }}</span>
          <div>
            <strong>{{ explainItem.title }}</strong>
            <p>{{ explainItem.artist_name }} · {{ explainItem.genre || '未知流派' }}</p>
          </div>
        </div>
        <div class="explain-grid">
          <div><span>匹配分数</span><strong>{{ ((explainItem.score || 0) * 100).toFixed(1) }}%</strong></div>
          <div><span>来源模型</span><strong>{{ modelSources(explainItem) }}</strong></div>
          <div class="full"><span>推荐理由</span><strong>{{ explainItem.reason || '综合你的历史偏好排序' }}</strong></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'; import api from '../api.js'
import TrackList from '../components/TrackList.vue'
import { coverStyle, coverText } from '../cover.js'

function getUserId() { return Number(localStorage.getItem('user_id')) || 1 }

const MODEL_NAMES = { hybrid:'混合推荐', itemcf:'物品协同过滤', usercf:'用户协同过滤', svd:'矩阵分解SVD', song2vec:'歌曲嵌入', sequence:'序列推荐', cold_start:'冷启动', genre:'流派回退' }
const models=ref(['hybrid']); const selectedModel=ref('hybrid')
const recs=ref([]); const recsLoading=ref(false); const recsError=ref('')
const artists=ref([]); const trending=ref([]); const toast=ref('')
const explainItem=ref(null)

function modelSources(item){return (item.source_models||[]).map(m=>MODEL_NAMES[m]||m).join(' / ') || item.genre || ''}
function openExplain(item){explainItem.value=item}

async function quickFeedback(item,rating){
  if(rating<0&&!confirm('确定跳过这首歌？系统会在一段时间内减少推荐它，反复跳过会延长屏蔽时间。'))return
  try{
    await api.submitFeedback(getUserId(),item.id,rating,selectedModel.value)
    if(rating>0)item.user_liked=true
    else{
      item.user_skipped=true
      recs.value=recs.value.filter(t=>t.id!==item.id)
    }
    toast.value=rating>0?'已标记喜欢':'已跳过，短期内不会再推荐'
    setTimeout(()=>toast.value='',2000)
  }catch(e){toast.value='操作失败';setTimeout(()=>toast.value='',2000)}
}

onMounted(async()=>{
  try{const d=await api.getModels();models.value=d.models||['hybrid']}catch(e){}
  try{const d=await api.getTrending(6);trending.value=d.items||[]}catch(e){}
})

async function fetchRecs(){
  recsLoading.value=true; recsError.value=''; artists.value=[]
  try{const d=await api.getRecommendations(getUserId(),selectedModel.value);recs.value=d.items||[]}catch(e){recsError.value=e.message}finally{recsLoading.value=false}
}

async function fetchArtists(){
  try{const d=await api.getArtistRecommendations(getUserId(),10);artists.value=d.items||[]}catch(e){}
}
</script>

<style scoped>
.controls{display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:16px}
.control-group{display:flex;flex-direction:column;gap:6px}
.control-group label{font-size:12px;font-weight:600;color:var(--color-text-muted);text-transform:uppercase}
.control-group select{min-width:200px}
.user-links{margin-bottom:24px;font-size:13px}.user-links a{color:var(--color-primary-light)}.sep{margin:0 8px;color:var(--color-border)}
.recs-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.recs-header h2{font-size:18px;font-weight:600;margin:0}
.results h2{font-size:18px;font-weight:600;margin-bottom:16px}
.model-tag{font-size:11px;padding:2px 8px;border-radius:10px;background:var(--color-primary);color:#fff;vertical-align:middle;margin-left:8px}
.recs-grid{display:flex;flex-direction:column;gap:2px}
.rec-card{background:var(--color-surface);border-radius:var(--radius);padding:12px 14px;display:flex;align-items:center;justify-content:space-between}
.rec-link{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;flex:1;min-width:0}
.rec-cover{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:Arial,"Microsoft YaHei",sans-serif;font-weight:700;font-size:16px;color:rgba(255,255,255,.5);flex-shrink:0}
.rec-meta{display:flex;flex-direction:column;min-width:0}.rec-title{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rec-artist{font-size:12px;color:var(--color-text-muted);margin-top:2px}.rec-reason{font-size:12px;color:var(--color-accent);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rec-genre{font-size:10px;color:var(--color-text-muted);margin-top:2px;opacity:.7}
.rec-actions{display:flex;align-items:center;gap:10px;flex-shrink:0}.rec-score{font-size:13px;font-weight:700;color:var(--color-accent)}
.btn-like-icon,.btn-dislike-icon,.btn-info-icon{width:28px;height:28px;border-radius:50%;border:none;font-size:14px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.btn-info-icon{background:var(--color-bg);color:var(--color-text-muted);font-weight:700}
.btn-info-icon:hover{background:var(--color-primary);color:#fff}
.btn-like-icon{background:var(--color-like);color:#fff}.btn-dislike-icon{background:var(--color-dislike);color:#fff}
.btn-like-icon.active,.btn-dislike-icon.active{box-shadow:0 0 0 2px rgba(255,255,255,.22);filter:brightness(1.08)}
.error-msg{color:var(--color-dislike);padding:20px;background:var(--color-surface);border-radius:var(--radius)}
.toast{text-align:center;color:var(--color-like);font-size:13px;margin-top:12px}
.section{margin-top:40px}.section h2{font-size:18px;font-weight:600;margin-bottom:16px}
.artist-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.artist-card{background:var(--color-surface);border-radius:var(--radius);padding:16px;display:flex;flex-direction:column;align-items:center;gap:6px}
.artist-avatar{width:48px;height:48px;border-radius:50%;background:var(--color-primary);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:22px}
.artist-name{font-size:14px;font-weight:600}.artist-genre{font-size:11px;color:var(--color-text-muted)}.artist-score{font-size:12px;color:var(--color-accent)}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.56);display:flex;align-items:center;justify-content:center;padding:20px;z-index:100}
.explain-modal{width:min(520px,100%);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;box-shadow:0 24px 80px rgba(0,0,0,.45)}
.modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.modal-head h2{font-size:18px;margin:0}
.modal-close{background:none;border:none;color:var(--color-text-muted);font-size:24px;cursor:pointer;line-height:1}
.modal-track{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.modal-track p{font-size:13px;color:var(--color-text-muted);margin-top:4px}
.rec-cover.large{width:56px;height:56px;font-size:22px}
.explain-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.explain-grid div{background:var(--color-bg);border-radius:var(--radius);padding:12px}
.explain-grid .full{grid-column:1/-1}
.explain-grid span{display:block;font-size:12px;color:var(--color-text-muted);margin-bottom:5px}
.explain-grid strong{font-size:14px;font-weight:600}
</style>
