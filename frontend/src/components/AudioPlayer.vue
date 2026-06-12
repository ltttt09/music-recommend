<template>
  <div v-if="playerState.currentTrack" class="audio-player" :class="{ expanded: showDetail }">
    <div class="player-bar" @click="showDetail = !showDetail">
      <div class="player-left" @click.stop="goNowPlaying">
        <img
          v-if="playerState.currentTrack.image_url"
          :src="playerState.currentTrack.image_url"
          class="player-cover"
          alt=""
          referrerpolicy="no-referrer"
        />
        <div v-else class="player-cover placeholder">&#9835;</div>
        <div class="player-info">
          <div class="player-title">{{ playerState.currentTrack.title }}</div>
          <div class="player-artist">{{ playerState.currentTrack.artist_name }}</div>
        </div>
      </div>
      <div class="player-center">
        <button class="player-btn" @click.stop="playTrack(playerState.currentTrack)">
          <span v-if="playerState.isPlaying">&#10074;&#10074;</span>
          <span v-else>&#9654;</span>
        </button>
      </div>
      <div class="player-right">
        <span class="player-time">{{ formatTime(playerState.currentTime) }} / {{ formatTime(playerState.duration) }}</span>
        <button class="player-btn player-close" @click.stop="closePlayer">&times;</button>
      </div>
    </div>
    <div v-if="showDetail" class="player-progress">
      <input
        type="range"
        min="0"
        :max="playerState.duration || 0"
        :value="playerState.currentTime"
        class="progress-slider"
        @input="seekTo(parseFloat($event.target.value))"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { playerState, playTrack, pauseTrack, seekTo, formatTime } from '../audio.js'

const showDetail = ref(false)
const router = useRouter()

function goNowPlaying() {
  if (playerState.currentTrack?.id) router.push('/playing/' + playerState.currentTrack.id)
}

function closePlayer() {
  pauseTrack()
  playerState.currentTrack = null
}
</script>

<style scoped>
.audio-player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -4px 24px rgba(0,0,0,0.3);
  user-select: none;
}
.player-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  cursor: pointer;
  max-width: 1200px;
  margin: 0 auto;
}
.player-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}
.player-cover {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}
.player-cover.placeholder {
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: rgba(255,255,255,0.5);
}
.player-info {
  min-width: 0;
}
.player-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-artist {
  font-size: 11px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-center {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
}
.player-btn {
  background: none;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  font-size: 18px;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all .2s;
}
.player-btn:hover {
  background: var(--color-bg);
  color: var(--color-primary-light);
}
.player-close {
  font-size: 20px;
  padding: 2px 8px;
}
.player-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.player-time {
  font-size: 11px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
.player-progress {
  padding: 0 20px 10px;
  max-width: 1200px;
  margin: 0 auto;
}
.progress-slider {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(90deg, var(--color-primary-light), var(--color-border));
  border-radius: 999px;
  outline: none;
  cursor: pointer;
}
.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-primary-light);
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0,0,0,.22);
}
@media (max-width: 600px) {
  .player-bar { padding: 8px 12px; }
  .player-right { display: none; }
  .player-center { padding: 0 8px; }
}
</style>
