<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-head">
        <h2>加入歌单</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div v-if="!uid" class="empty">
        <div class="guest-avatar">♪</div>
        <p>登录后可以把歌曲加入自己的歌单。</p>
        <router-link class="btn btn-primary btn-sm" to="/login">去登录</router-link>
      </div>

      <template v-else>
        <div class="create-row">
          <input v-model="newName" placeholder="新建歌单名称" @keyup.enter="createPlaylist" />
          <button class="btn btn-primary btn-sm" @click="createPlaylist" :disabled="creating">新建</button>
        </div>
        <p v-if="msg" class="msg" :class="msgOk ? 'success' : 'error'">{{ msg }}</p>

        <div v-if="loading" class="spinner"></div>
        <div v-else-if="playlists.length" class="playlist-list">
          <label v-for="playlist in playlists" :key="playlist.id" class="playlist-row">
            <input v-model="selected" type="checkbox" :value="playlist.id" />
            <span>{{ playlist.name }}</span>
            <small>{{ playlist.track_count || 0 }} 首</small>
          </label>
        </div>
        <div v-else class="empty">
          <p>还没有自建歌单，可以先新建一个。</p>
        </div>

        <div class="actions">
          <button class="btn btn-ghost btn-sm" @click="$emit('close')">取消</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="!selected.length || submitting">
            {{ submitting ? '添加中...' : '添加到选中歌单' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api.js'
import { auth } from '../auth.js'

const props = defineProps({
  trackIds: { type: Array, required: true },
})
const emit = defineEmits(['close', 'added'])

const uid = computed(() => auth.userId || Number(localStorage.getItem('user_id')) || 0)
const playlists = ref([])
const selected = ref([])
const loading = ref(false)
const submitting = ref(false)
const creating = ref(false)
const newName = ref('')
const msg = ref('')
const msgOk = ref(false)
let msgTimer = null
function setMsg(text, ok = false) {
  msg.value = text
  msgOk.value = ok
  if (msgTimer) clearTimeout(msgTimer)
  if (text) msgTimer = setTimeout(() => { msg.value = ''; msgOk.value = false; msgTimer = null }, ok ? 2000 : 3000)
}

async function loadPlaylists() {
  if (!uid.value) return
  loading.value = true
  try {
    const data = await api.getUserCreatedPlaylists(uid.value, 1, 50)
    playlists.value = data.items || []
  } catch (e) {
    setMsg(e.message || '歌单加载失败', false)
  } finally {
    loading.value = false
  }
}

async function createPlaylist() {
  const name = newName.value.trim()
  if (!name) {
    setMsg('歌单名称不能为空', false)
    return
  }
  if (name.length > 30) {
    setMsg('歌单名称不能超过 30 个字符', false)
    return
  }
  creating.value = true
  try {
    const created = await api.createUserPlaylist(uid.value, name)
    newName.value = ''
    setMsg('歌单创建成功', true)
    await loadPlaylists()
    if (created?.id) selected.value = Array.from(new Set([...selected.value, created.id]))
  } catch (e) {
    setMsg(e.message || '歌单创建失败', false)
  } finally {
    creating.value = false
  }
}

async function submit() {
  submitting.value = true
  msg.value = ''
  try {
    let success = 0
    for (const playlistId of selected.value) {
      for (const trackId of props.trackIds) {
        try {
          await api.addToPlaylist(playlistId, trackId)
          success += 1
        } catch (e) {
          if (!String(e.message || '').includes('UNIQUE')) throw e
        }
      }
    }
    setMsg(success ? '已加入歌单' : '歌曲已在选中歌单中', true)
    emit('added')
    setTimeout(() => emit('close'), 700)
  } catch (e) {
    setMsg(e.message || '加入歌单失败', false)
  } finally {
    submitting.value = false
  }
}

onMounted(loadPlaylists)
</script>

<style scoped>
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.56);display:flex;align-items:center;justify-content:center;padding:20px;z-index:120}
.modal{width:min(460px,100%);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;box-shadow:0 24px 80px rgba(0,0,0,.45)}
.modal-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}.modal-head h2{font-size:18px}.close-btn{background:none;border:none;color:var(--color-text-muted);font-size:24px;cursor:pointer}
.create-row{display:flex;gap:8px;margin-bottom:10px}.create-row input{flex:1}
.playlist-list{display:flex;flex-direction:column;gap:4px;max-height:280px;overflow:auto}.playlist-row{display:flex;align-items:center;gap:10px;background:var(--color-bg);border-radius:var(--radius);padding:10px 12px;cursor:pointer}.playlist-row span{flex:1}.playlist-row small{color:var(--color-text-muted)}
.actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}.msg{font-size:14px;margin:6px 0}.msg.success{color:var(--color-like)}.msg.error{color:var(--color-dislike);font-weight:bold}
.empty{text-align:center;color:var(--color-text-muted);padding:20px 0}.guest-avatar{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;background:var(--color-bg);font-size:24px;color:var(--color-primary-light)}
</style>
