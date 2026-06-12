<template>
  <div class="container">
    <div class="page-header"><h1>个人信息</h1><p>管理你的账户信息</p></div>

    <div v-if="loading" class="spinner"></div>
    <div v-else-if="user" class="profile-card">
      <div class="avatar-box">
        <img v-if="avatarPreview" :src="avatarPreview" alt="头像" />
        <span v-else>{{ (displayName || user.username || '?').charAt(0) }}</span>
      </div>
      <div class="field">
        <label>头像</label>
        <input type="file" accept="image/*" @change="onAvatarSelected" />
      </div>
      <div class="field">
        <label>用户名</label>
        <span class="field-value">{{ user.username }}</span>
      </div>
      <div class="field">
        <label>显示名称</label>
        <input v-model="displayName" placeholder="输入显示名称" />
      </div>
      <div class="field">
        <label>偏好流派</label>
        <input v-model="preferredGenres" placeholder="例如: 流行, 摇滚, 电子 (逗号分隔)" />
      </div>
      <div class="field">
        <label>注册时间</label>
        <span class="field-value">{{ user.join_date?.slice(0,10) || '-' }}</span>
      </div>
      <div class="field">
        <label>听歌统计</label>
        <span class="field-value" v-if="stats">{{ stats.total_listens || 0 }} 次播放</span>
      </div>

      <div class="actions">
        <button class="btn btn-primary" @click="saveProfile" :disabled="saving">{{ saving ? '保存中...' : '保存修改' }}</button>
      </div>
      <p v-if="msg" class="msg" :class="msgOk ? 'success' : 'error'">{{ msg }}</p>
    </div>
    <div v-else class="empty-hint">用户信息加载失败</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import { auth } from '../auth.js'

const user = ref(null)
const stats = ref(null)
const displayName = ref('')
const preferredGenres = ref('')
const avatarPreview = ref('')
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const msgOk = ref(false)

onMounted(async () => {
  const uid = auth.userId || Number(localStorage.getItem('user_id')) || 1
  try {
    const d = await api.getUser(uid)
    user.value = d.user
    stats.value = d.stats
    displayName.value = d.user?.display_name || ''
    preferredGenres.value = d.user?.preferred_genres || ''
    avatarPreview.value = d.user?.avatar_url || ''
  } catch (e) { console.error(e) } finally { loading.value = false }
})

function onAvatarSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    msg.value = '请选择图片文件'
    msgOk.value = false
    return
  }
  if (file.size > 800 * 1024) {
    msg.value = '头像图片不能超过 800KB'
    msgOk.value = false
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    avatarPreview.value = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}

async function saveProfile() {
  saving.value = true; msg.value = ''
  const uid = auth.userId || Number(localStorage.getItem('user_id')) || 1
  try {
    const d = await api.updateProfile(uid, { display_name: displayName.value, preferred_genres: preferredGenres.value, avatar_url: avatarPreview.value })
    if (d.username) {
      auth.username = d.display_name || d.username
      localStorage.setItem('username', auth.username)
      msg.value = '保存成功'
      msgOk.value = true
    }
  } catch (e) { msg.value = e.message; msgOk.value = false } finally { saving.value = false }
}
</script>

<style scoped>
.profile-card { max-width: 500px; background: var(--color-surface); border-radius: var(--radius); padding: 28px; }
.avatar-box { width: 78px; height: 78px; border-radius: 50%; overflow: hidden; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); color: #fff; font-size: 32px; font-weight: 800; margin-bottom: 18px; }
.avatar-box img { width: 100%; height: 100%; object-fit: cover; display: block; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 12px; font-weight: 700; color: var(--color-text-muted); text-transform: uppercase; margin-bottom: 6px; }
.field input { width: 100%; }
.field-value { font-size: 15px; color: var(--color-text); padding: 8px 0; display: block; }
.actions { margin-top: 20px; }
.msg { margin-top: 12px; font-size: 13px; }
.msg.success { color: var(--color-like); }
.msg.error { color: var(--color-dislike); }
.empty-hint { text-align: center; color: var(--color-text-muted); padding: 60px 0; }
</style>
