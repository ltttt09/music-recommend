<template>
  <div class="container">
    <div v-if="loading" class="spinner"></div>
    <template v-else-if="playlist">
      <button class="back-btn" @click="goBack">&larr; 返回</button>
      <div class="playlist-hero">
        <div class="hero-cover">
          <img
            v-if="tracks[0]?.image_url"
            :src="tracks[0].image_url"
            class="hero-img"
            alt=""
          />
          <span v-else class="hero-icon">&#9835;</span>
        </div>
        <div class="hero-info">
          <span class="playlist-badge">歌单</span>
          <h1>{{ playlist.name }}</h1>
          <p class="track-count">{{ tracks.length }} 首歌曲</p>
          <button v-if="tracks.length" class="btn btn-primary btn-sm" @click="playAll">
            &#9654; 播放全部
          </button>
        </div>
      </div>
      <div class="section">
        <TrackList :items="tracks" :can-remove="playlist.is_owner" @remove="removeTrack" />
      </div>
    </template>
    <div v-else class="error-state">
      <h2>歌单未找到</h2>
      <button class="btn btn-primary" @click="goBack">返回首页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'
import { playTrack } from '../audio.js'
import TrackList from '../components/TrackList.vue'

const route = useRoute()
const router = useRouter()
const playlist = ref(null)
const tracks = ref([])
const loading = ref(true)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

function playAll() {
  if (tracks.value.length) {
    const t = tracks.value[0]
    playTrack({
      id: t.track_id || t.id,
      title: t.title || t.track_name,
      artist_name: t.artist_name,
      image_url: t.image_url,
      preview_url: t.preview_url,
    })
  }
}

onMounted(async () => {
  try {
    const rawId = String(route.params.id)
    let d = null
    if (rawId.startsWith('home-')) {
      const cached = JSON.parse(sessionStorage.getItem('home_recommend_playlists') || '[]')
      const local = cached.find((item) => item.id === rawId)
      if (!local) throw new Error('歌单缓存已失效')
      d = {
        playlist: { id: rawId, name: local.name, is_owner: false, creator: '系统推荐', is_system: true },
        tracks: local.tracks || [],
      }
    } else {
      try {
        d = await api.getUserPlaylist(Number(rawId))
        if (d.playlist) d.playlist.is_owner = true
      } catch {
        d = await api.getPlaylist(Number(rawId))
        if (d.playlist) d.playlist.is_owner = false
      }
    }
    playlist.value = d.playlist
    tracks.value = (d.tracks || []).map(t => ({
      ...t,
      track_id: t.track_id || t.id,
      track_name: t.title,
      score: undefined,
    }))
  } catch {
  } finally {
    loading.value = false
  }
})

async function removeTrack(item) {
  if (!playlist.value?.is_owner) return
  const trackId = item.track_id || item.id
  if (!confirm('确定从歌单中移出这首歌？')) return
  await api.removeFromPlaylist(playlist.value.id, trackId)
  tracks.value = tracks.value.filter((track) => (track.track_id || track.id) !== trackId)
}
</script>

<style scoped>
.back-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
  padding: 8px 0;
  margin: 24px 0 16px;
  display: block;
}
.back-btn:hover { color: var(--color-text); }

.playlist-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
}
.hero-cover {
  width: 180px;
  height: 180px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hero-icon {
  font-size: 56px;
  color: rgba(255,255,255,0.4);
}
.hero-info h1 {
  font-size: 24px;
  font-weight: 700;
}
.playlist-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background: var(--color-primary);
  color: #fff;
  margin-bottom: 8px;
}
.track-count {
  color: var(--color-text-muted);
  font-size: 14px;
  margin-top: 8px;
}
.hero-info .btn {
  margin-top: 12px;
}
.section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .playlist-hero {
    flex-direction: column;
    text-align: center;
  }
}
</style>
