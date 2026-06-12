<template>
  <div class="container">
    <div class="page-header"><h1>我的收藏</h1><p>收藏的歌曲列表</p></div>
    <div v-if="loading" class="spinner"></div>
    <div v-else-if="items.length" class="section">
      <TrackList :items="items" />
    </div>
    <div v-else class="empty-hint">还没有收藏任何歌曲，去发现页听听看吧</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import TrackList from '../components/TrackList.vue'

function getUserId() { return Number(localStorage.getItem('user_id')) || 1 }

const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const d = await api.getFavorites(getUserId())
    items.value = d.items || []
  } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<style scoped>
.section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 60px 0; font-size: 14px; }
</style>