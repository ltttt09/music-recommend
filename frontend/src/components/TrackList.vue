<template>
  <div class="track-list">
    <div
      v-for="item in items"
      :key="item.track_id || item.id"
      class="track-row"
    >
      <router-link :to="'/track/' + (item.track_id || item.id)" class="track-link">
        <span class="track-cover">
          <img
            v-if="item.image_url && !imgFailed[item.track_id || item.id]"
            :src="item.image_url"
            class="track-cover-img"
            alt=""
            loading="lazy"
            referrerpolicy="no-referrer"
            @error="imgFailed[item.track_id || item.id] = true"
          />
          <span v-if="!item.image_url || imgFailed[item.track_id || item.id]" class="track-cover-fallback" :style="fallbackStyle(item)">
            {{ coverChar(item) }}
          </span>
        </span>
        <div class="track-meta">
          <span class="track-name">{{ item.track_name || item.title }}</span>
          <span class="track-artist">{{ item.artist_name }}</span>
        </div>
      </router-link>
      <div class="track-actions">
        <button class="track-play-btn" @click="play(item)" title="试听">
          <span v-if="isPlaying(item)">&#10074;&#10074;</span>
          <span v-else>&#9654;</span>
        </button>
        <span v-if="item.score !== undefined" class="track-score">
          {{ (item.score * 100).toFixed(1) }}%
        </span>
      </div>
    </div>
    <p v-if="items.length === 0" class="empty">暂无歌曲</p>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { playerState, playTrack } from '../audio.js'
import { coverStyle, coverText } from '../cover.js'
const imgFailed = reactive({})

defineProps({
  items: { type: Array, default: () => [] },
})

function coverChar(item) {
  return coverText(item.track_name || item.title || '?')
}

function fallbackStyle(item) {
  return coverStyle(item.track_id || item.id, item.genre || item.track_genre || '')
}

function isPlaying(item) {
  return playerState.currentTrack?.id === (item.track_id || item.id) && playerState.isPlaying
}

function play(item) {
  playTrack({
    id: item.track_id || item.id,
    title: item.track_name || item.title,
    artist_name: item.artist_name,
    image_url: item.image_url,
    preview_url: item.preview_url,
  })
}
</script>

<style scoped>
.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 8px 14px;
  transition: background 0.15s;
}

.track-row:hover {
  background: var(--color-surface-hover);
}

.track-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  flex: 1;
  min-width: 0;
}

.track-cover {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.track-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.track-cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  font-family: Arial, "Microsoft YaHei", sans-serif;
  color: rgba(255,255,255,0.5);
}

.track-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.track-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-artist {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.track-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.track-play-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s;
}
.track-play-btn:hover {
  background: var(--color-primary);
  color: white;
}
.track-score {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent);
}

.empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 40px 0;
}
</style>
