<template>
  <div class="container">
    <div v-if="loading" class="spinner"></div>
    <div v-else class="playing-layout">
      <div class="playing-cover">
        <img v-if="track.image_url" :src="track.image_url" alt="" referrerpolicy="no-referrer" />
        <div v-else class="cover-fallback" :style="coverStyle(track.id, track.genre)">
          <span>{{ coverText(track.title) }}</span>
        </div>
      </div>
      <div class="playing-info">
        <p class="eyebrow">正在播放</p>
        <h1>{{ track.title }}</h1>
        <p class="artist">{{ track.artist_name }}</p>
        <div class="tags">
          <span v-if="track.album">{{ track.album }}</span>
          <span v-if="track.genre">{{ track.genre }}</span>
          <span v-if="track.year">{{ track.year }}</span>
          <span>{{ track.audio_type === 'full' ? '完整音频' : '30 秒试听' }}</span>
        </div>
        <div class="play-controls">
          <button class="btn btn-primary" @click="playTrack(track)">
            {{ playerState.isPlaying && playerState.currentTrack?.id === track.id ? '暂停' : '播放' }}
          </button>
          <span class="time">{{ formatTime(playerState.currentTime) }} / {{ formatTime(playerState.duration) }}</span>
        </div>
        <input
          class="detail-progress"
          type="range"
          min="0"
          :max="playerState.duration || 0"
          :value="playerState.currentTime"
          @input="seekTo(parseFloat($event.target.value))"
        />
      </div>
    </div>

    <section class="section">
      <h2>歌词</h2>
      <div class="lyrics">
        <p v-for="line in lyricLines" :key="line">{{ line }}</p>
      </div>
    </section>

    <section class="section info-grid">
      <div><span>数据源</span><strong>{{ track.source || 'itunes' }}</strong></div>
      <div><span>授权/播放</span><strong>{{ track.license || 'iTunes 试听' }}</strong></div>
      <div><span>时长</span><strong>{{ formatDuration(track.duration_ms) }}</strong></div>
      <div><span>热度</span><strong>{{ Math.round(track.popularity || 0) }}</strong></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api.js'
import { coverStyle, coverText } from '../cover.js'
import { formatTime, playerState, playTrack, seekTo } from '../audio.js'

const route = useRoute()
const loading = ref(true)
const track = ref({})

const lyricLines = computed(() => [
  '当前数据源没有提供正式歌词。',
  `你正在试听《${track.value.title || '这首歌'}》。`,
  '后续可以接入本地 LRC 文件或歌词 API，为 iTunes 歌曲匹配歌词。',
])

function formatDuration(ms) {
  if (!ms) return '-'
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${m}:${String(s).padStart(2, '0')}`
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (playerState.currentTrack?.id === id) track.value = playerState.currentTrack
  try {
    track.value = await api.getTrack(id)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.playing-layout{display:grid;grid-template-columns:280px 1fr;gap:36px;align-items:center;margin:32px 0}
.playing-cover{width:280px;aspect-ratio:1;border-radius:16px;overflow:hidden;box-shadow:0 18px 60px rgba(0,0,0,.28)}
.playing-cover img,.cover-fallback{width:100%;height:100%;object-fit:cover}
.cover-fallback{display:flex;align-items:center;justify-content:center}.cover-fallback span{font-size:88px;color:rgba(255,255,255,.45)}
.eyebrow{font-size:13px;color:var(--color-primary);font-weight:700;margin-bottom:8px}
.playing-info h1{font-size:34px;line-height:1.15}.artist{color:var(--color-text-muted);font-size:18px;margin-top:8px}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.tags span{padding:5px 10px;background:var(--color-surface);border-radius:999px;font-size:12px;color:var(--color-text-muted)}
.play-controls{display:flex;align-items:center;gap:16px;margin:22px 0 12px}.time{font-size:13px;color:var(--color-text-muted);font-variant-numeric:tabular-nums}
.detail-progress{width:100%;height:10px;appearance:none;border-radius:999px;background:linear-gradient(90deg,var(--color-primary),var(--color-border));outline:none}
.detail-progress::-webkit-slider-thumb{appearance:none;width:20px;height:20px;border-radius:50%;background:var(--color-primary-light);border:3px solid white;box-shadow:0 2px 10px rgba(0,0,0,.22)}
.section{margin-top:28px}.section h2{font-size:18px;margin-bottom:12px}.lyrics{background:var(--color-surface);border-radius:var(--radius);padding:18px;line-height:1.9;color:var(--color-text-muted)}
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.info-grid div{background:var(--color-surface);border-radius:var(--radius);padding:14px}.info-grid span{display:block;color:var(--color-text-muted);font-size:12px;margin-bottom:5px}.info-grid strong{font-size:14px}
@media(max-width:760px){.playing-layout{grid-template-columns:1fr}.playing-cover{width:100%;max-width:280px}}
</style>
