<template>
  <div class="container">
    <div class="page-header"><h1>我喜欢的歌曲</h1><p>这里展示你标记为喜欢的歌曲</p></div>
    <div v-if="loading" class="spinner"></div>
    <div v-else-if="items.length" class="section">
      <TrackList :items="items" show-unlike @unlike="unlikeTrack" />
    </div>
    <div v-else class="empty-hint">还没有喜欢任何歌曲，去发现页听听看吧</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import { auth, getUserId } from '../auth.js'
import TrackList from '../components/TrackList.vue'

// getUserId() imported from auth.js

const items = ref([])
const loading = ref(true)

async function unlikeTrack(track) {
  const uid = getUserId()
  if (!uid) return
  const id = track.id || track.track_id
  const prev = items.value
  items.value = items.value.filter((item) => (item.id || item.track_id) !== id)
  try {
    await api.submitFeedback(uid, id, 1)
  } catch (e) {
    console.error(e)
    items.value = prev
    alert(e.message || '取消喜欢失败')
  }
}

onMounted(async () => {
  if (!getUserId()) {
    loading.value = false
    return
  }
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
