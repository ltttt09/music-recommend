<template>
  <div class="container">
    <div class="page-header">
      <div>
        <h1>发现音乐</h1>
        <p>选择几首你喜欢的歌，系统会生成初始推荐</p>
      </div>
      <button class="btn btn-ghost btn-sm" @click="loadSeeds" :disabled="seedsLoading">刷新</button>
    </div>

    <div v-if="step === 1">
      <div v-if="seedsLoading" class="spinner"></div>
      <div v-else-if="seedError" class="error-box">
        {{ seedError }}
        <button class="btn btn-ghost btn-sm" @click="loadSeeds">重新加载</button>
      </div>
      <div v-else-if="seeds.length" class="seed-grid">
        <div
          v-for="track in seeds"
          :key="track.id"
          class="seed-card"
          :class="{ selected: selectedIds.has(track.id) }"
          @click="toggleSeed(track)"
        >
          <div class="seed-cover">
            <img
              v-if="track.image_url && !imgFailed[track.id]"
              :src="track.image_url"
              class="seed-img"
              alt=""
              loading="lazy"
              referrerpolicy="no-referrer"
              @error="imgFailed[track.id] = true"
            />
            <div v-if="!track.image_url || imgFailed[track.id]" class="seed-fallback" :style="coverStyle(track.id, track.genre)">
              <span class="seed-letter">{{ coverText(track.title) }}</span>
            </div>
            <span v-if="selectedIds.has(track.id)" class="check">&#10003;</span>
            <button v-else class="seed-play" @click.stop="play(track)" title="试听">&#9654;</button>
          </div>
          <div class="seed-info">
            <div class="seed-title">{{ track.title }}</div>
            <div class="seed-artist">{{ track.artist_name }}</div>
            <div class="tag">{{ track.genre }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">暂时没有可用于发现页的歌曲，请稍后刷新</div>
      <div class="step-actions" v-if="!seedsLoading">
        <button class="btn btn-primary" :disabled="selectedIds.size < 1" @click="getRecs">
          获取推荐（已选 {{ selectedIds.size }} 首，至少 1 首）
        </button>
      </div>
    </div>

    <div v-else>
      <div class="back-link">
        <a href="#" @click.prevent="step = 1">&larr; 重新选择</a>
      </div>
      <div v-if="recsLoading" class="spinner"></div>
      <div v-else-if="recsError" class="error-box">{{ recsError }}</div>
      <div v-else-if="recs.length" class="section">
        <h2>为你推荐</h2>
        <TrackList :items="recs" />
      </div>
      <div v-else class="empty-hint">暂无推荐结果，请重新选择歌曲</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import api from '../api.js'
import { playTrack } from '../audio.js'
import TrackList from '../components/TrackList.vue'
import { coverStyle, coverText } from '../cover.js'
import { useRecommendations } from '../composables/useRecommendations.js'

const imgFailed = reactive({})
const step = ref(1)
const seeds = ref([])
const selectedIds = ref(new Set())
const {
  items: recs,
  loading: recsLoading,
  error: recsError,
  fetchColdStart,
} = useRecommendations('cold_start')
const seedsLoading = ref(true)
const seedError = ref('')

function toggleSeed(track) {
  const next = new Set(selectedIds.value)
  next.has(track.id) ? next.delete(track.id) : next.add(track.id)
  selectedIds.value = next
}

function play(track) {
  playTrack({
    id: track.id || track.track_id,
    title: track.title,
    artist_name: track.artist_name,
    image_url: track.image_url,
    preview_url: track.preview_url,
  })
}

async function getRecs() {
  step.value = 2
  await fetchColdStart([...selectedIds.value], 10)
}

async function loadSeeds() {
  seedsLoading.value = true
  seedError.value = ''
  selectedIds.value = new Set()
  Object.keys(imgFailed).forEach((key) => delete imgFailed[key])
  try {
    const data = await api.getColdStartSeeds(20)
    seeds.value = data.items || []
    if (!seeds.value.length) seedError.value = '发现页暂无歌曲数据'
  } catch (e) {
    seedError.value = e.message || '发现页歌曲加载失败'
    seeds.value = []
  } finally {
    seedsLoading.value = false
  }
}

onMounted(loadSeeds)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.seed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.seed-card {
  background: var(--color-surface);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: all .2s;
  border: 2px solid transparent;
}
.seed-card.selected {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}
.seed-cover {
  aspect-ratio: 1;
  position: relative;
  overflow: hidden;
  background: var(--color-bg);
}
.seed-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.seed-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.seed-letter {
  font-size: 36px;
  font-weight: 800;
  font-family: Arial, "Microsoft YaHei", sans-serif;
  color: rgba(255,255,255,.35);
}
.check {
  position: absolute;
  inset: 0;
  font-size: 32px;
  color: #fff;
  background: rgba(108,92,231,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
}
.seed-play {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.6);
  color: white;
  font-size: 12px;
  cursor: pointer;
  opacity: 0;
  transition: opacity .2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.seed-card:hover .seed-play { opacity: 1; }
.seed-play:hover { background: var(--color-primary); }
.seed-info { padding: 10px 12px; }
.seed-title { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.seed-artist { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.seed-info .tag { margin-top: 6px; font-size: 10px; display: inline-block; padding: 1px 6px; border-radius: 8px; background: var(--color-bg); color: var(--color-text-muted); }
.step-actions { text-align: center; margin: 24px 0; }
.back-link { margin-bottom: 20px; }
.section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 40px 0; font-size: 14px; }
.error-box { display: flex; align-items: center; justify-content: center; gap: 10px; color: var(--color-dislike); background: var(--color-surface); border-radius: var(--radius); padding: 20px; }
</style>
