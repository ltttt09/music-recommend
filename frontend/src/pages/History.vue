<template>
  <div class="container">
    <div class="page-header"><h1>听歌历史</h1><p v-if="user">用户：{{ user.display_name || user.username }}</p></div>
    <div v-if="loading" class="spinner"></div>
    <template v-else>
      <div class="stats" v-if="stats">
        <div class="stat-card"><span class="stat-value">{{ stats.total_listens }}</span><span class="stat-label">总播放</span></div>
        <div class="stat-card" v-if="stats.top_genre"><span class="stat-value">{{ stats.top_genre }}</span><span class="stat-label">最爱流派</span></div>
        <div class="stat-card" v-if="stats.top_artist"><span class="stat-value">{{ stats.top_artist }}</span><span class="stat-label">最爱艺人</span></div>
      </div>
      <div class="section"><h2>最近播放</h2>
        <div v-if="history.length===0" class="empty">暂无听歌记录</div>
        <div v-else class="history-list">
          <div v-for="h in pagedHistory" :key="h.id" class="history-row">
            <router-link :to="'/track/'+h.track_id" class="history-link">
              <span class="h-time">{{ formatDate(h.listened_at) }}</span>
              <span class="h-title">{{ h.track_title }}</span>
              <span class="h-artist">{{ h.artist_name }}</span>
            </router-link>
          </div>
        </div>
        <div class="pager"><button class="btn btn-ghost btn-sm" :disabled="page<=1" @click="page--">上一页</button><span>{{ page }} / {{ pages }}</span><button class="btn btn-ghost btn-sm" :disabled="page>=pages" @click="page++">下一页</button></div>
      </div>
    </template>
  </div>
</template>
<script setup>
import {computed,ref,onMounted} from 'vue';import api from'../api.js';import { auth } from '../auth.js'
function getUserId(){return auth.userId||Number(localStorage.getItem('user_id'))||0}
const history=ref([]);const user=ref(null);const stats=ref(null);const loading=ref(true)
const page=ref(1);const size=20
const pagedHistory=computed(()=>history.value.slice((page.value-1)*size,page.value*size))
const pages=computed(()=>Math.max(1,Math.ceil(history.value.length/size)))
function formatDate(d){if(!d)return'';return new Date(d).toLocaleDateString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
onMounted(async()=>{
  const uid=getUserId()
  if(!uid){loading.value=false;return}
  try{const[hD,uD]=await Promise.all([api.getUserHistory(uid,200),api.getUser(uid)]);history.value=hD.items||[];user.value=uD.user;stats.value=uD.stats}catch(e){}finally{loading.value=false}
})
</script>
<style scoped>
.stats{display:flex;gap:16px;margin-bottom:32px;flex-wrap:wrap}
.stat-card{background:var(--color-surface);border-radius:var(--radius);padding:20px 24px;display:flex;flex-direction:column;min-width:140px}
.stat-value{font-size:24px;font-weight:700;color:var(--color-primary-light)}.stat-label{font-size:12px;color:var(--color-text-muted);margin-top:4px}
.section h2{font-size:18px;font-weight:600;margin-bottom:16px}
.history-list{display:flex;flex-direction:column;gap:2px}
.history-row{background:var(--color-surface);border-radius:var(--radius);padding:10px 14px}
.history-link{display:flex;align-items:center;gap:16px;text-decoration:none;color:inherit}
.h-time{font-size:12px;color:var(--color-text-muted);min-width:90px}
.h-title{font-size:14px;font-weight:500;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-artist{font-size:13px;color:var(--color-text-muted)}.empty{text-align:center;color:var(--color-text-muted);padding:40px 0}
.pager{display:flex;align-items:center;justify-content:center;gap:12px;margin:18px 0;color:var(--color-text-muted);font-size:13px}
</style>
