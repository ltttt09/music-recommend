<template>
  <div class="track-card">
    <router-link :to="'/track/' + trackId" class="card-cover-link">
      <div class="card-cover">
        <img
          v-if="track.image_url && !imgFailed"
          :src="track.image_url"
          :alt="title"
          class="cover-img"
          loading="lazy"
          referrerpolicy="no-referrer"
          @error="imgFailed = true"
        />
        <div v-if="!track.image_url || imgFailed" class="cover-fallback" :style="fallbackStyle">
          <span class="cover-letter">{{ coverChar }}</span>
        </div>
        <div class="cover-overlay">
          <button class="play-btn" @click.prevent="play(track)" :title="'播放 ' + title">
            <span v-if="isCurrentPlaying">&#10074;&#10074;</span>
            <span v-else>&#9654;</span>
          </button>
        </div>
      </div>
    </router-link>
    <div class="card-body">
      <div class="card-title">{{ title }}</div>
      <div class="card-artist">{{ track.artist_name }}</div>
      <div class="card-meta">
        <span v-if="track.genre" class="card-genre">{{ track.genre }}</span>
        <span v-if="track.year" class="card-year">{{ track.year }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { playerState, playTrack } from '../audio.js'
import { coverStyle, coverText } from '../cover.js'

const props = defineProps({ track: { type: Object, required: true } })
const imgFailed = ref(false)

const trackId = computed(() => props.track.id || props.track.track_id)
const title = computed(() => props.track.title || props.track.track_name || '?')
const coverChar = computed(() => coverText(title.value))
const fallbackStyle = computed(() => coverStyle(trackId.value, props.track.genre || props.track.track_genre || ''))
const isCurrentPlaying = computed(() =>
  playerState.currentTrack?.id === trackId.value && playerState.isPlaying
)

function play(track) {
  playTrack({ ...track, id: track.id || track.track_id })
}
</script>

<style scoped>
.track-card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.25s, box-shadow 0.25s;
  border: 1px solid var(--color-border);
  position: relative;
}
.track-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
  border-color: var(--color-primary);
}

.card-cover-link {
  display: block;
  text-decoration: none;
  color: inherit;
}
.card-cover {
  aspect-ratio: 1;
  position: relative;
  overflow: hidden;
  background: var(--color-bg);
}
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s;
}
.track-card:hover .cover-img {
  transform: scale(1.05);
}
.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cover-letter {
  font-size: 56px;
  font-weight: 900;
  color: rgba(255,255,255,0.4);
  line-height: 1;
  font-family: Arial, "Microsoft YaHei", sans-serif;
  text-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.25s;
}
.track-card:hover .cover-overlay {
  background: rgba(0,0,0,0.35);
}
.play-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--color-primary);
  color: white;
  font-size: 18px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.25s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.track-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
}
.play-btn:hover {
  background: var(--color-primary-light);
  transform: translateY(0) scale(1.1);
}

.card-body { padding: 14px; }
.card-title {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-artist {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-meta {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.card-genre {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  background: var(--color-bg);
  color: var(--color-primary-light);
}
.card-year {
  font-size: 10px;
  color: var(--color-text-muted);
  padding: 2px 4px;
}
</style>
