import { reactive } from 'vue'
import { logAction } from './actionLog.js'

// Global audio player state
export const playerState = reactive({
  currentTrack: null,  // { id, title, artist_name, album, image_url, preview_url }
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  audio: null,
})

let audioElement = null

function currentTrackId() {
  return playerState.currentTrack?.id || null
}

function trackMetadata(extra = {}) {
  const track = playerState.currentTrack || {}
  return {
    title: track.title || track.track_name || '',
    artist_name: track.artist_name || '',
    preview_url: track.preview_url || '',
    current_time: playerState.currentTime,
    duration: playerState.duration,
    ...extra,
  }
}

function getAudio() {
  if (!audioElement) {
    audioElement = new Audio()
    audioElement.crossOrigin = "anonymous"
    audioElement.addEventListener('timeupdate', () => {
      playerState.currentTime = audioElement.currentTime
    })
    audioElement.addEventListener('loadedmetadata', () => {
      playerState.duration = audioElement.duration
      logAction('audio_loadedmetadata', {
        entity_type: 'track',
        entity_id: currentTrackId(),
        status: 'success',
        message: '音频元数据加载完成',
        metadata: trackMetadata({ duration: audioElement.duration }),
      })
    })
    audioElement.addEventListener('ended', () => {
      playerState.isPlaying = false
      logAction('audio_ended', {
        entity_type: 'track',
        entity_id: currentTrackId(),
        status: 'success',
        message: '歌曲播放结束',
        metadata: trackMetadata(),
      })
    })
    audioElement.addEventListener('play', () => {
      playerState.isPlaying = true
      logAction('audio_playing', {
        entity_type: 'track',
        entity_id: currentTrackId(),
        status: 'success',
        message: '歌曲开始播放',
        metadata: trackMetadata(),
      })
    })
    audioElement.addEventListener('pause', () => {
      playerState.isPlaying = false
      logAction('audio_paused', {
        entity_type: 'track',
        entity_id: currentTrackId(),
        status: 'success',
        message: '歌曲暂停播放',
        metadata: trackMetadata(),
      })
    })
    audioElement.addEventListener('error', () => {
      const err = audioElement.error
      logAction('audio_error', {
        entity_type: 'track',
        entity_id: currentTrackId(),
        status: 'error',
        message: '音频播放失败',
        metadata: trackMetadata({
          error_code: err?.code || '',
          error_message: err?.message || '',
        }),
      })
    })
  }
  return audioElement
}

export function playTrack(track) {
  const audio = getAudio()
  const normalizedTrack = { ...track, id: track.id || track.track_id }
  logAction('audio_play_request', {
    entity_type: 'track',
    entity_id: normalizedTrack.id,
    status: 'requested',
    message: '用户点击播放按钮',
    metadata: {
      title: normalizedTrack.title || normalizedTrack.track_name || '',
      artist_name: normalizedTrack.artist_name || '',
      has_preview_url: Boolean(normalizedTrack.preview_url),
      audio_type: normalizedTrack.audio_type || '',
    },
  })
  if (playerState.currentTrack?.id === normalizedTrack.id && audio.src) {
    // Same track - toggle play/pause
    if (playerState.isPlaying) {
      audio.pause()
    } else {
      audio.play().catch((err) => {
        logAction('audio_play_error', {
          entity_type: 'track',
          entity_id: normalizedTrack.id,
          status: 'error',
          message: '浏览器拒绝或无法播放音频',
          metadata: { error: err?.message || String(err) },
        })
      })
    }
    return
  }
  // New track
  audio.pause()
  audio.removeAttribute('src')
  audio.load()
  playerState.currentTrack = normalizedTrack
  playerState.currentTime = 0
  playerState.duration = 0
  if (normalizedTrack.preview_url) {
    audio.src = normalizedTrack.preview_url
    audio.load()
    audio.play().catch((err) => {
      logAction('audio_play_error', {
        entity_type: 'track',
        entity_id: normalizedTrack.id,
        status: 'error',
        message: '浏览器拒绝或无法播放音频',
        metadata: { error: err?.message || String(err), preview_url: normalizedTrack.preview_url },
      })
    })
  } else {
    logAction('audio_missing_source', {
      entity_type: 'track',
      entity_id: normalizedTrack.id,
      status: 'blocked',
      message: '歌曲缺少可播放地址',
      metadata: {
        title: normalizedTrack.title || normalizedTrack.track_name || '',
        artist_name: normalizedTrack.artist_name || '',
      },
    })
  }
}

export function pauseTrack() {
  const audio = getAudio()
  logAction('audio_pause_request', {
    entity_type: 'track',
    entity_id: currentTrackId(),
    status: 'requested',
    message: '用户请求暂停播放',
    metadata: trackMetadata(),
  })
  audio.pause()
}

export function seekTo(time) {
  const audio = getAudio()
  logAction('audio_seek', {
    entity_type: 'track',
    entity_id: currentTrackId(),
    status: 'success',
    message: '用户拖动播放进度',
    metadata: trackMetadata({ seek_to: time }),
  })
  audio.currentTime = time
}

export function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return m + ":" + String(s).padStart(2, "0")
}
